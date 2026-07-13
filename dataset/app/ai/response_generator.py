from typing import Optional
import time
import logging

from sqlalchemy.orm import Session
from app.ai.response_templates import get_invalid_district
from app.ai.intelligence_engine import IntelligenceBundle

logger = logging.getLogger(__name__)

_DEFAULT_SUGGESTIONS = [
    "Show theft cases in Bengaluru",
    "Predict crime trends for assault",
    "Show accused named Raju",
    "Open FIR KSP-000123"
]

class FormattingContext:
    def __init__(self, intent, results, entities, confidence, intelligence_bundle):
        self.intent = intent
        self.search_result = results
        self.resolved_entities = entities
        self.confidence = {"final": confidence}
        self.intelligence_bundle = intelligence_bundle
        self.response = None
        self.reasoning_result = None
        self.confidence_metrics = None
        self.evidence_correlation = None
        self.timeline_report = None
        self.knowledge_graph_report = None
        self.decision_support_report = None
        self.similarity_report = None
        self.multi_agent_report = None
        self.predictive_report = None
        self.warnings = []
        self.hallucination_safe = True
        self.hallucination_violations = []


class ResponseGenerator:
    
    @staticmethod
    def _build_dict(success: bool, intent: str, summary: str, entities: dict, results: list, start_time: float, confidence: float, count: int = 0, error: str = None, suggestions: list = None, select_stmt=None) -> dict:
        duration = (time.time() - start_time) * 1000
        return {
            "success": success,
            "intent": intent,
            "summary": summary,
            "count": count,
            "entities": entities,
            "results": results,
            "metadata": {
                "query": "",
                "query_time_ms": round((time.time() - start_time) * 1000, 2),
                "cache_hit": False,
                "confidence": confidence,
                "suggestions": entities.get("_dynamic_suggestions") or _DEFAULT_SUGGESTIONS,
            },
            "recommended_queries": [],
            "explanation": {},
            "error": error,
            "insights": []
        }

    @staticmethod
    def build_multi_intent_error(start_time: float) -> dict:
        summary = "You have requested multiple actions. Please execute these requests one by one so I can give you the best results."
        return ResponseGenerator._build_dict(
            False, "UNKNOWN", summary, {}, [], start_time, 1.0, 
            error="Multiple intents detected", suggestions=["Split your request into two separate queries."]
        )

    @staticmethod
    def build_conversational(intent: str, text: str, confidence: float, start_time: float) -> dict:
        return ResponseGenerator._build_dict(
            True if intent != "UNKNOWN" else False, intent, text, {}, [], start_time, confidence, 
            error="Low intent confidence" if intent == "UNKNOWN" else None
        )

    @staticmethod
    def build_clarification_required(intent: str, confidence: float, start_time: float) -> dict:
        summary = "I am not entirely sure what you want to do. Could you please clarify your request?"
        return ResponseGenerator._build_dict(
            False, "UNKNOWN", summary, {}, [], start_time, confidence, 
            error="Clarification required", suggestions=_DEFAULT_SUGGESTIONS
        )

    @staticmethod
    def build_ambiguous_error(error_msg: str, confidence: float, start_time: float) -> dict:
        return ResponseGenerator._build_dict(
            False, "AMBIGUOUS", error_msg, {}, [], start_time, confidence
        )

    @staticmethod
    def build_invalid_district(raw_district: str, suggestions: list, intent: str, entities: dict, confidence: float, start_time: float) -> dict:
        summary = get_invalid_district(raw_district, suggestions)
        return ResponseGenerator._build_dict(
            False, "UNKNOWN", summary, entities, [], start_time, confidence, 
            error=f"District '{raw_district}' not found", suggestions=[f"Show cases in {s}" for s in suggestions]
        )

    @staticmethod
    def build_fuzzy_match(name_entity: str, table_name: str, top_matches: list, intent: str, entities: dict, confidence: float, start_time: float) -> dict:
        suggest_str = "\n  • ".join(top_matches)
        summary = f"I couldn't find an exact match for '{name_entity}'.\n\nHowever, I found similar names:\n  • {suggest_str}\n\nWould you like to search one of these?"
        return ResponseGenerator._build_dict(
            False, "UNKNOWN", summary, entities, [], start_time, confidence, 
            error="No exact match", suggestions=[f"Find {table_name} {m}" for m in top_matches]
        )

    @staticmethod
    def build_prediction(prediction: dict, intent: str, entities: dict, db: Session, confidence: float, start_time: float) -> dict:
        predicted_count = prediction.get("predicted_cases", 0)
        res = ResponseGenerator._build_dict(
            True, "PREDICT_CRIME", prediction.get("reasoning"), entities, prediction.get("historical_counts", []), 
            start_time, confidence, count=predicted_count
        )
        res["metadata"].update({
            "prediction": prediction, 
            "rows_scanned": prediction.get("data_points_used"), 
            "rows_returned": 1
        })
        from app.ai.insights import IntelligenceEngine as InsightsEngine
        res["insights"] = InsightsEngine.generate_insights(db, intent, entities, predicted_count)
        res["recommended_queries"] = InsightsEngine.generate_recommendations(intent, entities, predicted_count)
        res["explanation"] = {
            "intent": "PREDICT_CRIME",
            "entities": {k: v for k, v in entities.items() if v is not None and not k.startswith("structured_")},
            "reasoning": prediction.get("reasoning"),
            "filters": [f"{k}={v}" for k, v in entities.items() if v and not k.startswith("structured_")],
            "sql_summary": "None (Predictive OLS Model)",
            "algorithm": prediction.get("model_used"),
            "confidence": prediction.get("confidence"),
            "trend_direction": prediction.get("trend"),
            "risk_level": prediction.get("risk_level"),
            "historical_data_used": f"{prediction.get('data_points_used')} monthly records"
        }
        res["prediction"] = prediction
        return res

    @staticmethod
    def build_smart_action_response(intent_val: str, synthetic_summary: str, entities: dict, results: list, confidence: float, start_time: float) -> dict:
        res = ResponseGenerator._build_dict(True, intent_val, synthetic_summary, entities, results, start_time, confidence)
        res["summary"] = synthetic_summary
        return res

    @staticmethod
    def build_active_context_resolution(intent_val: str, synthetic_summary: str, entities: dict, active_fir: dict, confidence: float, start_time: float) -> dict:
        if synthetic_summary:
            res = ResponseGenerator._build_dict(True, intent_val, synthetic_summary, entities, [active_fir] if active_fir else [], start_time, confidence)
            res["summary"] = synthetic_summary
        else:
            res = ResponseGenerator._build_dict(True, intent_val, "I retrieved the requested details.", entities, [active_fir] if active_fir else [], start_time, confidence)
        return res

    @staticmethod
    def build_comparison_error(entities: dict, comp_firs: list, confidence: float, start_time: float) -> dict:
        summary = "I currently have only one FIR in the active conversation.\n\nPlease open another FIR before requesting a comparison."
        return ResponseGenerator._build_dict(True, "COMPARE_CASES", summary, entities, comp_firs, start_time, confidence)

    @staticmethod
    def build_comparison(f1: dict, f2: dict, entities: dict, comp_firs: list, confidence: float, start_time: float) -> dict:
        comp = []
        comp.append("CASE COMPARISON")
        comp.append("===============")
        
        comp.append("• Crime Number:")
        comp.append(f"  - Case 1: {f1.get('crime_no')}")
        comp.append(f"  - Case 2: {f2.get('crime_no')}")
        
        comp.append("• Crime Type:")
        comp.append(f"  - Case 1: {f1.get('crime_category')}")
        comp.append(f"  - Case 2: {f2.get('crime_category')}")
        
        comp.append("• District:")
        comp.append(f"  - Case 1: {f1.get('district_name')}")
        comp.append(f"  - Case 2: {f2.get('district_name')}")
        
        comp.append("• Police Station:")
        comp.append(f"  - Case 1: {f1.get('police_station_name')}")
        comp.append(f"  - Case 2: {f2.get('police_station_name')}")
        
        comp.append("• Status:")
        comp.append(f"  - Case 1: {f1.get('status_name')}")
        comp.append(f"  - Case 2: {f2.get('status_name')}")
        
        comp.append("• Registration Date:")
        comp.append(f"  - Case 1: {f1.get('crime_registered_date')}")
        comp.append(f"  - Case 2: {f2.get('crime_registered_date')}")
        
        a1 = ", ".join(f1.get('accused_names', [])) if f1.get('accused_names') else f1.get('accused_name', 'Unknown')
        a2 = ", ".join(f2.get('accused_names', [])) if f2.get('accused_names') else f2.get('accused_name', 'Unknown')
        comp.append("• Accused:")
        comp.append(f"  - Case 1: {a1}")
        comp.append(f"  - Case 2: {a2}")
        
        v1 = ", ".join(f1.get('victim_names', [])) if f1.get('victim_names') else f1.get('victim_name', 'Unknown')
        v2 = ", ".join(f2.get('victim_names', [])) if f2.get('victim_names') else f2.get('victim_name', 'Unknown')
        from app.ai.response_formatter import ResponseFormatter
        ctx = FormattingContext("COMPARE_CASES", comp_firs, entities, confidence, None)
        summary = ResponseFormatter.format_comparison(ctx, f1, f2)
        return ResponseGenerator._build_dict(True, "COMPARE_CASES", summary, entities, comp_firs, start_time, confidence)

    @staticmethod
    def build_sql_error(intent_val: str, entities: dict, confidence: float, start_time: float) -> dict:
        return ResponseGenerator.build_clarification_required(intent_val, confidence, start_time)

    @staticmethod
    def build_final_response(intent: str, results: list, entities: dict, select_stmt, total_count: int, db: Session, start_time: float, confidence: float, intelligence_bundle: Optional[IntelligenceBundle] = None) -> dict:
        actual_length = len(results)
        count = total_count if total_count >= 0 else actual_length
        
        if intent == "AGGREGATE_COUNT" and results:
            row = results[0]
            if isinstance(row, dict) and row:
                count = int(list(row.values())[0])
            elif isinstance(row, (int, float)):
                count = int(row)
                
        if count == 0:
            summary = "No matching information was found."
        else:
            # Delegate formatting responsibility entirely to ResponseFormatter
            from app.ai.response_formatter import ResponseFormatter
            mock_ctx = FormattingContext(intent, results, entities, confidence, intelligence_bundle)
            summary = ResponseFormatter.format(mock_ctx, mode="officer")

        suggestions = entities.get("_dynamic_suggestions") or _DEFAULT_SUGGESTIONS
        res = ResponseGenerator._build_dict(True, intent, summary, entities, results, start_time, confidence, count=count, suggestions=suggestions, select_stmt=None)
        
        # Internal insights (not officer-facing)
        res["insights"] = ["Intelligence Orchestrator active."]
        res["recommended_queries"] = ["View next page"]
        res["explanation"] = {
            "intent": intent,
            "entities": {k: v for k, v in entities.items() if v is not None and not k.startswith("structured_") and k != "_dynamic_suggestions"},
            "reasoning": "Dynamic intelligence pipeline executed.",
            "confidence": confidence,
        }
        return res
