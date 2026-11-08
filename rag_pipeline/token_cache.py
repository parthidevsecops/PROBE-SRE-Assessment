"""
token_cache.py — Exact-match LLM response cache for advanced-PROBE.

Caches LLM responses keyed by a SHA-256 hash of the full message list.
On cache hit, returns stored response immediately — no LLM call made.
Saves prompt + completion tokens on every hit.

Storage: ~/.probe/token_cache/cache.json
Format:  {cache_key: {response, model, prompt_tokens, completion_tokens,
                      hit_count, created_at, last_hit_at}}

TTL defaults to 3600 seconds (1 hour). Set CACHE_TTL_SECONDS in .env to override.
Set CACHE_ENABLED=false to disable entirely.

Public API
----------
    get(messages, model)         -> str | None     — None = cache miss
    put(messages, model, response, prompt_tokens, completion_tokens)
    get_metrics()                -> CacheMetrics
    reset()                      — clear all entries + metrics
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_TTL: int = int(os.environ.get("CACHE_TTL_SECONDS", "3600"))
_ENABLED: bool = os.environ.get("CACHE_ENABLED", "true").lower() != "false"

_STORAGE_DIR = Path.home() / ".probe" / "token_cache"
_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
_CACHE_FILE   = _STORAGE_DIR / "cache.json"
_METRICS_FILE = _STORAGE_DIR / "cache_metrics.json"

_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

@dataclass
class CacheMetrics:
    hits:          int = 0
    misses:        int = 0
    tokens_saved:  int = 0   # prompt + completion tokens not sent to LLM
    evictions:     int = 0   # TTL-expired entries removed

    @property
    def total(self) -> int:
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        return round(self.hits / self.total * 100, 1) if self.total else 0.0

    def to_dict(self) -> dict:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "tokens_saved": self.tokens_saved,
            "evictions": self.evictions,
        }

    @classmethod
    def from_dict(cls, d: dict) -> CacheMetrics:
        return cls(
            hits=d.get("hits", 0),
            misses=d.get("misses", 0),
            tokens_saved=d.get("tokens_saved", 0),
            evictions=d.get("evictions", 0),
        )


def _load_metrics() -> CacheMetrics:
    try:
        if _METRICS_FILE.exists():
            return CacheMetrics.from_dict(json.loads(_METRICS_FILE.read_text()))
    except Exception as e:
        logger.warning("Failed to load cache metrics: %s", e)
    return CacheMetrics()


def _save_metrics(m: CacheMetrics) -> None:
    try:
        _METRICS_FILE.write_text(json.dumps(m.to_dict(), indent=2))
    except Exception as e:
        logger.warning("Failed to save cache metrics: %s", e)


def _load_cache() -> dict:
    try:
        if _CACHE_FILE.exists():
            return json.loads(_CACHE_FILE.read_text())
    except Exception as e:
        logger.warning("Failed to load cache: %s", e)
    return {}


def _save_cache(cache: dict) -> None:
    try:
        _CACHE_FILE.write_text(json.dumps(cache, indent=2))
    except Exception as e:
        logger.warning("Failed to save cache: %s", e)


# Module-level state — loaded once at import
_cache: dict   = _load_cache()
_metrics: CacheMetrics = _load_metrics()


# ---------------------------------------------------------------------------
# Cache key
# ---------------------------------------------------------------------------

def _make_key(messages: list[dict], model: str) -> str:
    payload = json.dumps({"model": model, "messages": messages}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


# ---------------------------------------------------------------------------
# TTL eviction
# ---------------------------------------------------------------------------

def _evict_expired(cache: dict) -> int:
    now = datetime.now(timezone.utc).replace(tzinfo=None).timestamp()
    expired = [
        k for k, v in cache.items()
        if now - datetime.fromisoformat(v["created_at"]).timestamp() > _TTL
    ]
    for k in expired:
        del cache[k]
    return len(expired)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get(messages: list[dict], model: str) -> str | None:
    """Return cached response string, or None on miss/disabled."""
    if not _ENABLED:
        return None

    key = _make_key(messages, model)
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    with _lock:
        entry = _cache.get(key)
        if entry is None:
            _metrics.misses += 1
            _save_metrics(_metrics)
            logger.debug("Cache MISS key=%s...", key[:8])
            return None

        age = (now - datetime.fromisoformat(entry["created_at"])).total_seconds()
        if age > _TTL:
            del _cache[key]
            _metrics.misses += 1
            _metrics.evictions += 1
            _save_cache(_cache)
            _save_metrics(_metrics)
            logger.debug("Cache EXPIRED key=%s...", key[:8])
            return None

        entry["hit_count"] += 1
        entry["last_hit_at"] = now.isoformat()
        saved = entry.get("prompt_tokens", 0) + entry.get("completion_tokens", 0)
        _metrics.hits += 1
        _metrics.tokens_saved += saved
        _save_cache(_cache)
        _save_metrics(_metrics)
        logger.info(
            "Cache HIT key=%s... hits=%d tokens_saved=%d",
            key[:8], entry["hit_count"], saved,
        )
        return entry["response"]


def put(
    messages: list[dict],
    model: str,
    response: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
) -> None:
    """Store a response in the cache."""
    if not _ENABLED:
        return

    key = _make_key(messages, model)
    now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()

    with _lock:
        evicted = _evict_expired(_cache)
        if evicted:
            _metrics.evictions += evicted

        _cache[key] = {
            "response":          response,
            "model":             model,
            "prompt_tokens":     prompt_tokens,
            "completion_tokens": completion_tokens,
            "hit_count":         0,
            "created_at":        now,
            "last_hit_at":       now,
        }
        _save_cache(_cache)
        _save_metrics(_metrics)
        logger.debug("Cache PUT key=%s... model=%s", key[:8], model)


def get_metrics() -> CacheMetrics:
    """Return a snapshot copy of current cache metrics."""
    with _lock:
        return CacheMetrics(
            hits=_metrics.hits,
            misses=_metrics.misses,
            tokens_saved=_metrics.tokens_saved,
            evictions=_metrics.evictions,
        )


def get_cache_size() -> int:
    """Return number of live (non-expired) entries."""
    with _lock:
        now = datetime.now(timezone.utc).replace(tzinfo=None).timestamp()
        return sum(
            1 for v in _cache.values()
            if (now - datetime.fromisoformat(v["created_at"]).timestamp()) <= _TTL
        )


def reset() -> None:
    """Clear all cache entries and metrics."""
    global _cache, _metrics
    with _lock:
        _cache = {}
        _metrics = CacheMetrics()
        _save_cache(_cache)
        _save_metrics(_metrics)
    logger.info("Token cache reset.")
