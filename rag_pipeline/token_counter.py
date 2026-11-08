"""
token_counter.py — Real-time token usage tracking for advanced-PROBE.

Tracks prompt tokens, completion tokens, and total tokens across all LLM
calls.  The counter is backed by a thread-safe in-process store that is
persisted to disk (at ~/.probe/token_usage/token_usage.json) on every update,
so usage is retained across CLI sessions. Streamlit session state is kept in
sync on every update so the UI reflects usage immediately after each request.

Token counting strategy
-----------------------
1. **Actual usage** (preferred): read ``usage`` from the OpenAI response object
   for non-streaming calls — this is exact.
2. **tiktoken estimation** (streaming / fallback): count tokens in the message
   list with ``tiktoken`` when the response has no usage field.  Falls back to
   a simple whitespace-split heuristic if ``tiktoken`` is not installed.

Token budget
------------
Set ``TOKEN_BUDGET`` in the environment (or ``.env``) to the total tokens
allotted for the session.  Defaults to 100 000.

Persistent storage
------------------
Token usage is automatically saved to ~/.probe/token_usage/token_usage.json
after each LLM call. On module load, usage is restored from disk so you
can resume tracking across multiple CLI invocations.

Public API
----------
    TokenUsage                      — dataclass: prompt / completion / total / by_model
    get_usage()  -> TokenUsage      — current session totals (with on-disk values)
    record_call(prompt_tokens, completion_tokens, model)  — add a call's usage (persisted)
    reset()                         — zero all counters and clear disk storage
    estimate_tokens(messages)       — count tokens in an OpenAI message list
    pct_used(budget)                — float 0–100
"""

from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Sequence

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Token budget — override via TOKEN_BUDGET env var or .env
# ---------------------------------------------------------------------------
DEFAULT_BUDGET: int = int(os.environ.get("TOKEN_BUDGET", "100000"))

# ---------------------------------------------------------------------------
# Cost tracking — INR per 1K tokens
# USD_TO_INR: override via LLM_USD_TO_INR in .env (default 84.0)
# Per-1K-token USD cost: override via LLM_COST_PER_1K_TOKENS_USD (default 0.005)
# Derived INR rate = USD_rate × USD_TO_INR
# ---------------------------------------------------------------------------
_USD_TO_INR: float = float(os.environ.get("LLM_USD_TO_INR", "84.0"))
_COST_PER_1K_USD: float = float(os.environ.get("LLM_COST_PER_1K_TOKENS_USD", "0.005"))
COST_PER_1K_INR: float = _COST_PER_1K_USD * _USD_TO_INR  # ≈ 0.42 INR/1K tokens


def tokens_to_inr(tokens: int) -> float:
    """Convert a token count to estimated cost in INR."""
    return round(tokens / 1000 * COST_PER_1K_INR, 6)

# ---------------------------------------------------------------------------
# Persistent storage for token usage across CLI sessions
# ---------------------------------------------------------------------------
_STORAGE_DIR = Path.home() / ".probe" / "token_usage"
_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
_STORAGE_FILE = _STORAGE_DIR / "token_usage.json"
_HISTORY_FILE = _STORAGE_DIR / "token_history.json"

# ---------------------------------------------------------------------------
# Thread-safe usage store
# ---------------------------------------------------------------------------
_lock = threading.Lock()


@dataclass
class TokenUsage:
    """Snapshot of token consumption for a session."""

    prompt_tokens:     int = 0
    completion_tokens: int = 0
    total_tokens:      int = 0
    call_count:        int = 0
    total_cost_inr:    float = 0.0
    # per-model breakdown  {model_name: total_tokens}
    by_model:          dict[str, int] = field(default_factory=dict)
    # last single-call counts (reset on each record_call)
    last_call_prompt:      int = 0
    last_call_completion:  int = 0
    last_call_total:       int = 0
    last_call_cost_inr:    float = 0.0

    def pct_used(self, budget: int = DEFAULT_BUDGET) -> float:
        """Return percentage of budget consumed (0.0 – 100.0)."""
        if budget <= 0:
            return 0.0
        return min(100.0, round(self.total_tokens / budget * 100, 2))

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict."""
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "call_count": self.call_count,
            "total_cost_inr": self.total_cost_inr,
            "by_model": self.by_model,
        }

    @classmethod
    def from_dict(cls, data: dict) -> TokenUsage:
        """Deserialize from JSON-compatible dict."""
        return cls(
            prompt_tokens=data.get("prompt_tokens", 0),
            completion_tokens=data.get("completion_tokens", 0),
            total_tokens=data.get("total_tokens", 0),
            call_count=data.get("call_count", 0),
            total_cost_inr=data.get("total_cost_inr", 0.0),
            by_model=data.get("by_model", {}),
        )


def _load_from_disk() -> TokenUsage:
    """Load token usage from persistent storage, return empty if not found."""
    try:
        if _STORAGE_FILE.exists():
            with open(_STORAGE_FILE, "r") as f:
                data = json.load(f)
                return TokenUsage.from_dict(data)
    except Exception as e:
        logger.warning(f"Failed to load token usage from disk: {e}")
    return TokenUsage()


def _save_to_disk(usage: TokenUsage) -> None:
    """Persist token usage to disk."""
    try:
        with open(_STORAGE_FILE, "w") as f:
            json.dump(usage.to_dict(), f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to save token usage to disk: {e}")


def _load_history() -> list[dict]:
    """Load call history from disk, return empty list if not found."""
    try:
        if _HISTORY_FILE.exists():
            with open(_HISTORY_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load token history from disk: {e}")
    return []


def _save_history(history: list[dict]) -> None:
    """Persist call history to disk."""
    try:
        with open(_HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to save token history to disk: {e}")


# Load history on module startup
_history = _load_history()


# Module-level mutable instance (one per Python process) — load from disk on startup
_usage = _load_from_disk()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_usage() -> TokenUsage:
    """Return a snapshot copy of current session token usage."""
    with _lock:
        return TokenUsage(
            prompt_tokens=_usage.prompt_tokens,
            completion_tokens=_usage.completion_tokens,
            total_tokens=_usage.total_tokens,
            call_count=_usage.call_count,
            total_cost_inr=_usage.total_cost_inr,
            by_model=dict(_usage.by_model),
            last_call_prompt=_usage.last_call_prompt,
            last_call_completion=_usage.last_call_completion,
            last_call_total=_usage.last_call_total,
            last_call_cost_inr=_usage.last_call_cost_inr,
        )


def record_call(
    prompt_tokens: int,
    completion_tokens: int,
    model: str = "unknown",
) -> TokenUsage:
    """Add one LLM call's token counts to the session totals.

    Thread-safe.  Returns the updated snapshot so callers can read immediately.
    Persists to disk after each call with timestamp in history.

    Args:
        prompt_tokens:      Tokens consumed by the input messages.
        completion_tokens:  Tokens in the model's reply.
        model:              Model identifier string (for per-model breakdown).

    Returns:
        Updated :class:`TokenUsage` snapshot.
    """
    # Treat None (returned by some endpoints) as 0 to avoid TypeError
    pt = int(prompt_tokens or 0)
    ct = int(completion_tokens or 0)
    call_cost_inr = tokens_to_inr(pt + ct)
    timestamp = datetime.utcnow().isoformat()

    with _lock:
        _usage.prompt_tokens     += pt
        _usage.completion_tokens += ct
        _usage.total_tokens      += pt + ct
        _usage.call_count        += 1
        _usage.total_cost_inr    += call_cost_inr
        _usage.by_model[model]    = (
            _usage.by_model.get(model, 0) + pt + ct
        )
        _usage.last_call_prompt     = pt
        _usage.last_call_completion = ct
        _usage.last_call_total      = pt + ct
        _usage.last_call_cost_inr   = call_cost_inr
        logger.debug(
            "Token usage recorded — prompt=%d completion=%d total=%d cost=₹%.4f model=%s (session=%d)",
            pt, ct, pt + ct, call_cost_inr, model, _usage.total_tokens,
        )
        snapshot = TokenUsage(
            prompt_tokens=_usage.prompt_tokens,
            completion_tokens=_usage.completion_tokens,
            total_tokens=_usage.total_tokens,
            call_count=_usage.call_count,
            total_cost_inr=_usage.total_cost_inr,
            by_model=dict(_usage.by_model),
            last_call_prompt=_usage.last_call_prompt,
            last_call_completion=_usage.last_call_completion,
            last_call_total=_usage.last_call_total,
            last_call_cost_inr=_usage.last_call_cost_inr,
        )

    # Add to history with timestamp
    _history.append({
        "timestamp": timestamp,
        "prompt_tokens": pt,
        "completion_tokens": ct,
        "total_tokens": pt + ct,
        "cost_inr": call_cost_inr,
        "model": model,
    })

    # Persist outside lock to avoid blocking token recording
    _save_to_disk(_usage)
    _save_history(_history)
    return snapshot


def get_history(hours: int | None = None) -> list[dict]:
    """Get call history, optionally filtered to last N hours.

    Args:
        hours: If provided, return only calls from the last N hours.

    Returns:
        List of call records with timestamp, tokens, and model.
    """
    if hours is None:
        return _history.copy()

    cutoff = datetime.utcnow().timestamp() - (hours * 3600)
    return [
        call for call in _history
        if datetime.fromisoformat(call["timestamp"]).timestamp() >= cutoff
    ]


def reset() -> None:
    """Zero all counters and clear persistent storage (call at the start of a new session)."""
    global _history
    with _lock:
        _usage.prompt_tokens     = 0
        _usage.completion_tokens = 0
        _usage.total_tokens      = 0
        _usage.call_count        = 0
        _usage.total_cost_inr    = 0.0
        _usage.by_model.clear()
        _usage.last_call_prompt     = 0
        _usage.last_call_completion = 0
        _usage.last_call_total      = 0
        _usage.last_call_cost_inr   = 0.0
        _history = []
    _save_to_disk(_usage)
    _save_history(_history)
    logger.info("Token counter reset (persistent storage cleared).")


# ---------------------------------------------------------------------------
# Token estimation helpers
# ---------------------------------------------------------------------------

def _tiktoken_count(text: str, model: str) -> int:
    """Encode *text* with tiktoken and return the token count."""
    try:
        import tiktoken  # type: ignore[import]
        try:
            enc = tiktoken.encoding_for_model(model)
        except KeyError:
            enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        # Heuristic fallback: ~0.75 tokens per word (GPT-style estimate)
        return max(1, int(len(text.split()) / 0.75))


def estimate_tokens(
    messages: Sequence[dict],
    model: str = "gpt-4",
) -> int:
    """Estimate prompt token count for an OpenAI message list.

    Uses tiktoken when available, falls back to a whitespace heuristic.
    Adds the standard per-message overhead (4 tokens/message, 2 for reply primer).

    Args:
        messages: OpenAI-format message list.
        model:    Model name used for tiktoken encoding selection.

    Returns:
        Estimated integer token count.
    """
    total = 0
    per_message_overhead = 4   # role + content delimiters
    for msg in messages:
        total += per_message_overhead
        content = msg.get("content") or ""
        total += _tiktoken_count(content, model)
    total += 2   # reply primer
    return total
