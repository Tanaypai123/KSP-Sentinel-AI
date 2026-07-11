from typing import Dict, Any, Tuple
import re
from app.ai.conversation_engine import ConversationState
from app.ai.memory_engine import MemoryEngine

class PronounResolver:
    @staticmethod
    def resolve(query: str, state: ConversationState) -> Tuple[bool, Dict[str, Any], str]:
        """
        Resolves generic pronouns (he, she, it, they, this) based on context.
        Returns:
            (was_resolved, resolved_entities, error_msg)
        """
        query_lower = query.lower()
        
        person_pronouns = r"\b(he|she|him|her|his|hers|they|them|their)\b"
        object_pronouns = r"\b(it|this|that|these|those|current|same)\b"
        
        # 1. Person Pronouns
        if re.search(person_pronouns, query_lower):
            mem = MemoryEngine.get_memory(state.conversation_id)
            active_acc = mem.active_accused if (mem and mem.active_accused) else state.active_accused
            active_vic = mem.active_victim if (mem and mem.active_victim) else state.active_victim
            active_fir = mem.active_fir if (mem and mem.active_fir) else state.active_fir
            
            acc_name = None
            vic_name = None
            
            if active_acc:
                acc_name = active_acc.get("accused_name")
            elif active_fir and (active_fir.get("accused_name") or active_fir.get("accused_names")):
                acc = active_fir.get("accused_name") or active_fir.get("accused_names")
                if isinstance(acc, list):
                    acc_name = acc[0]
                else:
                    acc_name = acc
            elif state.last_entities.get("accused_name"):
                acc_name = state.last_entities.get("accused_name")
                
            if active_vic:
                vic_name = active_vic.get("victim_name")
            elif active_fir and (active_fir.get("victim_name") or active_fir.get("victims")):
                vic = active_fir.get("victim_name") or active_fir.get("victims")
                if isinstance(vic, list):
                    vic_name = vic[0]
                else:
                    vic_name = vic
            elif state.last_entities.get("victim_name"):
                vic_name = state.last_entities.get("victim_name")

            if acc_name and vic_name:
                if state.last_intent == "SEARCH_ACCUSED" or "involved" in query_lower or "commit" in query_lower or "offence" in query_lower or "accused" in query_lower:
                    return True, {"accused_name": acc_name}, ""
                elif state.last_intent == "SEARCH_VICTIMS" or "victim" in query_lower:
                    return True, {"victim_name": vic_name}, ""
                else:
                    return True, {}, "Do you mean the accused or the victim?"
                    
            if acc_name:
                return True, {"accused_name": acc_name}, ""
            elif vic_name:
                return True, {"victim_name": vic_name}, ""
            else:
                # Pronoun exists, but no antecedent found
                pass
                
        # 2. Object Pronouns
        if re.search(object_pronouns, query_lower):
            active_pointers = r"\b(this|that|opened|same|current)\s+(fir|case|record)\b"
            if not re.search(active_pointers, query_lower):
                mem = MemoryEngine.get_memory(state.conversation_id)
                active_fir = mem.active_fir if (mem and mem.active_fir) else state.active_fir
                if active_fir:
                    fir_no = active_fir.get("crime_no") or active_fir.get("fir_no")
                    if fir_no:
                        return True, {"identifiers": [fir_no]}, ""
        
        return False, {}, ""

