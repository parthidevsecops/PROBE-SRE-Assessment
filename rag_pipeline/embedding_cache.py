"""
embedding_cache.py — In-memory LRU cache for SentenceTransformer embeddings.

Caches embedding computations to avoid recomputing the same text embeddings
across multiple retrieval calls within a session.
"""

from __future__ import annotations

import hashlib
import logging
from functools import lru_cache
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# Cache size: keep last 1000 embedding computations in memory
_CACHE_MAXSIZE = 1000


class _EmbeddingCacheKey:
    """Hashable key for embedding cache (text + model)."""

    def __init__(self, text: str, model: str) -> None:
        self.text = text
        self.model = model
        # Hash for O(1) equality check
        self._hash = hash((hashlib.md5(text.encode()).hexdigest(), model))

    def __hash__(self) -> int:
        return self._hash

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _EmbeddingCacheKey):
            return False
        return self.text == other.text and self.model == other.model


@lru_cache(maxsize=_CACHE_MAXSIZE)
def _cached_embed_single(text: str, model: str, embedding_fn) -> tuple:
    """Cache wrapper around a single embedding call.

    Args:
        text: Text to embed
        model: Model identifier (for cache key)
        embedding_fn: Callable that takes [text] and returns embeddings

    Returns:
        Tuple of embedding array (converted to tuple for hashability)
    """
    try:
        embeddings = embedding_fn([text])
    except TypeError as e:
        if "Unsupported input type" in str(e) or "Expected one of" in str(e):
            embeddings = embedding_fn(text)
        else:
            raise
    if isinstance(embeddings, list) and len(embeddings) > 0:
        return tuple(embeddings[0])
    return ()


def get_cached_embeddings(
    texts: list[str],
    model: str,
    embedding_fn,
) -> list:
    """Get embeddings with in-memory LRU caching.

    Args:
        texts: List of texts to embed
        model: Model identifier
        embedding_fn: Callable that takes list[str] and returns list[embedding]

    Returns:
        List of embeddings (same format as embedding_fn output)
    """
    if not texts:
        return []

    cached_results = []
    texts_to_compute = []
    indices_to_compute = []

    # Check which embeddings are already cached
    for i, text in enumerate(texts):
        try:
            cached_tuple = _cached_embed_single(text, model, embedding_fn)
            if cached_tuple:
                cached_results.append((i, list(cached_tuple)))
            else:
                texts_to_compute.append(text)
                indices_to_compute.append(i)
        except Exception:
            # Cache miss — compute fresh
            texts_to_compute.append(text)
            indices_to_compute.append(i)

    # Compute any uncached embeddings in batch
    if texts_to_compute:
        try:
            new_embeddings = embedding_fn(texts_to_compute)
            for i, (idx, emb) in enumerate(zip(indices_to_compute, new_embeddings)):
                cached_results.append((idx, emb))
                # Also populate the single-text cache for future calls
                _cached_embed_single(texts_to_compute[i], model, embedding_fn)
        except TypeError as e:
            if "Unsupported input type" in str(e) or "Expected one of" in str(e):
                logger.debug("Embedding function type mismatch, retrying individually: %s", e)
                cached_results = []
                for text in texts:
                    try:
                        emb_result = embedding_fn(text)
                        if isinstance(emb_result, list):
                            cached_results.append((texts.index(text), emb_result[0]))
                        else:
                            cached_results.append((texts.index(text), emb_result))
                    except Exception as inner_e:
                        logger.warning("Individual embedding failed: %s", inner_e)
                        return []
            else:
                logger.warning("Embedding computation failed: %s", e)
                return []
        except Exception as e:
            logger.warning("Embedding computation failed: %s", e)
            return []

    # Sort back to original order
    cached_results.sort(key=lambda x: x[0])
    return [emb for _, emb in cached_results]


def clear_embedding_cache() -> None:
    """Clear the embedding cache (e.g., after re-indexing)."""
    _cached_embed_single.cache_clear()
    logger.info("Embedding cache cleared (max size: %d)", _CACHE_MAXSIZE)


def get_embedding_cache_info() -> dict:
    """Return cache hit/miss statistics."""
    info = _cached_embed_single.cache_info()
    return {
        "hits": info.hits,
        "misses": info.misses,
        "maxsize": info.maxsize,
        "currsize": info.currsize,
        "hit_rate": info.hits / (info.hits + info.misses) if (info.hits + info.misses) > 0 else 0,
    }
