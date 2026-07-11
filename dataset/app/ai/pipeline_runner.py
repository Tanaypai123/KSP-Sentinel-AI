import time
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

# Import original engines and services
from app.ai.query_parser import parse_query
from app.ai.sql_generator import generate_select
from app.ai.query_executor import execute_query
from app.ai.intent_router import IntentRouter
from app.ai.conversation_engine import ConversationEngine, ConversationState
from app.ai.reference_resolver import ReferenceResolver
from app.ai.pronoun_resolver import PronounResolver
from app.ai.clarification_manager import ClarificationManager
from app.ai.response_generator import ResponseGenerator
from app.ai.response_formatter import ResponseFormatter
from app.ai.intelligence_engine import IntelligenceBundle
from app.ai.hotspot_engine import HotspotEngine
from app.ai.crime_pattern_analyzer import CrimePatternAnalyzer
from app.ai.network_engine import NetworkEngine
from app.ai.repeat_offender_engine import RepeatOffenderEngine
from app.ai.similarity_engine import SimilarityEngine
from app.ai.recommendation_engine import RecommendationEngine
from app.ai.reasoning_engine import ReasoningEngine
from app.ai.confidence_engine import ConfidenceEngine
from app.ai.explainability_engine import ExplainabilityEngine, ExplainabilityEngineStage
from app.ai.hallucination_guard import HallucinationGuard, HallucinationGuardStage
from app.ai.memory_engine import MemoryEngineStage
from app.ai.evidence_correlation_engine import EvidenceCorrelationStage
from app.ai.multi_agent_engine import MultiAgentEngineStage
from app.ai.predictive_engine import PredictiveEngineStage
from app.ai.knowledge_graph_engine import KnowledgeGraphStage
from app.ai.timeline_engine import TimelineStage
from app.ai.case_similarity_engine import CaseSimilarityStage
from app.ai.decision_support_engine import DecisionSupportStage
from app.ai.enterprise_orchestrator import EnterpriseOrchestrator

logger = logging.getLogger(__name__)

@dataclass
class ExecutionContext:
    raw_query: str
    db: Session
    conversation_id: str = "default"
    intent: Optional[str] = None
    intent_result: Optional[Any] = None
    conversation_state: Optional[ConversationState] = None
    resolved_entities: Dict[str, Any] = field(default_factory=dict)
    search_result: List[Dict[str, Any]] = field(default_factory=list)
    intelligence_bundle: Optional[IntelligenceBundle] = None
    response: Optional[Dict[str, Any]] = None
    reasoning_result: Optional[Dict[str, Any]] = None
    confidence_metrics: Optional[Dict[str, Any]] = None
    explainability: Optional[Dict[str, Any]] = None
    plan: List[str] = field(default_factory=list)
    execution_trace: List[Dict[str, Any]] = field(default_factory=list)
    confidence: Dict[str, float] = field(default_factory=dict)
    is_followup: bool = False
    start_time: float = field(default_factory=time.time)
    select_stmt: Optional[Any] = None
    warnings: List[str] = field(default_factory=list)
    executed_stages: List[str] = field(default_factory=list)
    skipped_stages: List[str] = field(default_factory=list)
    hallucination_violations: List[Dict[str, str]] = field(default_factory=list)
    hallucination_safe: bool = True
    memory_audit: Optional[Dict[str, Any]] = None
    evidence_correlation: Optional[Dict[str, Any]] = None
    multi_agent_report: Optional[Dict[str, Any]] = None
    predictive_report: Optional[Dict[str, Any]] = None
    knowledge_graph_report: Optional[Dict[str, Any]] = None
    knowledge_graph: Optional[Any] = None
    timeline_report: Optional[Dict[str, Any]] = None
    similarity_report: Optional[Dict[str, Any]] = None
    decision_support_report: Optional[Dict[str, Any]] = None
    enterprise_report: Optional[Dict[str, Any]] = None

class PipelineRunner:
    @staticmethod
    def run(query: str, db: Session, conversation_id: Optional[str] = None) -> ExecutionContext:
        if conversation_id is None:
            conversation_id = "default"
            
        q_low = query.lower()
        if any(x in q_low for x in ["forget", "reset", "clear", "new chat", "start over"]):
            ConversationEngine.reset(conversation_id)
            
        context = ExecutionContext(raw_query=query, db=db, conversation_id=conversation_id, start_time=time.time())
        context.execution_trace = []
        context.confidence = {}
        context.warnings = []
        context.executed_stages = []
        context.skipped_stages = []
        
        STAGE_REGISTRY = {
            "IntentRouterStage": IntentRouterStage,
            "ConversationEngineStage": ConversationEngineStage,
            "ClarificationResolutionStage": ClarificationResolutionStage,
            "ReferenceResolverStage": ReferenceResolverStage,
            "PronounResolverStage": PronounResolverStage,
            "ClarificationCheckStage": ClarificationCheckStage,
            "QueryPlannerStage": QueryPlannerStage,
            "SearchServiceStage": SearchServiceStage,
            "IntelligenceEngineStage": IntelligenceEngineStage,
            "ReasoningEngineStage": ReasoningEngineStage,
            "EvidenceCorrelationStage": EvidenceCorrelationStage,
            "KnowledgeGraphStage": KnowledgeGraphStage,
            "TimelineStage": TimelineStage,
            "CaseSimilarityStage": CaseSimilarityStage,
            "DecisionSupportStage": DecisionSupportStage,
            "MultiAgentEngineStage": MultiAgentEngineStage,
            "PredictiveEngineStage": PredictiveEngineStage,
            "ConfidenceEngineStage": ConfidenceEngineStage,
            "ExplainabilityEngineStage": ExplainabilityEngineStage,
            "HallucinationGuardStage": HallucinationGuardStage,
            "MemoryEngineStage": MemoryEngineStage,
            "ResponseGeneratorStage": ResponseGeneratorStage
        }
        
        context.plan = [
            "IntentRouterStage",
            "ConversationEngineStage",
            "ClarificationResolutionStage",
            "ReferenceResolverStage",
            "PronounResolverStage",
            "ClarificationCheckStage",
            "QueryPlannerStage"
        ]
        
        context = EnterpriseOrchestrator.run(context)
            
        # Calculate final confidence
        conf_vals = [v for v in context.confidence.values() if v is not None]
        if conf_vals:
            context.confidence["final"] = min(conf_vals)
        else:
            context.confidence["final"] = 0.50
            
        return context

class IntentRouterStage:
    @staticmethod
    def run(context: ExecutionContext) -> ExecutionContext:
        parsed_query = parse_query(context.raw_query, context.db)
        context.resolved_entities = parsed_query.get("entities", {})
        
        intent_result = IntentRouter.detect(context.raw_query)
        context.intent_result = intent_result
        context.intent = intent_result.intent or "UNKNOWN"
        context.confidence["intent"] = intent_result.confidence
        
        # Intercept conversational/multi-intent cases
        if intent_result.is_multi_intent:
            context.response = ResponseGenerator.build_multi_intent_error(context.start_time)
        elif intent_result.is_conversational:
            context.response = ResponseGenerator.build_conversational(
                intent_result.intent, intent_result.conversational_response, intent_result.confidence, context.start_time
            )
        return context

class ConversationEngineStage:
    @staticmethod
    def run(context: ExecutionContext) -> ExecutionContext:
        q_low = context.raw_query.lower()
        if any(x in q_low for x in ["forget", "reset", "clear", "new chat", "start over"]):
            ConversationEngine.reset(context.conversation_id)
            
        context.conversation_state = ConversationEngine.get_state(context.conversation_id)
        return context

class ClarificationResolutionStage:
    @staticmethod
    def run(context: ExecutionContext) -> ExecutionContext:
        # Check clarification resolution (intercepts query)
        is_resolved, orig_query, orig_intent = ClarificationManager.resolve_clarification(context.raw_query, context.conversation_state)
        if is_resolved:
            context.raw_query = orig_query
            context.intent = orig_intent
            if context.intent_result:
                context.intent_result.intent = orig_intent
        return context

class ReferenceResolverStage:
    @staticmethod
    def run(context: ExecutionContext) -> ExecutionContext:
        # Resolve ordinals/superlatives
        was_ref, resolved_rec, ref_err = ReferenceResolver.resolve(context.raw_query, context.conversation_state)
        if was_ref:
            if ref_err:
                context.response = ResponseGenerator.build_clarification_required(
                    context.intent, context.intent_result.confidence, context.start_time
                )
            elif resolved_rec:
                context.is_followup = True
                if "accused_name" in resolved_rec:
                    context.resolved_entities["accused_name"] = resolved_rec["accused_name"]
                    context.intent = "SEARCH_ACCUSED"
                elif "victim_name" in resolved_rec:
                    context.resolved_entities["victim_name"] = resolved_rec["victim_name"]
                    context.intent = "SEARCH_VICTIMS"
                else:
                    fir_no = resolved_rec.get("crime_no") or resolved_rec.get("fir_no") or resolved_rec.get("case_no")
                    if fir_no:
                        context.resolved_entities["identifiers"] = [fir_no]
                        context.resolved_entities["fir_number"] = fir_no
                        context.intent = "FIR_LOOKUP"
                        # Set active context resolution early response for FIR Lookups!
                        summary = f"Opening FIR {fir_no}."
                        context.response = ResponseGenerator.build_active_context_resolution(
                            "FIR_LOOKUP", summary, context.resolved_entities, resolved_rec, context.intent_result.confidence, context.start_time
                        )
        return context

class PronounResolverStage:
    @staticmethod
    def run(context: ExecutionContext) -> ExecutionContext:
        was_pronoun, resolved_ents, pron_err = PronounResolver.resolve(context.raw_query, context.conversation_state)
        if was_pronoun:
            if pron_err:
                context.response = ResponseGenerator.build_ambiguous_error(
                    pron_err, context.intent_result.confidence, context.start_time
                )
            else:
                context.is_followup = True
                for k, v in resolved_ents.items():
                    if v is not None:
                        context.resolved_entities[k] = v
                        if context.intent in ["UNKNOWN", "GENERAL_CHAT"]:
                            if k == "accused_name":
                                context.intent = "SEARCH_ACCUSED"
                            elif k == "victim_name":
                                context.intent = "SEARCH_VICTIMS"
        return context

class ClarificationCheckStage:
    @staticmethod
    def run(context: ExecutionContext) -> ExecutionContext:
        # Validate intent before update()
        parsed_q = {"intent": context.intent or "UNKNOWN", "entities": context.resolved_entities}
        merged_query = ConversationEngine.update(context.conversation_id, context.raw_query, parsed_q)
        
        merged_intent = merged_query.get("intent", context.intent)
        is_followup_intent = merged_intent != context.intent or merged_query.get("_is_followup", False) or context.is_followup
        context.is_followup = is_followup_intent
        context.intent = merged_intent
        context.resolved_entities = merged_query.get("entities", context.resolved_entities)
        
        # Clear location context for explicit FIR Lookups
        if context.intent == "FIR_LOOKUP" or "ksp-" in context.raw_query.lower():
            preserve_keys = {"identifiers", "fir_number", "limit", "offset", "sort_by", "sort_order"}
            for k in list(context.resolved_entities.keys()):
                if k not in preserve_keys:
                    context.resolved_entities.pop(k, None)
                    
        # Re-run IntentRouter detect with context state overrides
        active_fir = context.conversation_state.active_fir
        active_accused = context.conversation_state.active_accused
        intent_result = IntentRouter.detect(
            context.raw_query,
            is_followup_intent=is_followup_intent,
            has_active_fir=active_fir is not None,
            has_active_accused=active_accused is not None
        )
        context.intent_result = intent_result
        if intent_result.intent != "UNKNOWN":
            context.intent = intent_result.intent
            
        # Detect ambiguity/clarification required
        is_deterministic = "ksp-" in context.raw_query.lower() or intent_result.is_fir_open_query
        
        if not is_deterministic and ClarificationManager.detect_ambiguity(context.raw_query, context.conversation_state, context.intent, is_followup_intent):
            msg = ClarificationManager.store_clarification(context.raw_query, context.intent, context.conversation_state)
            context.response = ResponseGenerator.build_ambiguous_error(
                msg, intent_result.confidence, context.start_time
            )
        elif intent_result.clarification_required:
            context.response = ResponseGenerator.build_clarification_required(
                context.intent, intent_result.confidence, context.start_time
            )
            
        return context

class QueryPlannerStage:
    @staticmethod
    def run(context: ExecutionContext) -> ExecutionContext:
        from app.ai.query_planner import QueryPlanner
        new_stages = QueryPlanner.build_plan(context.intent, context.raw_query, context.resolved_entities)
        context.plan.extend(new_stages)
        return context

class SearchServiceStage:
    @staticmethod
    def run(context: ExecutionContext) -> ExecutionContext:
        from app.services.search_service import SearchService
        
        # Override SEARCH_LOCATION to SEARCH_CASES
        is_loc = context.intent == "SEARCH_LOCATION" or (context.intent_result and context.intent_result.intent == "SEARCH_LOCATION")
        if is_loc and "station" not in context.raw_query.lower() and "address" not in context.raw_query.lower():
            context.intent = "SEARCH_CASES"

        # 1. Invalid district check
        if not context.resolved_entities.get("structured_is_valid_district", True):
            raw_d = context.resolved_entities.get("structured_raw_district")
            suggestions = context.resolved_entities.get("structured_district_suggestions") or ["Mysuru", "Mandya", "Bengaluru Urban"]
            context.response = ResponseGenerator.build_invalid_district(raw_d, suggestions, context.intent, context.resolved_entities, context.intent_result.confidence, context.start_time)
            return context

        # 2. Predictive model OLS
        if context.intent == "PREDICT_CRIME":
            from app.ai.predictor import predict_crime
            merged_q = {"intent": context.intent, "entities": context.resolved_entities, "_raw_query": context.raw_query}
            prediction = predict_crime(context.db, merged_q)
            context.response = ResponseGenerator.build_prediction(prediction, context.intent, context.resolved_entities, context.db, context.intent_result.confidence, context.start_time)
            return context

        # 3. Handle context followups, smart actions, comparisons (BEFORE validation checks)
        early_res = SearchService._handle_context_flow(
            context.raw_query,
            {"intent": context.intent, "entities": context.resolved_entities, "_raw_query": context.raw_query},
            context.intent,
            context.resolved_entities,
            context.intent_result,
            context.is_followup,
            context.conversation_state,
            context.db,
            context.start_time
        )
        if early_res is not None:
            if isinstance(early_res, tuple):
                # Unpack query modification early exit
                context.intent = early_res[2].intent
                context.resolved_entities = early_res[0].get("entities", context.resolved_entities)
            else:
                context.response = early_res
                return context

        # 4. Validation Checks (only for queries that will hit the database search)
        if is_loc and not context.resolved_entities.get("district"):
            context.response = ResponseGenerator.build_clarification_required("SEARCH_LOCATION", context.intent_result.confidence, context.start_time)
            return context
        if context.intent == "SEARCH_ACCUSED" and not context.resolved_entities.get("accused_name") and not context.resolved_entities.get("age") and not context.resolved_entities.get("age_year"):
            context.response = ResponseGenerator.build_clarification_required(context.intent, context.intent_result.confidence, context.start_time)
            return context
        if context.intent == "FIR_LOOKUP" and not context.resolved_entities.get("identifiers"):
            context.response = ResponseGenerator.build_clarification_required(context.intent, context.intent_result.confidence, context.start_time)
            return context

        sql_intent = context.intent
        
        # 5. Generate SQL and Execute query
        if sql_intent != "NETWORK_SEARCH":
            merged_q = {"intent": sql_intent, "entities": context.resolved_entities, "_raw_query": context.raw_query}
            select_stmt = generate_select(merged_q)
            context.select_stmt = select_stmt
            if select_stmt is None:
                context.response = ResponseGenerator.build_sql_error(context.intent, context.resolved_entities, context.intent_result.confidence, context.start_time)
                return context
                
            results = execute_query(context.db, select_stmt)
            SearchService._enrich_results(context.db, results)
            context.search_result = results
            
        return context

class IntelligenceEngineStage:
    @staticmethod
    def run(context: ExecutionContext) -> ExecutionContext:
        intent = context.intent
        confidence = context.intent_result.confidence
        
        bundle = IntelligenceBundle(confidence=confidence)
        context.intelligence_bundle = bundle
        
        if not context.search_result and intent != "NETWORK_SEARCH":
            return context

        # Dynamic execution maps and failure isolation
        
        # 1. HOTSPOT / SEARCH_LOCATION -> Pattern -> Hotspot
        if intent == "HOTSPOT":
            try:
                bundle.hotspots = HotspotEngine.analyze_hotspots(context.search_result)
                bundle.execution_trace.append("Hotspot")
                context.search_result.clear()
                context.search_result.append({"hotspot_data": bundle.hotspots})
            except Exception as e:
                logger.error(f"HotspotEngine failed: {e}")
                context.warnings.append(f"HotspotEngine failed: {e}")
            
        elif intent == "SEARCH_LOCATION":
            # Pattern
            if len(context.search_result) > 1:
                try:
                    bundle.pattern_analysis = CrimePatternAnalyzer.build_pattern_summary(context.search_result)
                    bundle.execution_trace.append("Pattern")
                except Exception as e:
                    logger.error(f"CrimePatternAnalyzer failed: {e}")
                    context.warnings.append(f"CrimePatternAnalyzer failed: {e}")
            # Hotspot
            try:
                bundle.hotspots = HotspotEngine.analyze_hotspots(context.search_result)
                bundle.execution_trace.append("Hotspot")
            except Exception as e:
                logger.error(f"HotspotEngine failed: {e}")
                context.warnings.append(f"HotspotEngine failed: {e}")
            
        # 2. NETWORK_SEARCH -> Network
        elif intent == "NETWORK_SEARCH":
            active_fir = context.conversation_state.active_fir
            if active_fir:
                fir_no = active_fir.get("crime_no") or active_fir.get("fir_no")
                if fir_no:
                    try:
                        bundle.network = NetworkEngine.build_network("FIR", fir_no, context.db)
                        bundle.execution_trace.append("Network")
                        context.search_result.clear()
                        context.search_result.append({"network_data": bundle.network})
                    except Exception as e:
                        logger.error(f"NetworkEngine failed: {e}")
                        context.warnings.append(f"NetworkEngine failed: {e}")
            
        # 3. SEARCH_ACCUSED -> RepeatOffender -> Network -> Recommendation
        elif intent == "SEARCH_ACCUSED":
            # RepeatOffender
            accused_name = None
            try:
                for accused_record in context.search_result:
                    name = accused_record.get("accused_name")
                    if name:
                        accused_name = name
                    off_res = RepeatOffenderEngine.analyze_accused(accused_record.get("accused_name"), context.db)
                    accused_record["officer_summary"] = off_res.get("officer_summary", "")
                    accused_record["linked_firs"] = off_res.get("linked_firs", [])
                bundle.execution_trace.append("RepeatOffender")
                bundle.repeat_offender = {"results": context.search_result}
            except Exception as e:
                logger.error(f"RepeatOffenderEngine failed: {e}")
                context.warnings.append(f"RepeatOffenderEngine failed: {e}")
            
            # Network
            if accused_name:
                try:
                    bundle.network = NetworkEngine.build_network("ACCUSED", accused_name, context.db)
                    bundle.execution_trace.append("Network")
                except Exception as e:
                    logger.error(f"NetworkEngine failed: {e}")
                    context.warnings.append(f"NetworkEngine failed: {e}")
                
            # Recommendation
            try:
                bundle.recommendations = RecommendationEngine.generate_recommendations(context.search_result, context.resolved_entities)
                bundle.execution_trace.append("Recommendation")
            except Exception as e:
                logger.error(f"RecommendationEngine failed: {e}")
                context.warnings.append(f"RecommendationEngine failed: {e}")
            
        # 4. COMPARE_CASES / SIMILAR_CASES -> Similarity -> Pattern
        elif intent == "SEARCH_CASES" and ("similar" in context.raw_query.lower() or context.intent_result.is_similar_search):
            active_fir = context.conversation_state.active_fir
            if active_fir:
                try:
                    scored = SimilarityEngine.find_top_similar(active_fir, context.search_result)
                    new_results = []
                    for c, score, expl in scored:
                        c["_similarity_score"] = score
                        c["_similarity_explanation"] = expl
                        new_results.append(c)
                    context.search_result.clear()
                    context.search_result.extend(new_results)
                    bundle.similar_cases = context.search_result
                    bundle.execution_trace.append("Similarity")
                except Exception as e:
                    logger.error(f"SimilarityEngine failed: {e}")
                    context.warnings.append(f"SimilarityEngine failed: {e}")
                
                # Pattern
                if len(context.search_result) > 1:
                    try:
                        bundle.pattern_analysis = CrimePatternAnalyzer.build_pattern_summary(context.search_result)
                        bundle.execution_trace.append("Pattern")
                    except Exception as e:
                        logger.error(f"CrimePatternAnalyzer failed: {e}")
                        context.warnings.append(f"CrimePatternAnalyzer failed: {e}")

        # 5. Default Case Search / Police Station Search / FIR Lookup
        else:
            # Pattern
            if intent in ["SEARCH_CASES", "SEARCH_POLICE_STATION"] and len(context.search_result) > 1:
                try:
                    bundle.pattern_analysis = CrimePatternAnalyzer.build_pattern_summary(context.search_result)
                    bundle.execution_trace.append("Pattern")
                except Exception as e:
                    logger.error(f"CrimePatternAnalyzer failed: {e}")
                    context.warnings.append(f"CrimePatternAnalyzer failed: {e}")
            # Recommendation
            if intent in ["SEARCH_CASES", "FIR_LOOKUP", "SEARCH_POLICE_STATION"]:
                try:
                    bundle.recommendations = RecommendationEngine.generate_recommendations(context.search_result, context.resolved_entities)
                    bundle.execution_trace.append("Recommendation")
                except Exception as e:
                    logger.error(f"RecommendationEngine failed: {e}")
                    context.warnings.append(f"RecommendationEngine failed: {e}")

        # Set backward compatible _intelligence_report in search_result[0]
        if context.search_result:
            context.search_result[0]["_intelligence_report"] = {
                "pattern_summary": bundle.pattern_analysis,
                "similar_cases": bundle.similar_cases,
                "network_data": bundle.network,
                "hotspot_data": bundle.hotspots,
                "recommendations": bundle.recommendations
            }

        return context

class ReasoningEngineStage:
    @staticmethod
    def run(context: ExecutionContext) -> ExecutionContext:
        try:
            res = ReasoningEngine.evaluate(
                intent=context.intent,
                resolved_entities=context.resolved_entities,
                search_result=context.search_result,
                intelligence_bundle=context.intelligence_bundle,
                raw_query=context.raw_query
            )
            context.reasoning_result = res
            
            # Apply strict confidence adjustments based on reasoning
            adj = res.get("confidence_adjustment", 0.0)
            if adj != 0.0:
                # Add a reasoning confidence metric that will cap/pull down the final confidence
                context.confidence["reasoning"] = max(0.0, min(1.0, 1.0 + adj))

        except Exception as e:
            logger.error(f"ReasoningEngine failed: {e}")
            context.warnings.append(f"ReasoningEngine failed: {e}")
            
        return context

class ConfidenceEngineStage:
    @staticmethod
    def run(context: ExecutionContext) -> ExecutionContext:
        try:
            metrics = ConfidenceEngine.calculate(
                intent=context.intent,
                intent_confidence=context.intent_result.confidence if context.intent_result else 0.50,
                search_result=context.search_result,
                intelligence_bundle_trace=context.intelligence_bundle.execution_trace if context.intelligence_bundle else [],
                reasoning_result=context.reasoning_result or {},
                pipeline_warnings=context.warnings,
                clarification_required=context.intent_result.clarification_required if context.intent_result else False
            )
            context.confidence_metrics = metrics
            
            # Override pipeline unified confidence
            context.confidence["final"] = metrics["confidence"]
        except Exception as e:
            logger.error(f"ConfidenceEngine failed: {e}")
            context.warnings.append(f"ConfidenceEngine failed: {e}")
            
        return context

class ExplainabilityEngineStage:
    @staticmethod
    def run(context: ExecutionContext) -> ExecutionContext:
        try:
            context.explainability = ExplainabilityEngine.generate_explanation(
                intent=context.intent,
                resolved_entities=context.resolved_entities,
                is_followup=context.is_followup,
                select_stmt=context.select_stmt,
                intelligence_bundle_trace=context.intelligence_bundle.execution_trace if context.intelligence_bundle else [],
                reasoning_result=context.reasoning_result or {},
                confidence_metrics=context.confidence_metrics or {}
            )
        except Exception as e:
            logger.error(f"ExplainabilityEngine failed: {e}")
            context.warnings.append(f"ExplainabilityEngine failed: {e}")
        return context

class ResponseGeneratorStage:
    @staticmethod
    def run(context: ExecutionContext) -> ExecutionContext:
        # Calculate final confidence (Fallback if ConfidenceEngine failed/skipped)
        if "final" not in context.confidence:
            conf_vals = [v for v in context.confidence.values() if v is not None]
            if conf_vals:
                context.confidence["final"] = min(conf_vals)
            else:
                context.confidence["final"] = 0.50

        # Persist conversation state update at the end of the pipeline
        new_state = {
            "intent": context.intent or "UNKNOWN",
            "entities": context.resolved_entities,
            "results": context.search_result
        }
        ConversationEngine.update(context.conversation_id, context.raw_query, new_state, is_final_update=True)
        context.conversation_state = ConversationEngine.get_state(context.conversation_id)

        actual_length = len(context.search_result)
        total_count = actual_length # default
        
        # Build explanation metadata — use ExplainabilityEngine output if available
        if context.explainability:
            explanation = context.explainability
        else:
            explanation = {
                "intent": context.intent,
                "entities": {k: v for k, v in context.resolved_entities.items() if v is not None and not k.startswith("structured_") and k != "_dynamic_suggestions"},
                "reasoning": "Executing dynamic intelligence pipeline.",
            }
        
        response = ResponseGenerator.build_final_response(
            context.intent,
            context.search_result,
            context.resolved_entities,
            context.select_stmt,
            total_count,
            context.db,
            context.start_time,
            context.intent_result.confidence,
            intelligence_bundle=context.intelligence_bundle
        )
        
        # Inject reasoning output
        if context.reasoning_result:
            response["reasoning"] = context.reasoning_result
            
            # Override explanations with reasoning conclusion if insufficient
            if context.reasoning_result.get("conclusion") == "Insufficient evidence.":
                explanation["reasoning"] = "Conclusion: Insufficient evidence."
                
        # Inject confidence metrics
        if context.confidence_metrics:
            response["confidence_metrics"] = context.confidence_metrics
            explanation["confidence_explanation"] = context.confidence_metrics.get("explanation", [])
            explanation["confidence"] = context.confidence_metrics["confidence"]
            response["metadata"] = response.get("metadata", {})
            response["metadata"]["confidence"] = context.intent_result.confidence if context.intent_result else 0.50
        else:
            explanation["confidence"] = context.confidence.get("final", 0.50)
            response["metadata"] = response.get("metadata", {})
            response["metadata"]["confidence"] = context.intent_result.confidence if context.intent_result else 0.50
        
        
        # Build the final officer-friendly 8-section layout
        # 1. Executive Summary
        exec_summary = ""
        if context.intent in ["GREETING", "GOODBYE", "THANKS", "HELP", "BOT_IDENTITY", "BOT_CAPABILITIES", "UNKNOWN", "GENERAL_CHAT"]:
            exec_summary = response.get("summary", "No details available.")
        elif not context.search_result:
            exec_summary = "No matching information was found."
        else:
            crime = context.resolved_entities.get("crime_head") or "case"
            district = context.resolved_entities.get("district") or "the jurisdiction"
            crime_str = crime.replace('_', ' ').lower()
            count = len(context.search_result)
            if context.intent == "SEARCH_ACCUSED":
                exec_summary = f"I identified {count} accused profiles matching your criteria."
            elif context.intent == "SEARCH_VICTIMS":
                exec_summary = f"I identified {count} victim records matching your criteria."
            elif context.intent == "FIR_LOOKUP":
                fir_num = context.resolved_entities.get("identifiers", [""])[0] if context.resolved_entities.get("identifiers") else "the requested FIR"
                exec_summary = f"I retrieved the details for FIR {fir_num}."
            elif context.intent == "NETWORK_SEARCH":
                exec_summary = "I have successfully generated the investigation network graph."
            elif context.intent == "HOTSPOT":
                exec_summary = "I have generated the hotspot intelligence report based on the requested area and cases."
            else:
                exec_summary = f"I identified {count} {crime_str} records in {district} matching your request."

        # 2. Key Findings
        key_findings = "None."
        if context.search_result:
            findings_list = []
            for r in context.search_result[:3]:  # Top 3 records
                parts = []
                if r.get("crime_no"):
                    parts.append(f"FIR: {r['crime_no']}")
                if r.get("crime_category"):
                    parts.append(f"Crime: {r['crime_category']}")
                if r.get("district_name"):
                    parts.append(f"District: {r['district_name']}")
                if r.get("status_name"):
                    parts.append(f"Status: {r['status_name']}")
                if r.get("accused_name"):
                    parts.append(f"Accused: {r['accused_name']}")
                if r.get("age_year"):
                    parts.append(f"Age: {r['age_year']}")
                if parts:
                    findings_list.append(" | ".join(parts))
            if findings_list:
                key_findings = "\n".join(f"• {f}" for f in findings_list)
        elif context.intent in ["GREETING", "GOODBYE", "THANKS", "HELP", "BOT_IDENTITY", "BOT_CAPABILITIES", "UNKNOWN", "GENERAL_CHAT"]:
            key_findings = "N/A - General query."

        # 3. Evidence
        evidence = "None."
        if context.search_result:
            tables = []
            if context.intent in ["SEARCH_ACCUSED"]:
                tables.append("accused table")
            else:
                tables.append("case_master table")
            
            filters = []
            for k, v in context.resolved_entities.items():
                if v is not None and not k.startswith("structured_") and k != "_dynamic_suggestions":
                    filters.append(f"{k}={v}")
            
            filter_str = f" filtered by {', '.join(filters)}" if filters else ""
            evidence = f"• Source: database: {', '.join(tables)}{filter_str} ({len(context.search_result)} records)."
            if context.evidence_correlation:
                evidence += f"\n• Correlation Graph:\n{context.evidence_correlation['summary']}"
        elif context.intent in ["GREETING", "GOODBYE", "THANKS", "HELP", "BOT_IDENTITY", "BOT_CAPABILITIES", "UNKNOWN", "GENERAL_CHAT"]:
            evidence = "None - Response based on general/conversational context."

        # 4. Analytics
        analytics = "None - No active crime analysis was triggered."
        if context.intelligence_bundle:
            bundle = context.intelligence_bundle
            analytics_lines = []
            if getattr(bundle, "pattern_analysis", None):
                analytics_lines.append(f"• Crime Pattern: {bundle.pattern_analysis}")
            if getattr(bundle, "hotspots", None) and isinstance(bundle.hotspots, dict):
                h = bundle.hotspots
                rz = ", ".join(h.get("risk_zones", []))
                ph = ", ".join(h.get("peak_hours", []))
                analytics_lines.append(f"• Hotspots: Risk Zones: {rz or 'None'} | Peak Hours: {ph or 'None'}")
            if getattr(bundle, "network", None) and isinstance(bundle.network, dict):
                net = bundle.network
                analytics_lines.append(f"• Network Graph: Risk Score: {net.get('risk_score', 0)}/100 | Edges: {len(net.get('edges', []))}")
            if analytics_lines:
                analytics = "\n".join(analytics_lines)

        # 5. Reasoning
        reasoning = "Conclusions based on matching search entities."
        if context.reasoning_result:
            res = context.reasoning_result
            reasons = res.get("reason_chain") or res.get("evidence_chain") or []
            conclusion = res.get("conclusion", "")
            lines = [f"• {r}" for r in reasons]
            if conclusion:
                lines.append(f"• Conclusion: {conclusion}")
            if lines:
                reasoning = "\n".join(lines)
        elif context.intent in ["GREETING", "GOODBYE", "THANKS", "HELP", "BOT_IDENTITY", "BOT_CAPABILITIES", "UNKNOWN", "GENERAL_CHAT"]:
            reasoning = "General conversation handling."

        # 6. Recommendations
        recommendations = "None."
        if context.intelligence_bundle and getattr(context.intelligence_bundle, "recommendations", None):
            rec_list = context.intelligence_bundle.recommendations
            lines = []
            for r in rec_list:
                lines.append(f"• {r['action']} (Priority: {r['priority']}) - {r['reason']} (Confidence: {r['confidence']})")
            if lines:
                recommendations = "\n".join(lines)

        # 7. Confidence
        conf_score = 0.50
        conf_risk = "HIGH"
        conf_factors = []
        if context.confidence_metrics:
            conf_score = context.confidence_metrics.get("confidence", 0.50)
            conf_risk = context.confidence_metrics.get("risk", "HIGH")
            conf_factors = context.confidence_metrics.get("explanation", [])
        else:
            conf_score = context.confidence.get("final", 0.50)
        
        factor_str = "\n".join(f"  - {f}" for f in conf_factors)
        factor_section = f"\n{factor_str}" if conf_factors else ""
        confidence = f"• Score: {conf_score * 100:.1f}%\n• Risk Level: {conf_risk}{factor_section}"

        # 8. Warnings
        warnings = "None - Safe execution under current bounds."
        if context.warnings:
            warnings = "\n".join(f"• {w}" for w in context.warnings)

        # ── Attach supplementary data to response dict (internal use only) ──
        if context.multi_agent_report:
            response["multi_agent_report"] = context.multi_agent_report
        if context.predictive_report:
            response["predictive_report"] = context.predictive_report
        if context.knowledge_graph_report:
            response["knowledge_graph_report"] = context.knowledge_graph_report
        if context.timeline_report:
            response["timeline_report"] = context.timeline_report
        if context.decision_support_report:
            response["decision_support_report"] = context.decision_support_report
        if context.evidence_correlation:
            response["evidence_correlation"] = context.evidence_correlation

        response["insights"] = [f"Pipeline complete. Confidence: {context.confidence.get('final', 0.0):.2f}"]
        response["explanation"] = explanation

        # ── HallucinationGuard post-build integration ─────────────────────────
        if not getattr(context, "hallucination_safe", True):
            violations = getattr(context, "hallucination_violations", [])
            if violations:
                response = HallucinationGuard.sanitize_response(
                    response,
                    violations,
                    intent=context.intent or "UNKNOWN",
                    evidence_count=len(context.search_result),
                )
        else:
            if getattr(context, "hallucination_safe", True) and \
               "hallucination_guard" not in response:
                response = HallucinationGuard.mark_safe(response)

        # ── Enterprise Response Formatter ─────────────────────────────────────
        # Replace the raw pipeline dump with a clean, officer-friendly report.
        # All engine data is preserved in response dict; only the summary that
        # reaches the officer is reformatted here.
        try:
            officer_summary = ResponseFormatter.format(context, mode="officer")
            response["summary"] = officer_summary
        except Exception as fmt_err:
            # Formatter failure must never crash the pipeline — fall back to safe text.
            logger.error(f"ResponseFormatter failed: {fmt_err}")
            response["summary"] = (
                "Investigation report generated. "
                "Please review the attached records for details."
            )

        context.response = response
        return context
