"""
Storage-agnostic caching proxy delegating execution to registry-injected CacheProvider.
"""
from typing import Any, Optional, Dict
from app.core.storage.registry import StorageRegistry

class AnalyticalCacheProxy:
    """
    A lightweight proxy class delegating cache actions to the configured CacheProvider.
    Maintains full backward compatibility.
    """

    @property
    def _provider(self):
        return StorageRegistry.get_cache_provider()

    def get(self, key: str) -> Optional[Any]:
        return self._provider.get(key)

    def set(self, key: str, data: Any) -> None:
        self._provider.set(key, data)

    def clear(self) -> None:
        self._provider.clear()

    def contains(self, key: str) -> bool:
        return self._provider.contains(key)

    def stats(self) -> Dict[str, Any]:
        return self._provider.stats()


# Expose global cache instance using the proxy pattern
global_cache = AnalyticalCacheProxy()
