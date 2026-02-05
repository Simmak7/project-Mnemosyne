"""
RAG Query Cache - Simple LRU cache with TTL for repeated queries.

Caches retrieval results to avoid redundant database queries for
repeated or similar queries within a short time window.
"""

import hashlib
import time
from collections import OrderedDict
from dataclasses import dataclass
from threading import Lock
from typing import Any, Optional, Tuple

# Default cache settings
DEFAULT_MAX_SIZE = 100
DEFAULT_TTL_SECONDS = 300  # 5 minutes


@dataclass
class CacheEntry:
    """Cache entry with value and expiration time."""
    value: Any
    expires_at: float


class QueryCache:
    """
    Thread-safe LRU cache with TTL for RAG query results.

    Features:
    - LRU eviction when max size is reached
    - TTL-based expiration
    - Thread-safe operations
    - Configurable size and TTL
    """

    def __init__(self, max_size: int = DEFAULT_MAX_SIZE, ttl_seconds: int = DEFAULT_TTL_SECONDS):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = Lock()
        self._hits = 0
        self._misses = 0

    def _make_key(self, user_id: int, query: str, config_hash: str) -> str:
        """Create a cache key from user_id, query, and config hash."""
        key_str = f"{user_id}:{query.lower().strip()}:{config_hash}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def _config_hash(self, **config_options) -> str:
        """Create a hash of config options that affect query results."""
        # Sort keys for consistent hashing
        sorted_items = sorted(config_options.items())
        config_str = ":".join(f"{k}={v}" for k, v in sorted_items)
        return hashlib.md5(config_str.encode()).hexdigest()[:8]

    def get(
        self,
        user_id: int,
        query: str,
        min_similarity: float = 0.3,
        max_sources: int = 10,
        include_images: bool = True,
        include_graph: bool = True,
    ) -> Optional[Any]:
        """
        Get cached query result if available and not expired.

        Returns None if not in cache or expired.
        """
        config_hash = self._config_hash(
            min_similarity=min_similarity,
            max_sources=max_sources,
            include_images=include_images,
            include_graph=include_graph,
        )
        key = self._make_key(user_id, query, config_hash)

        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._misses += 1
                return None

            # Check if expired
            if time.time() > entry.expires_at:
                del self._cache[key]
                self._misses += 1
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            return entry.value

    def set(
        self,
        user_id: int,
        query: str,
        value: Any,
        min_similarity: float = 0.3,
        max_sources: int = 10,
        include_images: bool = True,
        include_graph: bool = True,
    ) -> None:
        """
        Store a query result in the cache.

        Evicts oldest entries if cache is at max size.
        """
        config_hash = self._config_hash(
            min_similarity=min_similarity,
            max_sources=max_sources,
            include_images=include_images,
            include_graph=include_graph,
        )
        key = self._make_key(user_id, query, config_hash)

        with self._lock:
            # Remove oldest if at capacity
            while len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)

            # Add new entry
            self._cache[key] = CacheEntry(
                value=value,
                expires_at=time.time() + self.ttl_seconds,
            )

    def invalidate(self, user_id: int) -> int:
        """
        Invalidate all cache entries for a user.

        Returns number of entries removed.
        """
        with self._lock:
            keys_to_remove = [
                key for key in self._cache.keys()
                if key.startswith(f"{user_id}:")
            ]
            for key in keys_to_remove:
                del self._cache[key]
            return len(keys_to_remove)

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def stats(self) -> dict:
        """Get cache statistics."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 3),
            }


# Global cache instance
_query_cache: Optional[QueryCache] = None


def get_query_cache() -> QueryCache:
    """Get or create the global query cache instance."""
    global _query_cache
    if _query_cache is None:
        _query_cache = QueryCache()
    return _query_cache


def cache_retrieval_results(
    user_id: int,
    query: str,
    config: 'QueryExecutionConfig',
    results: Tuple,
) -> None:
    """
    Cache retrieval results for a query.

    Args:
        user_id: User ID
        query: Query string
        config: Query configuration
        results: Tuple of retrieval results
    """
    cache = get_query_cache()
    cache.set(
        user_id=user_id,
        query=query,
        value=results,
        min_similarity=config.min_similarity,
        max_sources=config.max_sources,
        include_images=config.include_images,
        include_graph=config.include_graph,
    )


def get_cached_retrieval_results(
    user_id: int,
    query: str,
    config: 'QueryExecutionConfig',
) -> Optional[Tuple]:
    """
    Get cached retrieval results for a query.

    Returns None if not in cache.
    """
    cache = get_query_cache()
    return cache.get(
        user_id=user_id,
        query=query,
        min_similarity=config.min_similarity,
        max_sources=config.max_sources,
        include_images=config.include_images,
        include_graph=config.include_graph,
    )
