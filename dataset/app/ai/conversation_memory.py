from typing import Dict, Any

# Simple in‑process conversation memory. Stores the last parsed query (intent + entities)
# for the current process. This is sufficient for a single‑user, single‑session
# scenario typical of the AI Copilot demo. The memory is reset only when the
# process restarts.

_last_state: Dict[str, Any] = {
    "intent": None,
    "entities": {},
}

def get_last_state() -> Dict[str, Any]:
    """Return a shallow copy of the stored last parsed state.

    The returned dict has the shape {"intent": str | None, "entities": dict}.
    ``None`` is used for missing intent, and missing entity values are omitted.
    """
    return {"intent": _last_state.get("intent"), "entities": _last_state.get("entities", {}).copy()}

def merge_with_last(new_state: Dict[str, Any]) -> Dict[str, Any]:
    """Merge a newly parsed query with the previously stored state.

    * ``intent`` – if the new state provides a non‑null intent, it replaces the
      previous one; otherwise the previous intent is retained.
    * ``entities`` – for each entity, a non‑null value in the new state overrides
      the previous value; missing/``None`` values keep the old value.
    The function returns a new merged dict without mutating the stored state.
    """
    merged_intent = new_state.get("intent") or _last_state.get("intent")
    prev_entities = _last_state.get("entities", {})
    new_entities = new_state.get("entities", {})
    merged_entities: Dict[str, Any] = {}
    for key in set(prev_entities) | set(new_entities):
        new_val = new_entities.get(key)
        if new_val is not None:
            merged_entities[key] = new_val
        else:
            merged_entities[key] = prev_entities.get(key)
    return {"intent": merged_intent, "entities": merged_entities}

def update_state(state: Dict[str, Any]) -> None:
    """Persist the given state as the last parsed query.

    The supplied ``state`` should contain ``intent`` and ``entities`` keys.
    """
    global _last_state
    _last_state = {
        "intent": state.get("intent"),
        "entities": state.get("entities", {}).copy(),
    }
