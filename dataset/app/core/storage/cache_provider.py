import time
import sys
from collections import OrderedDict
from typing import Any, Optional, Dict
from app.core.storage.interfaces import CacheProvider

class MemoryCacheProvider(CacheProvider):
    """
    Standard unbounded in-memory cache provider wrapping the existing TTL cache logic.
    Provides hits/misses statistics tracking.
    """

    def __init__(self, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            entry = self._cache[key]
            if time.time() - entry["timestamp"] < self.ttl:
                self._hits += 1
                return entry["data"]
            else:
                del self._cache[key]
        self._misses += 1
        return None

    def set(self, key: str, value: Any) -> None:
        self._cache[key] = {
            "timestamp": time.time(),
            "data": value
        }

    def delete(self, key: str) -> None:
        self._cache.pop(key, None)

    def clear(self) -> None:
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def contains(self, key: str) -> bool:
        if key in self._cache:
            entry = self._cache[key]
            if time.time() - entry["timestamp"] < self.ttl:
                return True
            else:
                del self._cache[key]
        return False

    def stats(self) -> Dict[str, Any]:
        memory_usage_bytes = sys.getsizeof(self._cache)
        for k, v in self._cache.items():
            memory_usage_bytes += sys.getsizeof(k) + sys.getsizeof(v)
            
        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "evictions": 0,
            "memory_usage_bytes": memory_usage_bytes
        }


class LRUCacheProvider(CacheProvider):
    """
    LRU (Least Recently Used) Cache Provider with automatic eviction,
    TTL expiration, and statistics reporting.
    """

    def __init__(self, max_entries: int = 1000, ttl_seconds: int = 300):
        self.max_entries = max_entries
        self.ttl = ttl_seconds
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            entry = self._cache[key]
            if time.time() - entry["timestamp"] < self.ttl:
                # Move accessed key to end (most recently used)
                self._cache.move_to_end(key)
                self._hits += 1
                return entry["data"]
            else:
                del self._cache[key]
        self._misses += 1
        return None

    def set(self, key: str, value: Any) -> None:
        if key in self._cache:
            del self._cache[key]
        elif len(self._cache) >= self.max_entries:
            # Pop the first element (least recently used)
            self._cache.popitem(last=False)
            self._evictions += 1

        self._cache[key] = {
            "timestamp": time.time(),
            "data": value
        }

    def delete(self, key: str) -> None:
        self._cache.pop(key, None)

    def clear(self) -> None:
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def contains(self, key: str) -> bool:
        if key in self._cache:
            entry = self._cache[key]
            if time.time() - entry["timestamp"] < self.ttl:
                return True
            else:
                del self._cache[key]
        return False

    def stats(self) -> Dict[str, Any]:
        memory_usage_bytes = sys.getsizeof(self._cache)
        for k, v in self._cache.items():
            memory_usage_bytes += sys.getsizeof(k) + sys.getsizeof(v)
            
        return {
            "size": len(self._cache),
            "max_size": self.max_entries,
            "hits": self._hits,
            "misses": self._misses,
            "evictions": self._evictions,
            "memory_usage_bytes": memory_usage_bytes
        }


class FutureRedisCacheProvider(CacheProvider):
    """
    Stub for Future Redis-backed Cache Provider.
    """

    def __init__(self, host: str = "localhost", port: int = 6379):
        self.host = host
        self.port = port

    def get(self, key: str) -> Optional[Any]:
        raise NotImplementedError("Redis cache provider is not yet implemented.")

    def set(self, key: str, value: Any) -> None:
        raise NotImplementedError("Redis cache provider is not yet implemented.")

    def delete(self, key: str) -> None:
        raise NotImplementedError("Redis cache provider is not yet implemented.")

    def clear(self) -> None:
        raise NotImplementedError("Redis cache provider is not yet implemented.")

    def contains(self, key: str) -> bool:
        raise NotImplementedError("Redis cache provider is not yet implemented.")

    def stats(self) -> Dict[str, Any]:
        raise NotImplementedError("Redis cache provider is not yet implemented.")
