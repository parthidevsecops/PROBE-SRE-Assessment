"""
llm_client.py — LLM wrapper supporting two backends:

  **Remote** (default)  — OpenAI-compatible HTTP API endpoint
    Configured via HF_TOKEN, HF_MODEL, HF_BASE_URL in .env.
    Includes automatic retry + timeout for transient 5xx / Cloudflare 524 errors.

  **Local HF** (opt-in) — HuggingFace transformers pipeline on local hardware
    Activated by: HF_USE_LOCAL=true in .env.
    Model:   HF_LOCAL_MODEL  (default: FINAL-Bench/Darwin-36B-Opus)
    Options: HF_LOAD_IN_4BIT, HF_DEVICE_MAP, HF_MAX_NEW_TOKENS
    Requires: transformers, torch, accelerate (+ bitsandbytes for 4-bit quant)

Public API (unchanged regardless of backend):
    chat(messages)        -> str
    chat_stream(messages) -> Iterator[str]
"""

from __future__ import annotations

import logging
import os
import time
from typing import Iterator

from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    OpenAI,
)
import instructor
from pydantic import BaseModel

from .token_counter import record_call, estimate_tokens, get_usage
from .token_cache import get as cache_get, put as cache_put

# API latency thresholds (milliseconds)
_LATENCY_WARNING_THRESHOLD: float = float(os.environ.get("LLM_LATENCY_WARNING_THRESHOLD", "30000"))
_LATENCY_CRITICAL_THRESHOLD: float = float(os.environ.get("LLM_LATENCY_CRITICAL_THRESHOLD", "180000"))

# override=True ensures the .env file always wins over stale shell exports
# (e.g. an old hf_ token that was exported in a previous session).
load_dotenv(override=True)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration — resolved lazily inside _get_client() so that a
# load_dotenv(override=True) call anywhere before the first LLM request
# is always picked up, even if this module was imported earlier.
# ---------------------------------------------------------------------------
# Temperature — keep low for RAG use cases so answers stay grounded in context.
# Override via LLM_TEMPERATURE in .env (float, 0.0–1.0).
_TEMPERATURE: float = float(os.environ.get("LLM_TEMPERATURE", "1.0"))
# Per-request timeout in seconds.  Kept under Cloudflare's 120s proxy limit
# so Python raises a clean error rather than waiting for Cloudflare's 524.
_TIMEOUT: float = float(os.environ.get("LLM_TIMEOUT", "90"))
# Maximum number of automatic retries *per provider* on transient 5xx / timeout errors.
# After exhausting retries on one provider, the next provider in the chain is tried.
_MAX_RETRIES: int = int(os.environ.get("LLM_MAX_RETRIES", "2"))
# Initial backoff (seconds) before the first retry; doubles each attempt.
_BACKOFF_BASE: float = 5.0

# ---------------------------------------------------------------------------
# Local HuggingFace transformers backend configuration
# Activated only when HF_USE_LOCAL=true; all other settings are ignored otherwise.
# ---------------------------------------------------------------------------
_HF_USE_LOCAL: bool = os.environ.get("HF_USE_LOCAL", "false").lower() == "true"
_HF_LOCAL_MODEL: str = os.environ.get("HF_LOCAL_MODEL", "FINAL-Bench/Darwin-36B-Opus")
_HF_LOAD_IN_4BIT: bool = os.environ.get("HF_LOAD_IN_4BIT", "true").lower() == "true"
_HF_DEVICE_MAP: str = os.environ.get("HF_DEVICE_MAP", "auto")
_HF_MAX_NEW_TOKENS: int = int(os.environ.get("HF_MAX_NEW_TOKENS", "2048"))


# ---------------------------------------------------------------------------
# Provider chain — multi-LLM automatic failover
# ---------------------------------------------------------------------------
# Configure providers in .env using numbered variables:
#   LLM_PROVIDER_1_TOKEN / _MODEL / _URL  (primary)
#   LLM_PROVIDER_2_TOKEN / _MODEL / _URL  (first fallback)
#   LLM_PROVIDER_3_TOKEN / _MODEL / _URL  (second fallback) … up to 9
# If LLM_PROVIDER_1_* is absent, the legacy HF_TOKEN / HF_MODEL / HF_BASE_URL
# vars are used as provider 1 automatically (backward compatible).
# ---------------------------------------------------------------------------

class _LLMProvider:
    """One entry in the ordered LLM fallback chain."""

    def __init__(self, name: str, token: str, base_url: str, model: str) -> None:
        self.name     = name
        self.token    = token
        self.base_url = base_url
        self.model    = model
        self._client: OpenAI | None = None

    def client(self) -> OpenAI:
        """Return (or lazily create) the OpenAI client for this provider."""
        if self._client is None:
            self._client = OpenAI(
                api_key=self.token,
                base_url=self.base_url or None,
            )
        return self._client

    def __repr__(self) -> str:
        return f"<LLMProvider name={self.name!r} model={self.model!r}>"


def _build_provider_chain() -> list[_LLMProvider]:
    """Build the ordered provider list from environment variables.

    Reads ``LLM_PROVIDER_N_TOKEN`` / ``_MODEL`` / ``_URL`` for N = 1 … 9.
    When N = 1 entries are absent, falls back to the legacy ``HF_TOKEN`` /
    ``HF_MODEL`` / ``HF_BASE_URL`` variables (backward compatibility).
    Stops scanning at the first N where ``TOKEN`` is not set.
    """
    providers: list[_LLMProvider] = []
    for n in range(1, 10):
        prefix = f"LLM_PROVIDER_{n}_"
        token = os.environ.get(f"{prefix}TOKEN")
        model = os.environ.get(f"{prefix}MODEL")
        url   = os.environ.get(f"{prefix}URL")

        if n == 1 and not token:
            # Legacy backward-compat: provider 1 falls back to HF_* vars
            token = os.environ.get("HF_TOKEN") or os.environ.get("OPENAI_API_KEY")
            model = model or os.environ.get("HF_MODEL") or os.environ.get("OPENAI_MODEL", "openai/gpt-4o-mini")
            url   = url or os.environ.get("HF_BASE_URL") or os.environ.get("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")

        if not token:
            break  # gap in numbering — stop scanning

        host = (
            (url or "local")
            .replace("https://", "")
            .replace("http://", "")
            .split("/")[0]
        )
        providers.append(_LLMProvider(
            name=f"P{n}\u00b7{host}",
            token=token,
            base_url=url or "",
            model=model or "",
        ))

    if not providers:
        raise EnvironmentError(
            "No LLM providers configured. "
            "Set HF_TOKEN in .env or add LLM_PROVIDER_1_TOKEN / _MODEL / _URL."
        )

    if len(providers) > 1:
        chain_str = " \u2192 ".join(p.name for p in providers)
        logger.info("LLM fallback chain (%d providers): %s", len(providers), chain_str)
    else:
        logger.info("LLM provider: %s", providers[0].name)

    return providers


# Lazy singleton — built on first use so .env changes before first call are picked up.
_PROVIDERS: list[_LLMProvider] = []
# Backward-compatible module-level model name (used as default arg sentinel).
MODEL: str = os.environ.get("LLM_PROVIDER_1_MODEL") or os.environ.get("HF_MODEL", "")


def _get_providers() -> list[_LLMProvider]:
    global _PROVIDERS
    if not _PROVIDERS:
        _PROVIDERS = _build_provider_chain()
    return _PROVIDERS


# ---------------------------------------------------------------------------
# Public model-switching API
# ---------------------------------------------------------------------------

def get_active_model() -> str:
    """Return the model name currently used by the primary provider."""
    providers = _get_providers()
    return providers[0].model if providers else MODEL


def set_active_model(model: str) -> None:
    """Switch the primary provider to *model* for all subsequent calls.

    Updates provider 1's model name in-place so the already-built OpenAI
    client is reused — only the model field in the request payload changes.
    Also persists the choice to ``os.environ`` so that any re-import or
    ``reload()`` of this module picks up the new value.
    """
    providers = _get_providers()
    if providers:
        providers[0].model = model
    os.environ["HF_MODEL"] = model


def get_last_call_usage() -> dict:
    """Return token counts + cost for the most recent LLM call.

    Reads from the token_counter module which is updated inside chat() / chat_stream().
    Safe to call immediately after chat() returns.

    Returns:
        dict with keys: prompt_tokens, completion_tokens, total_tokens,
        cost_inr, model (last model used from provider chain).
    """
    snap = get_usage()
    return {
        "prompt_tokens": snap.last_call_prompt,
        "completion_tokens": snap.last_call_completion,
        "total_tokens": snap.last_call_total,
        "cost_inr": snap.last_call_cost_inr,
    }


def get_available_models() -> list[str]:
    """Return selectable model IDs from the ``LLM_MODELS`` env var.

    Reads a comma-separated list; always ensures the currently active
    model appears first so the selector stays consistent even when the
    user enters a custom ID not in the configured list.
    """
    raw = os.environ.get("LLM_MODELS", "")
    models: list[str] = [m.strip() for m in raw.split(",") if m.strip()]
    active = get_active_model()
    if active and active not in models:
        models.insert(0, active)
    return models


# ---------------------------------------------------------------------------
# Retry / fallback helpers
# ---------------------------------------------------------------------------

def _is_retryable(exc: Exception) -> bool:
    """Return True for transient errors worth retrying or switching provider for."""
    if isinstance(exc, (APITimeoutError, APIConnectionError)):
        return True
    if isinstance(exc, APIStatusError):
        # 429 rate-limit, 500/502/503 server errors, 524 Cloudflare timeout
        return exc.status_code in (429, 500, 502, 503, 524, 529)
    # Latency threshold exceeded — switch provider
    if isinstance(exc, RuntimeError) and "API latency" in str(exc):
        return True
    return False


def _call_with_fallback(messages: list[dict], **api_kwargs):
    """Try each provider in order with per-provider exponential-backoff retry.

    For each provider, attempts up to ``_MAX_RETRIES + 1`` times before moving
    to the next one.  Returns ``(response, provider, latency_ms)`` from the first success.
    Raises the last exception if every provider exhausts its retries.

    Includes prompt caching: system prompts are cached for 5 minutes to reduce
    token consumption across turns in a session.
    """
    providers = _get_providers()
    last_exc: Exception | None = None

    for provider in providers:
        delay = _BACKOFF_BASE
        for attempt in range(1, _MAX_RETRIES + 2):
            try:
                start_time = time.time()

                # Attempt prompt caching if supported (OpenAI-compatible providers)
                # Not all providers support cache_control; fail gracefully if unsupported
                cache_kwargs = dict(api_kwargs)
                if messages and messages[0].get("role") == "system":
                    cache_kwargs["cache_control"] = {"type": "ephemeral"}

                try:
                    response = provider.client().chat.completions.create(
                        model=provider.model,
                        messages=messages,
                        temperature=_TEMPERATURE,
                        timeout=_TIMEOUT,
                        **cache_kwargs,
                    )
                except TypeError as te:
                    # Provider doesn't support cache_control — retry without it
                    if "cache_control" in str(te):
                        logger.debug(
                            "[%s] Provider does not support prompt caching; retrying without cache_control",
                            provider.name,
                        )
                        cache_kwargs.pop("cache_control", None)
                        response = provider.client().chat.completions.create(
                            model=provider.model,
                            messages=messages,
                            temperature=_TEMPERATURE,
                            timeout=_TIMEOUT,
                            **cache_kwargs,
                        )
                    else:
                        raise
                latency_ms = (time.time() - start_time) * 1000

                # Log cache hit/miss info if available
                usage = getattr(response, "usage", None)
                cache_read_tokens = getattr(usage, "cache_read_input_tokens", 0) if usage else 0
                cache_creation_tokens = getattr(usage, "cache_creation_input_tokens", 0) if usage else 0
                if cache_read_tokens > 0 or cache_creation_tokens > 0:
                    logger.info(
                        "[%s] Prompt cache: read=%d tokens, created=%d tokens",
                        provider.name, cache_read_tokens, cache_creation_tokens,
                    )

                if latency_ms > _LATENCY_CRITICAL_THRESHOLD:
                    logger.error(
                        "[%s] CRITICAL: API latency %.0f ms exceeds threshold %.0f ms. "
                        "Consider switching LLM providers.",
                        provider.name, latency_ms, _LATENCY_CRITICAL_THRESHOLD,
                    )
                    raise RuntimeError(
                        f"API latency {latency_ms:.0f}ms exceeds critical threshold "
                        f"{_LATENCY_CRITICAL_THRESHOLD:.0f}ms. Switch LLM provider."
                    )
                elif latency_ms > _LATENCY_WARNING_THRESHOLD:
                    logger.warning(
                        "[%s] WARNING: API latency %.0f ms exceeds warning threshold %.0f ms",
                        provider.name, latency_ms, _LATENCY_WARNING_THRESHOLD,
                    )

                if provider is not providers[0] or attempt > 1:
                    logger.info(
                        "LLM call succeeded via %s (attempt %d, latency: %.0f ms)",
                        provider.name, attempt, latency_ms,
                    )
                return response, provider, latency_ms
            except Exception as exc:
                if not _is_retryable(exc):
                    raise
                last_exc = exc
                if attempt <= _MAX_RETRIES:
                    logger.warning(
                        "[%s] attempt %d/%d failed: %s — retrying in %.0fs …",
                        provider.name, attempt, _MAX_RETRIES + 1,
                        type(exc).__name__, delay,
                    )
                    time.sleep(delay)
                    delay *= 2
                else:
                    logger.warning(
                        "[%s] all %d attempt(s) exhausted (%s) — switching to next provider …",
                        provider.name, _MAX_RETRIES + 1, type(exc).__name__,
                    )
                    break  # inner loop done — try next provider

    raise last_exc  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Local HuggingFace transformers backend
# ---------------------------------------------------------------------------

_local_pipe = None  # lazy-loaded once on first use


def _get_local_pipeline():
    """Lazy-load and cache the local HF transformers text-generation pipeline.

    Uses 4-bit quantisation by default (``HF_LOAD_IN_4BIT=true``) to reduce
    VRAM requirements for large models like Darwin-36B-Opus (~18 GB vs ~72 GB).
    Requires: ``transformers``, ``torch``, ``accelerate``
    Optional:  ``bitsandbytes`` (for 4-bit quantisation)
    """
    global _local_pipe
    if _local_pipe is not None:
        return _local_pipe

    logger.info(
        "Loading local HF model '%s' (device_map=%s, 4bit=%s) — this may take a few minutes …",
        _HF_LOCAL_MODEL, _HF_DEVICE_MAP, _HF_LOAD_IN_4BIT,
    )
    try:
        from transformers import pipeline as hf_pipeline  # type: ignore[import]
    except ImportError as e:
        raise ImportError(
            "'transformers' is required for local inference. "
            "Install it with: pip install transformers torch accelerate"
        ) from e

    pipe_kwargs: dict = {
        "task": "text-generation",
        "model": _HF_LOCAL_MODEL,
        "device_map": _HF_DEVICE_MAP,
    }

    if _HF_LOAD_IN_4BIT:
        try:
            import torch  # type: ignore[import]
            from transformers import BitsAndBytesConfig  # type: ignore[import]
            pipe_kwargs["model_kwargs"] = {
                "quantization_config": BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                )
            }
        except ImportError:
            logger.warning(
                "bitsandbytes not installed — loading '%s' in full precision "
                "(install with: pip install bitsandbytes).",
                _HF_LOCAL_MODEL,
            )

    _local_pipe = hf_pipeline(**pipe_kwargs)
    logger.info("Local model loaded: %s", _HF_LOCAL_MODEL)
    return _local_pipe


def _local_chat(messages: list[dict]) -> str:
    """Run a message list through the local transformers pipeline (blocking)."""
    pipe = _get_local_pipeline()
    gen_kwargs: dict = {"max_new_tokens": _HF_MAX_NEW_TOKENS, "do_sample": _TEMPERATURE > 0}
    if _TEMPERATURE > 0:
        gen_kwargs["temperature"] = _TEMPERATURE
    result = pipe(messages, **gen_kwargs)
    # pipeline with chat template returns list-of-dicts; last entry = assistant reply
    generated = result[0]["generated_text"]
    if isinstance(generated, list):
        return generated[-1].get("content", "")
    return str(generated)


def _local_chat_stream(messages: list[dict]) -> Iterator[str]:
    """Stream tokens from the local model via TextIteratorStreamer.

    Falls back to a single-chunk yield when streaming dependencies are absent.
    """
    try:
        import threading
        import torch  # type: ignore[import]
        from transformers import TextIteratorStreamer  # type: ignore[import]
    except ImportError as ie:
        logger.warning("Streaming deps missing (%s) — falling back to blocking call.", ie)
        yield _local_chat(messages)
        return

    pipe = _get_local_pipeline()
    model_obj = pipe.model
    tokenizer = pipe.tokenizer

    inputs = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        tokenize=True,
        return_dict=True,
        return_tensors="pt",
    ).to(model_obj.device)

    streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
    gen_kwargs: dict = {
        **inputs,
        "streamer": streamer,
        "max_new_tokens": _HF_MAX_NEW_TOKENS,
        "do_sample": _TEMPERATURE > 0,
    }
    if _TEMPERATURE > 0:
        gen_kwargs["temperature"] = _TEMPERATURE

    thread = threading.Thread(target=model_obj.generate, kwargs=gen_kwargs, daemon=True)
    thread.start()
    for token_text in streamer:
        yield token_text
    thread.join()


def _extract_thinking(text: str) -> tuple[str, str]:
    """Extract ``<think>…</think>`` block from an LLM reply.

    Many reasoning models (GLM, Qwen, DeepSeek-R1) emit a chain-of-thought
    inside ``<think>…</think>`` tags before the actual answer.  This helper
    separates the two so the UI can display them independently.

    Args:
        text: Raw LLM output, potentially containing ``<think>`` tags.

    Returns:
        ``(thinking, clean_text)`` where *thinking* is the inner content of
        the first ``<think>`` block (empty string if absent) and *clean_text*
        is the remaining text with the ``<think>`` block stripped.
    """
    import re as _re
    m = _re.search(r"<think>(.*?)</think>", text, _re.DOTALL | _re.IGNORECASE)
    if not m:
        return "", text.strip()
    thinking = m.group(1).strip()
    clean = (text[: m.start()] + text[m.end() :]).strip()
    return thinking, clean





def chat_structured(
    messages: list[dict],
    response_model: type[BaseModel],
    model: str = MODEL,
) -> BaseModel:
    """Send messages and enforce structured Pydantic response.

    Uses Instructor to patch the OpenAI client for automatic response
    validation against the provided Pydantic model.
    Raises ValidationError if LLM output doesn't match schema.
    """
    if _HF_USE_LOCAL:
        logger.warning("Structured output not supported with local HF backend; using unstructured chat")
        reply = _local_chat(messages)
        record_call(
            prompt_tokens=estimate_tokens(messages, _HF_LOCAL_MODEL),
            completion_tokens=estimate_tokens(
                [{"role": "assistant", "content": reply}], _HF_LOCAL_MODEL
            ),
            model=_HF_LOCAL_MODEL,
        )
        logger.info("llm_call=1 mode=structured-degraded-local model=%s", _HF_LOCAL_MODEL)
        # Return a minimal BaseModel instance for compatibility
        return response_model(**{"data": reply})

    # Patch the provider's OpenAI client with Instructor
    providers = _get_providers()
    client = instructor.from_openai(providers[0].client())

    try:
        # Enable prompt caching for structured output (if supported)
        cache_kwargs = {}
        if messages and messages[0].get("role") == "system":
            cache_kwargs["cache_control"] = {"type": "ephemeral"}

        try:
            response = client.chat.completions.create(
                model=providers[0].model,
                messages=messages,
                response_model=response_model,
                temperature=_TEMPERATURE,
                timeout=_TIMEOUT,
                **cache_kwargs,
            )
        except Exception as te:
            # Provider doesn't support cache_control — retry without it.
            # NOTE: this must catch Exception, not TypeError. instructor's
            # own retry wrapper (instructor.v2.retry) intercepts the raw
            # TypeError from client.chat.completions.create() internally,
            # exhausts its own retry budget, then re-raises its OWN
            # exception type (not a TypeError) once retries are exhausted.
            # A plain `except TypeError` never sees the original error here
            # — it silently misses the retry and the call fails outright,
            # even though the exact same cache_control fallback in chat()
            # (which does NOT go through instructor.from_openai) works fine.
            # We still gate on the message content so unrelated failures
            # are re-raised unchanged rather than masked.
            if "cache_control" in str(te):
                logger.debug("Provider does not support prompt caching in structured mode; retrying")
                cache_kwargs.pop("cache_control", None)
                response = client.chat.completions.create(
                    model=providers[0].model,
                    messages=messages,
                    response_model=response_model,
                    temperature=_TEMPERATURE,
                    timeout=_TIMEOUT,
                    **cache_kwargs,
                )
            else:
                raise
        # Record usage
        record_call(
            prompt_tokens=estimate_tokens(messages, providers[0].model),
            completion_tokens=estimate_tokens(
                [{"role": "assistant", "content": str(response)}], providers[0].model
            ),
            model=providers[0].model,
        )
        logger.info("llm_call=1 mode=structured model=%s response_model=%s", providers[0].model, response_model.__name__)
        return response
    except Exception as e:
        logger.error("llm_call=failed mode=structured error=%s", e)
        raise


def chat(messages: list[dict], model: str = MODEL) -> str:
    """Send *messages* to the LLM and return the full response text.

    Routes to the local HuggingFace transformers backend when
    ``HF_USE_LOCAL=true`` is set; otherwise walks the provider fallback
    chain until a response is received.

    Raises RuntimeError if API latency exceeds critical threshold.
    """
    if _HF_USE_LOCAL:
        cached = cache_get(messages, _HF_LOCAL_MODEL)
        if cached is not None:
            logger.info("llm_call=cache_hit model=%s", _HF_LOCAL_MODEL)
            return cached
        reply = _local_chat(messages)
        pt = estimate_tokens(messages, _HF_LOCAL_MODEL)
        ct = estimate_tokens([{"role": "assistant", "content": reply}], _HF_LOCAL_MODEL)
        record_call(prompt_tokens=pt, completion_tokens=ct, model=_HF_LOCAL_MODEL)
        cache_put(messages, _HF_LOCAL_MODEL, reply, pt, ct)
        logger.info("llm_call=1 backend=local model=%s prompt_tokens=%d completion_tokens=%d", _HF_LOCAL_MODEL, pt, ct)
        return reply

    active_model = _get_providers()[0].model
    cached = cache_get(messages, active_model)
    if cached is not None:
        logger.info("llm_call=cache_hit model=%s", active_model)
        return cached

    response, provider, latency_ms = _call_with_fallback(messages)
    # Record exact usage from the response object (always present for non-streaming)
    reply = response.choices[0].message.content or ""
    usage = getattr(response, "usage", None)
    if usage:
        pt, ct = usage.prompt_tokens, usage.completion_tokens
        record_call(prompt_tokens=pt, completion_tokens=ct, model=provider.model)
    else:
        pt = estimate_tokens(messages, provider.model)
        ct = estimate_tokens([{"role": "assistant", "content": reply}], provider.model)
        record_call(prompt_tokens=pt, completion_tokens=ct, model=provider.model)
    cache_put(messages, provider.model, reply, pt, ct)
    return reply


def chat_stream(messages: list[dict], model: str = MODEL) -> Iterator[str]:
    """Stream tokens from the LLM.

    Yields individual text chunks as they arrive, suitable for use with
    ``st.write_stream()`` in Streamlit.

    Connection-phase errors trigger the provider fallback chain; once a
    stream is established, tokens are yielded from that provider.

    When ``HF_USE_LOCAL=true`` streams via ``TextIteratorStreamer`` from the
    local model; otherwise streams from the remote provider chain.

    Raises RuntimeError if API latency exceeds critical threshold during connection.

    Args:
        messages: OpenAI-format message list.
        model:    Ignored — each provider uses its own configured model.

    Yields:
        String fragments of the assistant reply.
    """
    if _HF_USE_LOCAL:
        full_chunks: list[str] = []
        for token in _local_chat_stream(messages):
            full_chunks.append(token)
            yield token
        # Token accounting after streaming completes
        record_call(
            prompt_tokens=estimate_tokens(messages, _HF_LOCAL_MODEL),
            completion_tokens=estimate_tokens(
                [{"role": "assistant", "content": "".join(full_chunks)}], _HF_LOCAL_MODEL
            ),
            model=_HF_LOCAL_MODEL,
        )
        return

    stream, provider, latency_ms = _call_with_fallback(
        messages,
        stream=True,
        stream_options={"include_usage": True},
    )
    # Estimate prompt tokens upfront (streaming usage arrives only at the final chunk)
    estimated_prompt = estimate_tokens(messages, provider.model)
    completion_text: list[str] = []
    usage_recorded = False
    for chunk in stream:
        delta = chunk.choices[0].delta if chunk.choices else None
        if delta and delta.content:
            completion_text.append(delta.content)
            yield delta.content
        # OpenAI streaming: usage is sent in the final chunk when stream_options used
        usage = getattr(chunk, "usage", None)
        if usage and not usage_recorded:
            record_call(
                prompt_tokens=usage.prompt_tokens or 0,
                completion_tokens=usage.completion_tokens or 0,
                model=provider.model,
            )
            usage_recorded = True
    # Fallback if the endpoint did not return usage in the stream
    if not usage_recorded:
        record_call(
            prompt_tokens=estimated_prompt,
            completion_tokens=estimate_tokens(
                [{"role": "assistant", "content": "".join(completion_text)}], provider.model
            ),
            model=provider.model,
        )