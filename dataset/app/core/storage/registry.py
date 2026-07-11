from app.core.storage.interfaces import ConversationStateStore, CacheProvider
from app.core.storage.conversation_store import InMemoryConversationStore
from app.core.storage.cache_provider import LRUCacheProvider

class StorageRegistry:
    """
    Registry for managing concrete storage and caching providers.
    Enables dependency injection for pluggable backend strategies.
    By default, registers LRUCacheProvider as the production-hardened cache backend.
    """
    _conversation_store: ConversationStateStore = InMemoryConversationStore()
    _cache_provider: CacheProvider = LRUCacheProvider(max_entries=10000, ttl_seconds=300)

    @classmethod
    def get_conversation_store(cls) -> ConversationStateStore:
        return cls._conversation_store

    @classmethod
    def set_conversation_store(cls, store: ConversationStateStore) -> None:
        cls._conversation_store = store

    @classmethod
    def get_cache_provider(cls) -> CacheProvider:
        return cls._cache_provider

    @classmethod
    def set_cache_provider(cls, provider: CacheProvider) -> None:
        cls._cache_provider = provider
