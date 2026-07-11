from abc import ABC, abstractmethod
from typing import Any, Optional, Dict

class ConversationStateStore(ABC):
    """
    Abstract Interface for managing Conversation State Storage.
    Enables pluggable state backends (in-memory, Redis, DynamoDB, etc.).
    """

    @abstractmethod
    def load(self, conversation_id: str) -> Optional[Any]:
        """Load conversation state from the storage backend."""
        pass

    @abstractmethod
    def save(self, conversation_id: str, state: Any) -> None:
        """Save conversation state to the storage backend."""
        pass

    @abstractmethod
    def delete(self, conversation_id: str) -> None:
        """Delete conversation state from the storage backend."""
        pass

    @abstractmethod
    def exists(self, conversation_id: str) -> bool:
        """Check if conversation state exists in the backend."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all conversation states in the backend."""
        pass


class CacheProvider(ABC):
    """
    Abstract Interface for managing cache providers.
    Enables pluggable cache backends (in-memory, Redis, Disk, etc.).
    """

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get an entry from the cache."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set an entry in the cache."""
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete an entry from the cache."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all cache entries."""
        pass

    @abstractmethod
    def contains(self, key: str) -> bool:
        """Check if an entry exists in the cache."""
        pass

    @abstractmethod
    def stats(self) -> Dict[str, Any]:
        """Retrieve operational statistics of the cache provider."""
        pass
