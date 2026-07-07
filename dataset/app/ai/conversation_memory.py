from typing import Dict, Any

# Simple in‑process conversation memory. Stores the last parsed query (intent + entities)
# for the current process. This is sufficient for a single‑user, single‑session
# scenario typical of the AI Copilot demo. The memory is reset only when the
# process restarts.

_last_state: Dict[str, Any] = {
    "intent": None,
    "entities": {},
    "results": [],
}

def get_last_state() -> Dict[str, Any]:
    """Return a shallow copy of the stored last parsed state.

    The returned dict has the shape {"intent": str | None, "entities": dict}.
    ``None`` is used for missing intent, and missing entity values are omitted.
    """
    return {"intent": _last_state.get("intent"), "entities": _last_state.get("entities", {}).copy()}

def merge_with_last(new_state: Dict[str, Any], query: str = "") -> Dict[str, Any]:
    """Merge a newly parsed query with the previously stored state.
    State only carries over if the user explicitly asks a follow-up query.
    """
    merged_intent = new_state.get("intent") or _last_state.get("intent")
    prev_entities = _last_state.get("entities", {})
    new_entities = new_state.get("entities", {})
    merged_entities: Dict[str, Any] = {}
    
    # Enhanced follow-up detection
    import re
    followup_patterns = r"\b(what\s+about|how\s+about|and\s+in|and\s+for|what\s+if|who\s+is|any\s+similar|open\s+(the\s+)?first|open\s+(the\s+)?last)\b"
    is_followup = bool(re.search(followup_patterns, query.lower()))
    
    # If it's a completely new entity-less query and intent is missing, it might be a follow-up
    if not new_entities and not new_state.get("intent"):
        is_followup = True

    for key in set(prev_entities) | set(new_entities):
        new_val = new_entities.get(key)
        if new_val is not None:
            merged_entities[key] = new_val
        elif is_followup:
            merged_entities[key] = prev_entities.get(key)
        else:
            merged_entities[key] = None

    # Handle "Open the first FIR"
    if "first" in query.lower() and merged_intent == "FIR_LOOKUP" and not merged_entities.get("identifiers"):
        results = _last_state.get("results", [])
        if results:
            first_fir = results[0].get("crime_no") or results[0].get("fir_no") or results[0].get("case_no")
            if first_fir:
                merged_entities["identifiers"] = [first_fir]
                
    # Handle "Who is the accused" if no accused provided
    if merged_intent == "SEARCH_ACCUSED" and not merged_entities.get("accused_name"):
        # If we have a previous FIR, keep it to search accused in that FIR
        pass # Automatically handled by keeping previous entities like identifiers
            
    return {"intent": merged_intent, "entities": merged_entities}

def update_state(state: Dict[str, Any]) -> None:
    """Persist the given state as the last parsed query.

    The supplied ``state`` should contain ``intent`` and ``entities`` keys.
    """
    global _last_state
    _last_state = {
        "intent": state.get("intent"),
        "entities": state.get("entities", {}).copy(),
        "results": state.get("results", [])
    }
