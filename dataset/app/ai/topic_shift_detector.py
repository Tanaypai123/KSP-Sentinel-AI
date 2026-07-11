from typing import Dict, Any, Tuple, List
from app.ai.conversation_engine import ConversationState

class TopicShiftDetector:
    @staticmethod
    def detect(query: str, state: ConversationState, new_intent: str, new_entities: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Detects if the user has shifted topics, requiring a context wipe.
        Returns:
            (is_major_shift, fields_to_clear)
        """
        q_low = query.lower()
        fields_to_clear = []
        is_shift = False

        if not state:
            return False, []

        # 1. Explicit Reset
        if any(x in q_low for x in ["forget", "reset", "clear", "new chat", "start over"]):
            return True, ["ALL"]

        # 2. Hard Entity Overrides
        is_comparison = new_intent == "COMPARE_CASES" or "compare" in q_low
        if not is_comparison:
            new_dist = new_entities.get("district")
            new_crime = new_entities.get("crime_head")
            new_acc = new_entities.get("accused_name")
            
            if state.active_fir:
                prev_dist = state.active_fir.get("district_name") or state.active_fir.get("district")
            else:
                prev_dist = state.last_entities.get("district")
                
            if state.active_fir:
                prev_crime = state.active_fir.get("crime_category") or state.active_fir.get("crime_head")
            else:
                prev_crime = state.last_entities.get("crime_head")
                
            if state.active_accused:
                prev_acc = state.active_accused.get("accused_name")
            else:
                prev_acc = state.last_entities.get("accused_name")
            
            if new_dist and prev_dist and new_dist.lower() != prev_dist.lower():
                is_shift = True
            
            if new_crime and prev_crime and new_crime.lower() != prev_crime.lower():
                is_shift = True
                
            if new_acc and prev_acc and new_acc.lower() != prev_acc.lower():
                is_shift = True
                
            # If the intent pivots from a specific lookup to a new broad search
            if new_intent in ["SEARCH_CASES", "SEARCH_LOCATION", "SEARCH_ACCUSED"] and state.last_intent in ["FIR_LOOKUP", "SEARCH_OFFICER", "SEARCH_VICTIMS", "AGGREGATE_COUNT"]:
                if (new_dist and new_dist.lower() != (prev_dist or "").lower()) or \
                   (new_crime and new_crime.lower() != (prev_crime or "").lower()) or \
                   (new_acc and new_acc.lower() != (prev_acc or "").lower()):
                    is_shift = True

        if is_shift:
            fields_to_clear = ["active_record", "active_fir", "active_accused", "active_victim", "_active_records"]

        return is_shift, fields_to_clear

