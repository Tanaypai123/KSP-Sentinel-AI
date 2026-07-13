from typing import Tuple
import re
from app.ai.conversation_engine import ConversationState

class ClarificationManager:
    @staticmethod
    def detect_ambiguity(query: str, state: ConversationState, merged_intent: str, is_followup: bool) -> bool:
        """
        Detects if the query is a follow-up that relies on an active record,
        but multiple active records exist, requiring clarification.
        """
        if not is_followup:
            return False
            
        if merged_intent not in ["SEARCH_ACCUSED", "SEARCH_VICTIMS", "FIR_LOOKUP", "SEARCH_POLICE_STATION", "SEARCH_LOCATION", "SEARCH_OFFICER", "AGGREGATE_COUNT"]:
            return False
            
        if len(state._active_records) > 1:
            # Check unique IDs
            unique_ids = set()
            for rec in state._active_records:
                rec_id = rec.get("crime_no") or rec.get("fir_no") or rec.get("case_no")
                if rec_id: unique_ids.add(rec_id)
                
            if len(unique_ids) > 1:
                q_low = query.lower()
                if not re.search(r"\b(first|second|third|latest|newest|this|that|both|previous|last|recent|other|earlier|prior)\b", q_low):
                    return True
                
        return False
        
    @staticmethod
    def store_clarification(query: str, intent: str, state: ConversationState) -> str:
        """
        Stores the pending state and generates a dynamic prompt based on active records.
        """
        state.pending_clarification = True
        state.clarification_query = query
        state.clarification_intent = intent
        state.clarification_options = state._active_records.copy()
        
        ids = []
        for rec in state.clarification_options:
            rec_id = rec.get("crime_no") or rec.get("fir_no") or rec.get("case_no")
            if rec_id:
                ids.append(rec_id)
                
        if len(ids) == 2:
            return f"Do you mean FIR {ids[0]} or FIR {ids[1]}?"
        elif len(ids) > 2:
            options_str = ", ".join(f"FIR {id}" for id in ids[:-1]) + f", or FIR {ids[-1]}"
            return f"Do you mean {options_str}?"
        else:
            return "Which specific record do you mean?"
            
    @staticmethod
    def resolve_clarification(query: str, state: ConversationState) -> Tuple[bool, str, str]:
        """
        Intercepts incoming query if pending_clarification is True.
        Attempts to map the user's answer to one of the options.
        Returns (is_resolved, original_query, original_intent).
        """
        if not state.pending_clarification:
            return False, query, ""
            
        q_low = query.lower()
        
        # Explicit Reset Bypass
        if any(x in q_low for x in ["forget", "reset", "clear", "new chat", "start over"]):
            state.pending_clarification = False
            state.clarification_query = None
            state.clarification_intent = None
            state.clarification_options = []
            return False, query, ""
            
        selected_rec = None
        
        if re.search(r"\bfirst\b", q_low) and len(state.clarification_options) >= 1:
            selected_rec = state.clarification_options[0]
        elif re.search(r"\bsecond\b", q_low) and len(state.clarification_options) >= 2:
            selected_rec = state.clarification_options[1]
        elif re.search(r"\bthird\b", q_low) and len(state.clarification_options) >= 3:
            selected_rec = state.clarification_options[2]
            
        if not selected_rec:
            for rec in state.clarification_options:
                rec_id = rec.get("crime_no") or rec.get("fir_no") or rec.get("case_no")
                if rec_id and rec_id.lower() in q_low:
                    selected_rec = rec
                    break
                    
        if selected_rec:
            state.pending_clarification = False
            state._active_records = [selected_rec]
            state.active_fir = selected_rec
            state.active_record = selected_rec
            
            orig_query = state.clarification_query
            orig_intent = state.clarification_intent
            
            state.clarification_query = None
            state.clarification_intent = None
            state.clarification_options = []
            
            return True, orig_query, orig_intent
            
        return False, query, ""

