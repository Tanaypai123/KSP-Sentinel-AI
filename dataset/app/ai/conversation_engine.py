import re
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime

@dataclass
class ConversationState:
    conversation_id: str
    last_intent: Optional[str] = None
    last_query: Optional[str] = None
    last_entities: Dict[str, Any] = field(default_factory=dict)
    last_results: List[Dict[str, Any]] = field(default_factory=list)
    active_record: Optional[Dict[str, Any]] = None
    active_fir: Optional[Dict[str, Any]] = None
    active_accused: Optional[Dict[str, Any]] = None
    active_victim: Optional[Dict[str, Any]] = None
    active_station: Optional[Dict[str, Any]] = None
    active_district: Optional[Dict[str, Any]] = None
    active_crime_type: Optional[str] = None
    last_action: Optional[str] = None
    conversation_depth: int = 0
    topic_history: List[str] = field(default_factory=list)
    confidence: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    _active_records: List[Dict[str, Any]] = field(default_factory=list)
    
    # Phase 2.5 Clarification Engine
    pending_clarification: bool = False
    clarification_query: Optional[str] = None
    clarification_intent: Optional[str] = None
    clarification_options: List[Dict[str, Any]] = field(default_factory=list)
    
    # Validation regressions
    clarification_state: Optional[Dict[str, Any]] = None
    reference_cache: Optional[Dict[str, Any]] = None

    @property
    def entities(self) -> Dict[str, Any]:
        return self.last_entities

    @entities.setter
    def entities(self, val: Dict[str, Any]) -> None:
        self.last_entities = val

    @property
    def active_records(self) -> List[Dict[str, Any]]:
        return self._active_records

    @active_records.setter
    def active_records(self, val: List[Dict[str, Any]]) -> None:
        self._active_records = val


class ConversationEngine:
    """
    Stateless ConversationEngine supporting dynamic dispatch for 100% backwards compatibility.
    Acts as pure state management layer.
    """

    @classmethod
    def get_store(cls):
        from app.core.storage.registry import StorageRegistry
        return StorageRegistry.get_conversation_store()

    @classmethod
    def initialize(cls, conversation_id: str = "default") -> None:
        store = cls.get_store()
        if not store.exists(conversation_id):
            cls.reset(conversation_id)
            
    @classmethod
    def get_state(cls, conversation_id: str = "default") -> ConversationState:
        store = cls.get_store()
        if not store.exists(conversation_id):
            cls.initialize(conversation_id)
        return store.load(conversation_id)

    @classmethod
    def reset(cls, conversation_id: str = "default") -> None:
        store = cls.get_store()
        state = ConversationState(conversation_id=conversation_id)
        store.save(conversation_id, state)

    @classmethod
    def set_active_record(cls, arg1: Any, arg2: Any = None, arg3: str = "FIR") -> None:
        if isinstance(arg1, str) and (isinstance(arg2, dict) or arg2 is None):
            conversation_id = arg1
            record = arg2
            record_type = arg3
        else:
            conversation_id = "default"
            record = arg1
            record_type = arg2 if arg2 is not None else "FIR"

        state = cls.get_state(conversation_id)
        state.active_record = record
        
        # Append to active records, keep max 3
        exists = False
        def _get_id(r):
            return r.get("crime_no") or r.get("case_no") or r.get("fir_no")
            
        r_id = _get_id(record)
        for act in state._active_records:
            if _get_id(act) == r_id:
                exists = True
                break
                
        if not exists:
            state._active_records.append(record)
            if len(state._active_records) > 3:
                state._active_records.pop(0)
                
        if record_type == "FIR":
            state.active_fir = record
            if record.get("accused_names") and isinstance(record["accused_names"], list) and record["accused_names"]:
                state.active_accused = {"accused_name": record["accused_names"][0]}
            else:
                state.active_accused = None
            if record.get("victim_names") and isinstance(record["victim_names"], list) and record["victim_names"]:
                state.active_victim = {"victim_name": record["victim_names"][0]}
            else:
                state.active_victim = None
        elif record_type == "ACCUSED":
            state.active_accused = record
            state.active_victim = None
        elif record_type == "VICTIM":
            state.active_victim = record
            state.active_accused = None
        state.updated_at = datetime.now()
        cls.get_store().save(conversation_id, state)

    @classmethod
    def clear_active_record(cls, conversation_id: str = "default") -> None:
        state = cls.get_state(conversation_id)
        state.active_record = None
        state.active_fir = None
        state.active_accused = None
        state.active_victim = None
        state._active_records = []
        state.updated_at = datetime.now()
        cls.get_store().save(conversation_id, state)

    @classmethod
    def update_entities(cls, arg1: Any, arg2: Any = None) -> None:
        if isinstance(arg1, str) and (isinstance(arg2, dict) or arg2 is None):
            conversation_id = arg1
            new_entities = arg2
        else:
            conversation_id = "default"
            new_entities = arg1

        state = cls.get_state(conversation_id)
        state.last_entities.update(new_entities)
        state.updated_at = datetime.now()
        cls.get_store().save(conversation_id, state)

    @classmethod
    def update_results(cls, arg1: Any, arg2: Any = None) -> None:
        if isinstance(arg1, str) and (isinstance(arg2, list) or arg2 is None):
            conversation_id = arg1
            results = arg2
        else:
            conversation_id = "default"
            results = arg1

        state = cls.get_state(conversation_id)
        state.last_results = results
        
        if results and ("crime_no" in results[0] or "fir_no" in results[0] or "case_no" in results[0]):
            state._active_records = results[:3]
            
        state.updated_at = datetime.now()
        cls.get_store().save(conversation_id, state)

    @classmethod
    def update(cls, arg1: Any, arg2: Any = None, arg3: Any = None, is_final_update: bool = False) -> Dict[str, Any]:
        if isinstance(arg1, str) and isinstance(arg2, str):
            conversation_id = arg1
            query = arg2
            new_state = arg3
        else:
            conversation_id = "default"
            query = arg1
            new_state = arg2
            is_final_update = arg3 if arg3 is not None else False

        state = cls.get_state(conversation_id)
        q_low = query.lower()

        new_intent = new_state.get("intent")
        if new_intent is None:
            raise ValueError("ConversationEngine.update received None intent.")
        merged_intent = new_intent or state.last_intent
        
        prev_entities = state.last_entities.copy()
        new_entities = new_state.get("entities", {})
        
        if not is_final_update:
            from app.ai.topic_shift_detector import TopicShiftDetector
            is_shift, clear_fields = TopicShiftDetector.detect(query, state, merged_intent, new_entities)
            if "ALL" in clear_fields:
                cls.reset(conversation_id)
                return new_state
            elif is_shift:
                for field in clear_fields:
                    if hasattr(state, field):
                        if isinstance(getattr(state, field), list):
                            setattr(state, field, [])
                        else:
                            setattr(state, field, None)
                            
        merged_entities: Dict[str, Any] = {}
        
        followup_patterns = r"\b(what|who|which|how|any|show|open|only|filter|sort|find|when|where)\b"
        is_followup = bool(re.search(followup_patterns, q_low))
        if not new_entities and not new_intent:
            is_followup = True

        for key in set(prev_entities) | set(new_entities):
            new_val = new_entities.get(key)
            if new_val is not None:
                merged_entities[key] = new_val
            elif is_followup:
                merged_entities[key] = prev_entities.get(key)
            else:
                merged_entities[key] = None

        if not is_final_update:
            if "only pending" in q_low or "pending ones" in q_low:
                merged_entities["status"] = "Pending"
            if "sort them by newest" in q_low:
                merged_entities["sort_by"] = "date"
                merged_entities["sort_order"] = "desc"
            
        if is_final_update:
            state.last_intent = merged_intent
            state.last_query = query
            state.last_entities = merged_entities
            state.conversation_depth += 1
            state.updated_at = datetime.now()
            
            results = new_state.get("results", [])
            if results:
                cls.update_results(conversation_id, results)
                if merged_intent in ["SEARCH_CASES", "FIR_LOOKUP", "SEARCH_LOCATION", "SEARCH_POLICE_STATION"]:
                    def _get_id(r):
                        return r.get("crime_no") or r.get("case_no") or r.get("fir_no")
                    
                    curr_active = state.active_fir
                    if not curr_active or _get_id(curr_active) != _get_id(results[0]):
                        cls.set_active_record(conversation_id, results[0], "FIR")
                        
                elif merged_intent == "SEARCH_ACCUSED":
                    cls.set_active_record(conversation_id, results[0], "ACCUSED")
                elif merged_intent == "SEARCH_VICTIMS":
                    cls.set_active_record(conversation_id, results[0], "VICTIM")
            
        cls.get_store().save(conversation_id, state)
        return {"intent": merged_intent, "entities": merged_entities, "_is_followup": is_followup}
