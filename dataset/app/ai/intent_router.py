import re
from dataclasses import dataclass
from typing import Optional
from app.ai.pipeline import classify_pipeline_intent
from app.ai.response_templates import CONVERSATIONAL_RESPONSES

@dataclass
class IntentResult:
    intent: str
    confidence: float
    
    # Validation / Short-circuits
    is_multi_intent: bool = False
    is_conversational: bool = False
    conversational_response: Optional[str] = None
    clarification_required: bool = False
    
    # Explicit Action Overrides
    is_smart_action: bool = False
    smart_action_type: Optional[str] = None  # 'FIND_RELATED', 'SHOW_NEARBY', 'ANALYZE_NETWORK', 'VIEW_HOTSPOTS'
    
    # Follow-up Overrides
    is_comparison: bool = False
    is_similar_search: bool = False
    is_accused_followup: bool = False
    accused_followup_type: Optional[str] = None  # 'OTHER_FIRS', 'SAME_FIR'
    
    # Context Overrides
    is_victim_query: bool = False
    is_officer_query: bool = False
    is_date_query: bool = False
    is_fir_open_query: bool = False

class IntentRouter:
    @staticmethod
    def detect(query: str, is_followup_intent: bool = False, has_active_fir: bool = False, has_active_accused: bool = False) -> IntentResult:
        from app.ai.nlp_engine import NLPEngine
        normalized_query = NLPEngine.normalize_query(query)
        q_low = normalized_query.strip()
        
        result = IntentResult(intent="UNKNOWN", confidence=0.0)
        
        # 0. Incomplete Query Validation
        generic_tokens = {"show", "find", "search", "cases", "crime", "accused", "victim", "district", "police station", "location"}
        if q_low in generic_tokens or (len(q_low.split()) == 1 and q_low in generic_tokens):
            result.clarification_required = True
            return result

        # 0.5 Smart Action Overrides (Bypass conversational & aliases)
        smart_actions = {
            "find related cases": "FIND_RELATED",
            "show nearby crimes": "SHOW_NEARBY",
            "analyze network": "ANALYZE_NETWORK",
            "view hotspots": "VIEW_HOTSPOTS"
        }
        if q_low in smart_actions:
            result.is_smart_action = True
            result.smart_action_type = smart_actions[q_low]
            return result

        # 0.6 Alias Mapping
        alias_map = {
            "reset": "GENERAL_CHAT",
            "clear": "GENERAL_CHAT",
            "clear the chat": "GENERAL_CHAT",
            "clear chat": "GENERAL_CHAT",
            "crime trend": "CRIME_TREND",
            "crime trends": "CRIME_TREND",
            "trend": "CRIME_TREND",
            "crime statistics": "AGGREGATE_COUNT",
            "statistics": "AGGREGATE_COUNT",
            "distribution": "AGGREGATE_COUNT",
            "crime distribution": "AGGREGATE_COUNT",
            "hotspots": "HOTSPOT",
            "dangerous places": "HOTSPOT",
            "high crime areas": "HOTSPOT",
            "top crimes": "AGGREGATE_COUNT",
            "top crime categories": "AGGREGATE_COUNT",
            "most common crimes": "AGGREGATE_COUNT",
            "predict theft": "PREDICT_CRIME",
            "predict": "PREDICT_CRIME",
            "network": "NETWORK_SEARCH",
            "connections": "NETWORK_SEARCH",
            "linked cases": "NETWORK_SEARCH",
            "hotspot": "HOTSPOT",
            "risk zones": "HOTSPOT"
        }
        for alias, mapped_intent in alias_map.items():
            if q_low == alias or q_low.startswith(f"{alias} ") or q_low.endswith(f" {alias}"):
                result.intent = mapped_intent
                result.confidence = 1.0
                if mapped_intent in ["GREETING", "GOODBYE", "THANKS", "HELP", "BOT_IDENTITY", "BOT_CAPABILITIES", "UNKNOWN", "GENERAL_CHAT"]:
                    result.is_conversational = True
                    result.conversational_response = CONVERSATIONAL_RESPONSES.get(mapped_intent, CONVERSATIONAL_RESPONSES["UNKNOWN"])
                return result

        # 0.7 Regex Overrides — High-priority deterministic rules
        # "What about X?" / "What about murder?" → SEARCH_CASES (topic shift with crime type)
        if re.match(r'^what about (.+)\??$', q_low) and not re.search(r'\b(status|count|how many|statistics)\b', q_low):
            result.intent = "SEARCH_CASES"
            result.confidence = 0.92
            return result

        # "Where is the station?" / "What is the station location?" → SEARCH_LOCATION (NOT HOTSPOT)
        if re.search(r'\b(where is|location of|located|address of)\b', q_low) and re.search(r'\b(station|police station|ps)\b', q_low):
            result.intent = "SEARCH_LOCATION"
            result.confidence = 0.95
            if has_active_fir:
                result.is_officer_query = False  # specifically location
            return result

        # "Show his FIRs" / "List his cases" when active accused → accused followup FIR_LOOKUP
        if has_active_accused and re.search(r'\b(his|their|accused|suspect)\b', q_low) and re.search(r'\b(fir|firs|case|cases|records)\b', q_low):
            result.intent = "FIR_LOOKUP"
            result.confidence = 0.90
            result.is_accused_followup = True
            result.accused_followup_type = "OTHER_FIRS"
            return result

        # "The first one" / "The second one" / ordinal selectors → contextual resolution
        if re.match(r'^(the\s+)?(first|second|third|latest|newest|this one|that one|this|that)(\s+one)?$', q_low):
            # When there are active records, this selects by ordinal — let context resolution handle it
            # Don't trigger clarification; just mark as follow-up
            result.intent = "FIR_LOOKUP"
            result.confidence = 0.85
            if is_followup_intent or has_active_fir:
                result.is_fir_open_query = True
            return result

        # "Is he involved in other cases?" / "Are they in other FIRs?" with active accused → SEARCH_CASES
        if (has_active_accused or has_active_fir) and re.search(r'\b(he|she|they|accused)\b', q_low) and re.search(r'\b(involved|appear|found|other|more)\b', q_low):
            result.intent = "SEARCH_CASES"
            result.confidence = 0.90
            result.is_accused_followup = True
            result.accused_followup_type = "OTHER_FIRS"
            return result

        # "Who is the victim?" with active FIR → SEARCH_VICTIMS
        if has_active_fir and re.search(r'\b(victim|complainant|complainant name)\b', q_low):
            result.intent = "SEARCH_VICTIMS"
            result.confidence = 0.92
            result.is_victim_query = True
            return result

        # "Which station?" / "Which police station?" with active FIR → SEARCH_POLICE_STATION
        if has_active_fir and re.match(r'^(which|what)\s+(police\s+)?station', q_low):
            result.intent = "SEARCH_POLICE_STATION"
            result.confidence = 0.92
            return result

        # Timeline / chronological overrides (placed before classification to avoid short-circuiting)
        if has_active_fir:
            timeline_keywords = {"first", "earliest", "start", "begin", "last", "latest", "end", "conclude", "timeline", "chronology", "sequence", "happen first", "happen last"}
            if any(k in q_low for k in timeline_keywords) and not "explain" in q_low:
                result.intent = "FIR_LOOKUP"
                result.confidence = 0.95
                result.is_fir_open_query = True
                return result

        # Network / Relationship Graph overrides (placed before classification to avoid short-circuiting)
        network_keywords = {"network", "graph", "connection", "connected", "relationship", "relationships", "linked", "associate", "knowledge graph", "crime network", "accused network"}
        if any(k in q_low for k in network_keywords):
            result.intent = "NETWORK_SEARCH"
            result.confidence = 0.94
            return result

        # 1. Multi-Intent Check
        if " and " in normalized_query.lower():
            parts = normalized_query.lower().split(" and ")
            if len(parts) == 2:
                intent1, conf1 = classify_pipeline_intent(parts[0])
                intent2, conf2 = classify_pipeline_intent(parts[1])
                if conf1 > 0.60 and conf2 > 0.60 and intent1 != intent2:
                    result.is_multi_intent = True
                    return result

        # 2. TF-IDF Classification
        intent_obj, confidence = classify_pipeline_intent(normalized_query)
        intent_val = intent_obj.value if hasattr(intent_obj, 'value') else str(intent_obj)
        
        result.intent = intent_val
        result.confidence = confidence

        # 3. Conversational Short-circuit
        conversational_intents = ["GREETING", "GOODBYE", "THANKS", "HELP", "BOT_IDENTITY", "BOT_CAPABILITIES", "UNKNOWN", "GENERAL_CHAT"]
        if intent_val in conversational_intents:
            result.is_conversational = True
            result.conversational_response = CONVERSATIONAL_RESPONSES.get(intent_val, CONVERSATIONAL_RESPONSES["UNKNOWN"])
            return result

        # 5. Clarification Check — skip if there is an active FIR (follow-up context)
        if confidence < 0.60 and not is_followup_intent and not has_active_fir:
            result.clarification_required = True
            return result

        # 6. Context Resolution & Regex Overrides
        if is_followup_intent or "similar" in q_low or "compare" in q_low:
            if "compare" in q_low:
                result.intent = "COMPARE_CASES"
                result.confidence = 0.95
                result.is_comparison = True
                return result
            elif "similar" in q_low and has_active_fir:
                result.intent = "SEARCH_CASES"
                result.confidence = 0.90
                result.is_similar_search = True
                return result
                
            elif has_active_accused and re.search(r'\b(he|his|they|those|accused)\b', q_low):
                result.is_accused_followup = True
                if re.search(r'\b(other|firs|cases|investigated|district)\b', q_low):
                    if "other" in q_low:
                        result.accused_followup_type = "OTHER_FIRS"
                    else:
                        result.accused_followup_type = "SAME_FIR"
                return result

        # 7. Active FIR Explicit Field Queries
        if has_active_fir:
            if "victim" in q_low and intent_val == "SEARCH_ACCUSED":
                result.intent = "SEARCH_VICTIMS"
                result.is_victim_query = True
            elif "officer" in q_low or "investigating" in q_low:
                result.intent = "SEARCH_OFFICER"
                result.is_officer_query = True
            elif intent_val == "CRIME_TREND" or "when" in q_low:
                result.intent = "CRIME_TREND"
                result.is_date_query = True
            elif intent_val == "FIR_LOOKUP":
                if q_low.startswith("open another") or q_low.startswith("open the") or q_low.startswith("open fir") or q_low.startswith("show fir") or "previous" in q_low or "last" in q_low or "next" in q_low:
                    result.is_fir_open_query = True

        return result
