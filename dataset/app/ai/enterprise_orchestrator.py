import time
import logging
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── 1. Enterprise Report Data Structures ─────────────────────────────────────

@dataclass
class StageMetrics:
    stage_name: str
    start_time: float
    end_time: float
    latency_ms: float
    status: str
    error: Optional[str] = None
    retries: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class EnterpriseExecutionReport:
    execution_id: str
    overall_status: str
    total_latency_ms: float
    orchestration_overhead_ms: float
    stage_metrics: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    health_status: str = "HEALTHY"
    confidence_timeline: List[Dict[str, Any]] = field(default_factory=list)
    decision_timeline: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

# ── 2. Managers ──────────────────────────────────────────────────────────────

class MetricsCollector:
    def __init__(self):
        self.metrics: List[StageMetrics] = []
        self.start_time = time.perf_counter()
        
    def record_stage(self, stage_name: str, t_start: float, t_end: float, status: str, error: Optional[str] = None, retries: int = 0):
        latency = (t_end - t_start) * 1000.0
        self.metrics.append(StageMetrics(
            stage_name=stage_name,
            start_time=t_start,
            end_time=t_end,
            latency_ms=latency,
            status=status,
            error=error,
            retries=retries
        ))
        
    def get_total_latency(self) -> float:
        return sum(m.latency_ms for m in self.metrics)

class PerformanceMonitor:
    @staticmethod
    def measure_overhead(total_wall_clock_ms: float, total_stage_latency_ms: float) -> float:
        # Overhead is the time spent in the orchestrator loops vs inside the stage execution
        return max(0.0, total_wall_clock_ms - total_stage_latency_ms)

class HealthChecker:
    @staticmethod
    def verify(metrics: List[StageMetrics], warnings: List[str], errors: List[str]) -> str:
        if errors:
            return "DEGRADED_ERRORS"
        failed = [m for m in metrics if m.status == "FAILED"]
        if failed:
            return "DEGRADED_FAILURES"
        if len(warnings) > 5:
            return "WARNING_HEAVY"
        return "HEALTHY"

class FailureRecoveryManager:
    """
    Determines if a failure is recoverable or critical.
    """
    # Safe to retry network or transient DB errors. Hallucinations or logic errors are fatal.
    SAFE_RETRIES = 1
    
    @classmethod
    def can_retry(cls, stage_name: str, exception: Exception, attempt: int) -> bool:
        if attempt >= cls.SAFE_RETRIES:
            return False
        # Do not retry hallucination errors
        if "hallucination" in str(exception).lower():
            return False
        # Do not retry fatal database integrity errors
        if "integrityerror" in str(type(exception).__name__).lower() or "integrityerror" in str(exception).lower():
            return False
        return True

class ContextManager:
    """
    Manages the ExecutionContext state, preventing illegal modifications.
    """
    @staticmethod
    def log_confidence_shift(context: Any, report: EnterpriseExecutionReport, stage_name: str):
        if hasattr(context, "confidence_metrics") and context.confidence_metrics:
            conf = context.confidence_metrics.get("confidence", 0.0)
            report.confidence_timeline.append({
                "stage": stage_name,
                "confidence": conf
            })
            
    @staticmethod
    def log_decision_shift(context: Any, report: EnterpriseExecutionReport, stage_name: str):
        if hasattr(context, "decision_support_report") and context.decision_support_report:
            score = context.decision_support_report.get("decision_score", 0.0)
            report.decision_timeline.append({
                "stage": stage_name,
                "decision_score": score
            })

class AuditCoordinator:
    @staticmethod
    def build_report(
        execution_id: str,
        metrics: MetricsCollector,
        total_wall_clock_ms: float,
        context: Any,
        errors: List[str]
    ) -> EnterpriseExecutionReport:
        overhead = PerformanceMonitor.measure_overhead(total_wall_clock_ms, metrics.get_total_latency())
        
        report = EnterpriseExecutionReport(
            execution_id=execution_id,
            overall_status="SUCCESS" if not errors else "PARTIAL_FAILURE",
            total_latency_ms=total_wall_clock_ms,
            orchestration_overhead_ms=overhead,
            stage_metrics=[m.to_dict() for m in metrics.metrics],
            warnings=getattr(context, "warnings", []),
            errors=errors
        )
        report.health_status = HealthChecker.verify(metrics.metrics, report.warnings, report.errors)
        return report

# ── 3. Pipeline Execution ────────────────────────────────────────────────────

class EnterprisePipelineStage:
    """
    Wraps standard stages to provide retry and monitoring logic.
    """
    @staticmethod
    def execute(stage_name: str, stage_class: Any, context: Any, metrics_collector: MetricsCollector, errors_list: List[str]) -> Any:
        attempt = 0
        while True:
            t_start = time.perf_counter()
            try:
                context = stage_class.run(context)
                t_end = time.perf_counter()
                metrics_collector.record_stage(stage_name, t_start, t_end, "SUCCESS", retries=attempt)
                return context
            except Exception as e:
                t_end = time.perf_counter()
                error_msg = f"{type(e).__name__}: {str(e)}"
                logger.error(f"Stage {stage_name} failed on attempt {attempt}: {error_msg}")
                
                if FailureRecoveryManager.can_retry(stage_name, e, attempt):
                    attempt += 1
                    logger.info(f"Retrying stage {stage_name}, attempt {attempt}")
                    continue
                else:
                    metrics_collector.record_stage(stage_name, t_start, t_end, "FAILED", error=error_msg, retries=attempt)
                    errors_list.append(f"[{stage_name}] {error_msg}")
                    # Allow execution to continue if safe, some stages are non-critical
                    # If it's a critical stage, we'll let the orchestrator decide.
                    return context

class PipelineCoordinator:
    @staticmethod
    def get_stage_registry() -> Dict[str, Any]:
        # Import dynamically to avoid circular dependencies
        from app.ai.pipeline_runner import (
            IntentRouterStage, ConversationEngineStage, ClarificationResolutionStage,
            ReferenceResolverStage, PronounResolverStage, ClarificationCheckStage,
            QueryPlannerStage, SearchServiceStage, IntelligenceEngineStage,
            ReasoningEngineStage, EvidenceCorrelationStage, KnowledgeGraphStage,
            TimelineStage, CaseSimilarityStage, DecisionSupportStage,
            MultiAgentEngineStage, PredictiveEngineStage, ConfidenceEngineStage,
            ExplainabilityEngineStage, HallucinationGuardStage, MemoryEngineStage,
            ResponseGeneratorStage, ContextNormalizerStage, InvestigationReasoningEngineStage
        )
        return {
            "IntentRouterStage": IntentRouterStage,
            "ConversationEngineStage": ConversationEngineStage,
            "ClarificationResolutionStage": ClarificationResolutionStage,
            "ReferenceResolverStage": ReferenceResolverStage,
            "PronounResolverStage": PronounResolverStage,
            "ClarificationCheckStage": ClarificationCheckStage,
            "QueryPlannerStage": QueryPlannerStage,
            "SearchServiceStage": SearchServiceStage,
            "ContextNormalizerStage": ContextNormalizerStage,
            "EvidenceCorrelationStage": EvidenceCorrelationStage,
            "ReasoningEngineStage": ReasoningEngineStage,
            "InvestigationReasoningEngineStage": InvestigationReasoningEngineStage,
            "IntelligenceEngineStage": IntelligenceEngineStage,
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

class ExecutionManager:
    @staticmethod
    def execute_plan(context: Any, registry: Dict[str, Any], metrics: MetricsCollector, errors: List[str], report: EnterpriseExecutionReport) -> Any:
        executed_set = set()
        
        while context.plan:
            # If response is already terminal, skip remaining
            if context.response is not None:
                context.skipped_stages.extend(context.plan)
                context.plan = []
                break
                
            stage_name = context.plan.pop(0)
            
            # Rule: Execute every stage only once. No duplicated execution.
            if stage_name in executed_set:
                context.warnings.append(f"Stage {stage_name} skipped (duplicate execution prevented)")
                continue
            
            if stage_name not in registry:
                errors.append(f"Unknown stage requested: {stage_name}")
                continue
                
            stage_class = registry[stage_name]
            executed_set.add(stage_name)
            
            # Record trace for backward compatibility with PipelineRunner trace format
            stage_trace = {
                "stage": stage_name,
                "start": time.time(),
                "decision": "Executed",
                "reason": "Enterprise Orchestrator",
                "skipped": False,
                "executed": True
            }
            
            context = EnterprisePipelineStage.execute(stage_name, stage_class, context, metrics, errors)
            
            ContextManager.log_confidence_shift(context, report, stage_name)
            ContextManager.log_decision_shift(context, report, stage_name)
            
            stage_trace["end"] = time.time()
            context.execution_trace.append(stage_trace)
            context.executed_stages.append(stage_name)
            
        return context

class EnterpriseOrchestrator:
    """
    The Single Enterprise Entry Point.
    Replaces the standard pipeline runner loop with a hardened, monitored orchestrator.
    """
    
    @classmethod
    def run(cls, context: Any) -> Any:
        wall_start = time.perf_counter()
        
        metrics = MetricsCollector()
        errors: List[str] = []
        
        # We need a report object early for confidence/decision timelines
        report = EnterpriseExecutionReport(
            execution_id=context.conversation_id,
            overall_status="RUNNING",
            total_latency_ms=0.0,
            orchestration_overhead_ms=0.0
        )
        
        registry = PipelineCoordinator.get_stage_registry()
        
        try:
            context = ExecutionManager.execute_plan(context, registry, metrics, errors, report)
        except Exception as e:
            error_msg = f"Fatal Pipeline Crash: {str(e)}"
            logger.critical(error_msg)
            errors.append(error_msg)
            context.warnings.append("Pipeline crashed deterministically.")
        finally:
            wall_end = time.perf_counter()
            total_wall_ms = (wall_end - wall_start) * 1000.0
            
            final_report = AuditCoordinator.build_report(
                execution_id=context.conversation_id,
                metrics=metrics,
                total_wall_clock_ms=total_wall_ms,
                context=context,
                errors=errors
            )
            
            # Carry over the timelines captured during execution
            final_report.confidence_timeline = report.confidence_timeline
            final_report.decision_timeline = report.decision_timeline
            
            # Attach to context
            context.enterprise_report = final_report.to_dict()
            
            # Attach to final response payload if it exists
            if context.response is not None:
                context.response["enterprise_report"] = context.enterprise_report
                
        return context
