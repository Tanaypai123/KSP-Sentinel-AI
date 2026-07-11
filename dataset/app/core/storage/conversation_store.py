from typing import Any, Optional, Dict
from app.core.storage.interfaces import ConversationStateStore

class InMemoryConversationStore(ConversationStateStore):
    """
    In-memory storage provider for Conversation State.
    Maintains a dictionary mapping conversation IDs to state objects.
    """

    def __init__(self):
        self._states: Dict[str, Any] = {}

    def load(self, conversation_id: str) -> Optional[Any]:
        return self._states.get(conversation_id)

    def save(self, conversation_id: str, state: Any) -> None:
        self._states[conversation_id] = state

    def delete(self, conversation_id: str) -> None:
        self._states.pop(conversation_id, None)

    def exists(self, conversation_id: str) -> bool:
        return conversation_id in self._states

    def clear(self) -> None:
        self._states.clear()
