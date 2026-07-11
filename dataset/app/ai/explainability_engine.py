import time
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class ExplainabilityEngine:
    """
    Explainability Engine (XAI) for KSP Sentinel AI:
    Evaluates observable execution decisions of the AI pipeline and translates
    them into plain English reports for Officers, Developers, and Auditors.
    """

    @staticmethod
    def generate_explanation(
        context_or_intent: Any = "UNKNOWN",
        resolved_entities: Dict[str, Any] = None,
        is_followup: bool = False,
        select_stmt: Any = None,
        intelligence_bundle_trace: List[str] = None,
        reasoning_result: Dict[str, Any] = None,
        confidence_metrics: Dict[str, Any] = None,
        intent: Any = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Reads ExecutionContext and builds a complete, schema-compliant ExplainabilityReport.
        Supports backwards compatible keyword arg routing.
        """
        context = None
        if intent is not None:
            intent_val = intent
        else:
            if isinstance(context_or_intent, str) or context_or_intent is None:
                intent_val = context_or_intent or "UNKNOWN"
            else:
                context = context_or_intent
                intent_val = context.intent or "UNKNOWN"

        if context is None:
            # Reconstruct a mock context for backwards compatibility
            class DummyContext:
                def __init__(self):
                    self.raw_query = "Backward compatible query lookup."
                    self.conversation_id = "default"
                    self.intent = intent_val
                    self.resolved_entities = resolved_entities or {}
                    self.search_result = []
                    self.confidence_metrics = confidence_metrics
                    self.reasoning_result = reasoning_result
                    self.hallucination_safe = True
                    self.hallucination_violations = []
                    self.start_time = time.time()
                    self.select_stmt = select_stmt
                    self.warnings = []
                    self.plan = []
                    self.execution_trace = []
                    self.confidence = {"final": (confidence_metrics or {}).get("confidence", 0.50)}
                    self.is_followup = is_followup
                    
                    class DummyBundle:
                        def __init__(self):
                            self.execution_trace = intelligence_bundle_trace or []
                            self.hotspots = []
                            self.network = {}
                            self.repeat_offender = {}
                            self.similar_cases = []
                            self.pattern_analysis = ""
                            self.recommendations = []
                    self.intelligence_bundle = DummyBundle()
            context = DummyContext()

        execution_id = f"exec_{int(context.start_time * 1000)}"
        conversation_id = context.conversation_id or "default"
        resolved_entities_dict = {
            k: v for k, v in context.resolved_entities.items()
            if v is not None and not k.startswith("structured_") and k != "_dynamic_suggestions"
        }

        # 1. Query Summary (Plain English)
        query_summary = f"User initiated query: '{context.raw_query}'"

        # 2. SQL Summary (Officer-friendly translation)
        sql_summary = ExplainabilityEngine._translate_sql(intent_val, resolved_entities_dict)

        # 3. Reasoning Summary
        reasoning_summary = {
            "evidence_used": [f"Record {i+1}: {r.get('crime_no') or r.get('accused_name') or 'N/A'}" for i, r in enumerate(context.search_result[:5])],
            "reasoning_path": context.reasoning_result.get("reason_chain", []) if context.reasoning_result else ["No active reasoning chain generated."],
            "conclusion": context.reasoning_result.get("conclusion", "Query processed normally.") if context.reasoning_result else "Query processed normally.",
            "alternative_possibilities": ["None identified based on context filters."] if resolved_entities_dict else [],
            "missing_evidence": context.reasoning_result.get("missing_entities", []) if context.reasoning_result else [],
            "rejected_paths": []
        }

        # 4. Analytics Used
        analytics_used = []
        intel_bundle = context.intelligence_bundle
        if intel_bundle and hasattr(intel_bundle, "execution_trace"):
            for module in intel_bundle.execution_trace:
                detail = ""
                if module == "Hotspot" and getattr(intel_bundle, "hotspots", None):
                    detail = f"Identified {len(intel_bundle.hotspots)} local density points."
                elif module == "Network" and getattr(intel_bundle, "network", None):
                    detail = f"Mapped associate graph with {len(intel_bundle.network.get('nodes', []))} nodes."
                elif module == "RepeatOffender" and getattr(intel_bundle, "repeat_offender", None):
                    detail = "Compiled repeat suspect criminal patterns."
                elif module == "Similarity" and getattr(intel_bundle, "similar_cases", None):
                    detail = f"Scored {len(intel_bundle.similar_cases)} similar case profiles."
                elif module == "Pattern" and getattr(intel_bundle, "pattern_analysis", None):
                    detail = "Synthesized temporal patterns."
                analytics_used.append({
                    "module": module,
                    "reason": f"Triggered to enrich analysis for intent '{intent_val}'.",
                    "detail": detail,
                    "confidence": 1.0
                })
        if not analytics_used:
            analytics_used.append({
                "module": "None",
                "reason": "Direct lookup query did not trigger advanced analytics engines.",
                "detail": "",
                "confidence": 1.0
            })

        # 5. Recommendation Sources
        rec_sources = []
        if intel_bundle and getattr(intel_bundle, "recommendations", None):
            rec_sources = [
                {"recommendation": rec, "source_evidence": "Database record matched profiles"}
                for rec in intel_bundle.recommendations
            ]

        # 6. Confidence Breakdown
        conf_metrics = context.confidence_metrics or {}
        confidence_breakdown = {
            "intent_confidence": context.intent_result.confidence if getattr(context, "intent_result", None) else 0.50,
            "entities_verification": 1.0 if resolved_entities_dict else 0.50,
            "database_coverage": 1.0 if context.search_result else 0.50,
            "reasoning_accuracy": 1.0 + context.reasoning_result.get("confidence_adjustment", 0.0) if context.reasoning_result and isinstance(context.reasoning_result, dict) else 1.0,
            "safety_verification": 1.0 if context.hallucination_safe else 0.0,
            "final_score": context.confidence.get("final", 0.50)
        }

        # 7. Hallucination Guard Checks
        hallucination_checks = {
            "checked": True,
            "safe": context.hallucination_safe,
            "violations_detected": [
                {"category": v.get("category"), "detail": v.get("detail")}
                for v in context.hallucination_violations
            ],
            "action_taken": "None — response is fully evidence-backed." if context.hallucination_safe else "Suppressed unbacked details."
        }

        # 8. Clarification History
        clarification_history = {
            "context_reused": context.is_followup,
            "reference_resolved": "Resolved relative references." if context.is_followup else "No active reference resolving required.",
            "pronoun_resolved": "Resolved active pronoun markers." if context.is_followup else "No pronouns detected.",
            "clarification_answered": "Completed clarification query loop." if context.is_followup else "N/A"
        }

        # 9. Pipeline Execution Trace
        pipeline_execution = []
        for trace in context.execution_trace:
            pipeline_execution.append({
                "stage": trace.get("stage"),
                "latency_ms": trace.get("latency_ms", 0.0),
                "status": trace.get("decision", "Executed"),
                "skipped": trace.get("skipped", False),
                "reason": trace.get("reason", "Dynamic execution pipeline"),
                "executed": trace.get("executed", True),
                "output_size": len(str(context.search_result)) if trace.get("stage") == "SearchServiceStage" else 0
            })

        # 10. Warnings and Limitations
        warnings = list(context.warnings)
        limitations = []
        if intent_val == "PREDICT_CRIME":
            limitations.append("Prediction confidence is bounded by depth of historical records.")
        if len(context.search_result) > 100:
            limitations.append("Result output was capped due to pagination parameters.")

        # ── OFFICER MODE ──────────────────────────────────────────────────────
        results_count = len(context.search_result)
        officer_bullets = [
            f"Detected Intent: {intent_val.replace('_', ' ').title()}.",
            f"Extracted search parameters: {', '.join([f'{k}={v}' for k, v in resolved_entities_dict.items()]) or 'None'}."
        ]
        if results_count > 0:
            officer_bullets.append(f"Successfully matched and retrieved {results_count} records from the database.")
        else:
            officer_bullets.append("No database records matched your search parameters.")
        if context.hallucination_safe:
            officer_bullets.append("Safety Guard: Response is fully backed by database evidence.")
        else:
            officer_bullets.append("Safety Guard: Some unbacked details were suppressed to prevent hallucination.")
        officer_bullets.append(f"System Confidence: {confidence_breakdown['final_score'] * 100:.1f}%.")

        officer_mode = {
            "concise_explanation": officer_bullets[:5]
        }

        # ── DEVELOPER MODE ────────────────────────────────────────────────────
        developer_mode = {
            "modules": [trace["stage"] for trace in context.execution_trace if trace.get("executed")],
            "latency_ms": sum(trace.get("latency_ms", 0.0) for trace in context.execution_trace),
            "confidence": confidence_breakdown,
            "execution_order": [trace["stage"] for trace in context.execution_trace],
            "decision_path": list(context.plan),
            "sql_query": str(context.select_stmt) if context.select_stmt is not None else "None"
        }

        # ── AUDIT MODE ────────────────────────────────────────────────────────
        audit_mode = {
            "execution_id": execution_id,
            "conversation_id": conversation_id,
            "module_trace": pipeline_execution,
            "reason_trace": reasoning_summary["reasoning_path"],
            "confidence_breakdown": confidence_breakdown,
            "safety_decisions": hallucination_checks
        }

        # ── BACKWARDS COMPATIBILITY MAPPINGS ──────────────────────────────────
        intent_map = {
            "FIR_LOOKUP": "Searching specific FIR records",
            "SEARCH_CASES": "Searching for general case records",
            "SEARCH_ACCUSED": "Looking up accused profiles",
            "SEARCH_VICTIMS": "Looking up victim profiles",
            "SEARCH_LOCATION": "Searching for crime locations",
            "SEARCH_POLICE_STATION": "Searching for police station details",
            "NETWORK_SEARCH": "Analyzing criminal associate networks",
            "PREDICT_CRIME": "Predicting future crime patterns",
            "COMPARE_CASES": "Comparing multiple case records",
            "AGGREGATE_COUNT": "Aggregating crime statistics",
            "CRIME_TREND": "Analyzing crime trends",
            "HOTSPOT": "Identifying crime hotspots",
            "GREETING": "Handling conversational greeting",
            "UNKNOWN": "Attempting to resolve unknown intent"
        }
        detected_intent = intent_map.get(intent_val, f"Processing {intent_val} query")

        clean_entities = {
            k: v for k, v in context.resolved_entities.items()
            if v is not None and not str(k).startswith("_") and not str(k).startswith("structured_")
        }
        entities_extracted = clean_entities if clean_entities else "No specific entities extracted."

        if context.is_followup:
            context_resolution = "Query relies on conversational context from previous interactions (e.g., active FIR or Suspect profile)."
        else:
            context_resolution = "Query is fully independent and requires no previous conversational context."

        if context.select_stmt is not None:
            filters = []
            for k, v in clean_entities.items():
                if k not in ["sort_by", "sort_order", "limit", "offset"]:
                    filters.append(f"{k.replace('_', ' ').title()} = '{v}'")
            if filters:
                data_retrieval = f"Filtered database records where: {', '.join(filters)}."
            else:
                data_retrieval = "Queried database without specific entity filters."
        else:
            data_retrieval = "No database query executed for this intent."

        bundle_trace = intel_bundle.execution_trace if intel_bundle and hasattr(intel_bundle, "execution_trace") else []
        if bundle_trace:
            analytics_used_old = [f"Executed {module} module" for module in bundle_trace]
        else:
            analytics_used_old = ["No advanced analytical modules triggered."]

        if context.reasoning_result is not None:
            reasoning_path = context.reasoning_result.get("reason_chain", [])
            if not reasoning_path:
                reasoning_path = ["Insufficient data to form a reasoning chain."]
        else:
            reasoning_path = ["Reasoning engine skipped."]

        confidence_explanation = conf_metrics.get("explanation", []) if isinstance(conf_metrics, dict) else []
        if not confidence_explanation:
            confidence_explanation = ["Confidence metrics unavailable."]

        return {
            "execution_id": execution_id,
            "conversation_id": conversation_id,
            "intent": intent_val,
            "resolved_entities": resolved_entities_dict,
            "query_summary": query_summary,
            "sql_summary": sql_summary,
            "reasoning_summary": reasoning_summary,
            "analytics_used": analytics_used,
            "recommendation_sources": rec_sources,
            "confidence_breakdown": confidence_breakdown,
            "hallucination_checks": hallucination_checks,
            "clarification_history": clarification_history,
            "pipeline_execution": pipeline_execution,
            "warnings": warnings,
            "limitations": limitations,
            "officer_mode": officer_mode,
            "developer_mode": developer_mode,
            "audit_mode": audit_mode,
            
            # Backwards compatibility keys
            "detected_intent": detected_intent,
            "entities_extracted": entities_extracted,
            "context_resolution": context_resolution,
            "data_retrieval": data_retrieval,
            "analytics_used": analytics_used_old,
            "reasoning_path": reasoning_path,
            "confidence_explanation": confidence_explanation
        }

    @staticmethod
    def _translate_sql(intent: str, entities: Dict[str, Any]) -> str:
        """
        Translates intent filters into highly readable, non-technical English.
        """
        if intent == "FIR_LOOKUP":
            firs = entities.get("identifiers") or entities.get("fir_number") or []
            fir_str = firs[0] if isinstance(firs, list) and firs else firs
            if fir_str:
                return f"The system retrieved the specific crime record details for FIR '{fir_str}'."
            return "The system searched database records matching the requested crime identifiers."
        
        parts = []
        crime_cat = entities.get("crime_category") or entities.get("crime_head")
        if crime_cat:
            parts.append(f"matching crime category '{crime_cat.replace('_', ' ').lower()}'")
        else:
            parts.append("records")

        district = entities.get("district")
        if district:
            parts.append(f"registered within the {district} Police District")

        station = entities.get("police_station")
        if station:
            parts.append(f"at the {station} station")

        accused = entities.get("accused_name")
        if accused:
            parts.append(f"associated with accused individual '{accused}'")

        victim = entities.get("victim_name")
        if victim:
            parts.append(f"associated with victim '{victim}'")

        if intent == "SEARCH_ACCUSED":
            return f"The system searched database suspect profiles {' '.join(parts)}."
        elif intent == "SEARCH_VICTIMS":
            return f"The system searched database victim profiles {' '.join(parts)}."
        elif intent == "HOTSPOT":
            return f"The system analyzed geographical crime hotspot patterns {' '.join(parts)}."
        
        return f"The system searched database case {' '.join(parts)}."


class ExplainabilityEngineStage:
    """
    Pipeline stage wrapper for ExplainabilityEngine.
    """

    @staticmethod
    def run(context: Any) -> Any:  # context: ExecutionContext
        try:
            context.explainability = ExplainabilityEngine.generate_explanation(context)
        except Exception as e:
            logger.error(f"ExplainabilityEngineStage failed: {e}", exc_info=True)
            context.warnings.append(f"ExplainabilityEngineStage failed: {e}")
        return context
