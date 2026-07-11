from typing import Dict, Any
from app.ai.conversation_engine import ConversationState
from app.ai.pronoun_resolver import PronounResolver
from app.ai.reference_resolver import ReferenceResolver
from app.ai.clarification_manager import ClarificationManager
from app.ai.response_generator import ResponseGenerator

class ContextResolverPipeline:
    @staticmethod
    def resolve(
        query: str,
        state: ConversationState,
        intent_val: str,
        is_followup_intent: bool,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Orchestrates all resolver logic (Pronouns -> References -> Clarifications)
        in a single deterministic pipeline.
        Returns a dictionary with the resolution status, updated intent/entities,
        and any early error response formatters if ambiguity is detected.
        """
        # Clear previous filters for explicit FIR Lookups
        if intent_val == "FIR_LOOKUP" or "ksp-" in query.lower():
            preserve_keys = {"identifiers", "fir_number", "limit", "offset", "sort_by", "sort_order"}
            for k in list(entities.keys()):
                if k not in preserve_keys:
                    entities.pop(k, None)

        # Step 1: Pronoun Resolution
        # Resolve pronouns ("he", "she", "it", etc.) using the active context.
        was_pronoun, resolved_ents, pron_err = PronounResolver.resolve(query, state)
        if was_pronoun:
            if pron_err:
                def build_err(start_time, confidence):
                    return ResponseGenerator.build_ambiguous_error(pron_err, confidence, start_time)
                return {
                    "error": True,
                    "error_response": build_err
                }
            # Merge resolved entities
            for k, v in resolved_ents.items():
                if v is not None:
                    entities[k] = v

        # Step 2: Reference Resolution
        # Resolve ordinals ("first", "second") or superlatives ("latest") to in-memory records.
        was_ref, resolved_rec, ref_err = ReferenceResolver.resolve(query, state)
        if was_ref:
            if ref_err:
                def build_err(start_time, confidence):
                    return ResponseGenerator.build_clarification_required(intent_val, confidence, start_time)
                return {
                    "error": True,
                    "error_response": build_err
                }
            if resolved_rec:
                state.active_fir = resolved_rec
                state.active_record = resolved_rec
                rec_id = resolved_rec.get("crime_no") or resolved_rec.get("fir_no") or resolved_rec.get("case_no")
                if rec_id:
                    entities["identifiers"] = [rec_id]
                    entities["fir_number"] = [rec_id]
                    intent_val = "FIR_LOOKUP"

        # Step 3: Clarification / Ambiguity Check
        # Check if the query refers to a resource ambiguously when multiple active records are present.
        is_deterministic = (
            "victim" in query.lower() or
            "officer" in query.lower() or
            "investigating" in query.lower() or
            "similar" in query.lower() or
            "compare" in query.lower() or
            "ksp-" in query.lower() or
            was_ref or
            intent_val in ["COMPARE_CASES", "SEARCH_VICTIMS", "SEARCH_OFFICER", "SEARCH_POLICE_STATION", "SEARCH_LOCATION", "FIR_LOOKUP"]
        )
        
        if not is_deterministic and ClarificationManager.detect_ambiguity(query, state, intent_val, is_followup_intent):
            msg = ClarificationManager.store_clarification(query, intent_val, state)
            def build_err(start_time, confidence):
                return ResponseGenerator.build_ambiguous_error(msg, confidence, start_time)
            return {
                "error": True,
                "error_response": build_err
            }

        return {
            "error": False,
            "intent_val": intent_val,
            "entities": entities
        }
