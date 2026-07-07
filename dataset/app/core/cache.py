"""In-memory caching utility for repeated database and analytical queries.

Provides a TTL-based cache (default 5 minutes) to speed up operations and reduce
duplicate SQL execution.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional


class AnalyticalCache:
    """Intelligent in-memory cache supporting key-based lookup and 5-minute TTL expiration."""

    def __init__(self, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache if it exists and is not expired."""
        if key in self._cache:
            entry = self._cache[key]
            if time.time() - entry["timestamp"] < self.ttl:
                return entry["data"]
            else:
                # Evict expired entry
                del self._cache[key]
        return None

    def set(self, key: str, data: Any) -> None:
        """Store a value in the cache with the current timestamp."""
        self._cache[key] = {
            "timestamp": time.time(),
            "data": data
        }

    def clear(self) -> None:
        """Clear all entries in the cache."""
        self._cache.clear()


# Shared cache instance
global_cache = AnalyticalCache(ttl_seconds=300)
