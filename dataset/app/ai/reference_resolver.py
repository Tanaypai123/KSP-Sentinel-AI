from typing import Optional, Dict, Any, Tuple
import re
from app.ai.conversation_engine import ConversationState
from app.ai.memory_engine import MemoryEngine

class ReferenceResolver:
    @staticmethod
    def resolve(query: str, state: ConversationState) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Resolves conversational references to in-memory records.
        Returns (was_reference_detected, resolved_record, error_message)
        """
        query_lower = query.lower()
        mem = MemoryEngine.get_memory(state.conversation_id)
        
        # 1. Active Pointers
        active_pointers = r"\b(this|that|opened|same|current)\s+(fir|case|record)\b"
        if re.search(active_pointers, query_lower):
            active_fir = mem.active_fir if (mem and mem.active_fir) else state.active_fir
            if active_fir:
                return True, active_fir, None
            return True, None, "I don't have an active FIR opened. Which FIR do you mean?"
            
        # Station Pointer
        if re.search(r"\b(this|that|same|current)\s+(station|police station)\b", query_lower):
            active_station = mem.active_station if (mem and mem.active_station) else state.active_station
            if active_station:
                return True, active_station, None
            return True, None, "I couldn't identify the active police station reference."

        # Accused Pointer
        if re.search(r"\b(this|that|same|current)\s+(accused|suspect)\b", query_lower):
            active_accused = mem.active_accused if (mem and mem.active_accused) else state.active_accused
            if active_accused:
                return True, active_accused, None
            return True, None, "I couldn't identify the active accused reference."

        # District Pointer
        if re.search(r"\b(this|that|same|current)\s+(district|jurisdiction)\b", query_lower):
            active_district = mem.active_district if (mem and mem.active_district) else state.active_district
            if active_district:
                return True, active_district, None
            return True, None, "I couldn't identify the active district reference."

        # Vehicle Pointer
        if re.search(r"\b(this|that|same|current)\s+(vehicle|car|bike)\b", query_lower):
            active_vehicle = mem.active_vehicle if mem else None
            if active_vehicle:
                return True, active_vehicle, None
            return True, None, "I couldn't identify the active vehicle reference."

        # 2. Temporal Pointers
        if re.search(r"\bprevious\b", query_lower):
            if len(state._active_records) >= 2:
                return True, state._active_records[1], None
            return True, None, "I don't have a previous FIR in our conversation history."
            
        # 3. Superlatives
        superlatives = r"\b(latest|newest|recent|last)\b"
        if re.search(superlatives, query_lower):
            if state.last_results:
                sorted_results = sorted(state.last_results, key=lambda x: str(x.get("crime_registered_date", "")), reverse=True)
                return True, sorted_results[0], None
            elif state.active_fir:
                return True, state.active_fir, None
            return True, None, "I couldn't find a recent FIR. Could you specify the FIR number?"
            
        # 4. Ordinals
        if re.search(r"\bfirst\b", query_lower):
            if state.last_results and len(state.last_results) >= 1:
                return True, state.last_results[0], None
            return True, None, "I couldn't find a first FIR in our recent results."
            
        if re.search(r"\bsecond\b", query_lower):
            if state.last_results and len(state.last_results) >= 2:
                return True, state.last_results[1], None
            return True, None, "I couldn't find a second FIR in our recent results."
            
        if re.search(r"\bthird\b", query_lower):
            if state.last_results and len(state.last_results) >= 3:
                return True, state.last_results[2], None
            return True, None, "I couldn't find a third FIR in our recent results."
            
        return False, None, None

