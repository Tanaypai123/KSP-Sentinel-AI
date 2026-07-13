import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from app.ai.decision_support_engine import DecisionSupportStage
from app.ai.investigation_reasoning_engine import Contradiction, InvestigationLimitation, OfficerInsight, InvestigationConclusion
from app.ai.report_consistency_validator import ReportConsistencyValidator
from app.ai.confidence_calculator import ConfidenceCalculator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data Models for the Investigation Brief
# ---------------------------------------------------------------------------

@dataclass
class EvidenceItem:
    label: str
    verification_status: str = "Verified"
    strength: str = "Medium"
    source: str = "Case Master"

@dataclass
class InvestigationPriority:
    level: str = "Medium"
    reason: str = "Standard investigation procedures required."

@dataclass
class InvestigationTask:
    task: str
    status: str

@dataclass
class InvestigationProgress:
    tasks: List[InvestigationTask] = field(default_factory=list)
    completion_pct: int = 0

@dataclass
class ConfidenceExplanation:
    score: float = 0.5
    positive_factors: List[str] = field(default_factory=list)
    negative_factors: List[str] = field(default_factory=list)
    calculation_summary: str = "Base confidence without strong corroboration."

@dataclass
class RiskItem:
    level: str
    reason: str
    evidence_used: List[str] = field(default_factory=list)

@dataclass
class RecommendedAction:
    text: str
    evidence: str
    reason: str
    risk: str
    recommendation: str
    expected_impact: str
    priority: str
    confidence: float
    dependencies: List[str]

@dataclass
class InvestigationBrief:
    executive_summary: str = ""
    investigation_priority: Optional[InvestigationPriority] = None
    investigation_progress: Optional[InvestigationProgress] = None
    collected_evidence: List[EvidenceItem] = field(default_factory=list)
    missing_critical_evidence: List[EvidenceItem] = field(default_factory=list)
    key_findings: List[str] = field(default_factory=list)
    risk_assessment: List[RiskItem] = field(default_factory=list)
    recommendations: List[RecommendedAction] = field(default_factory=list)
    confidence_explanation: Optional[ConfidenceExplanation] = None
    
    correlated_evidence: List[str] = field(default_factory=list)
    investigation_limitations: List[InvestigationLimitation] = field(default_factory=list)
    contradictions: List[Contradiction] = field(default_factory=list)
    officer_insights: List[OfficerInsight] = field(default_factory=list)
    investigation_conclusion: Optional[InvestigationConclusion] = None

# ---------------------------------------------------------------------------
# InvestigationBriefBuilder
# ---------------------------------------------------------------------------

class InvestigationBriefBuilder:
    """
    Evaluates raw pipeline data from ExecutionContext to construct a structured,
    explainable, and deduplicated InvestigationBrief.
    """

    _DEV_PATTERNS = [
        "stage skipped", "duplicate execution", "source table", "confidence penalty",
        "pipeline warning", "reasoning adjustment", "sql", "select ", "where ",
        "from ", "filter", "table_name", "database", "stack trace", "traceback",
        "error in stage", "internal id", "structured_", "_dynamic_suggestions",
        "execution_trace", "memory_state", "debug", "penalty",
        "decision support engine", "decision score", "pipeline", "generated strategy",
        "engine", "module", "stage", "execution", "analytics generated", "coverage:"
    ]

    @classmethod
    def _is_safe(cls, text: str) -> bool:
        if not text:
            return True
        lower = text.lower()
        return not any(p in lower for p in cls._DEV_PATTERNS)

    @classmethod
    def _sanitize(cls, text: str) -> str:
        lines = text.splitlines()
        safe = [l for l in lines if cls._is_safe(l)]
        return "\n".join(safe).strip()

    @classmethod
    def _get_crime_type(cls, context: Any) -> str:
        cases = getattr(context, "normalized_cases", []) or []
        for c in cases:
            if hasattr(c, "classification"):
                crime = c.classification.crime_head or c.classification.crime_category
                if crime:
                    return crime.replace("_", " ").title()
        
        entities = getattr(context, "resolved_entities", {}) or {}
        crime = entities.get("crime_head") or ""
        return crime.replace("_", " ").title()

    @classmethod
    def _build_summary(cls, context: Any, crime_type: str) -> str:
        intent = getattr(context, "intent", "") or ""
        cases = getattr(context, "normalized_cases", []) or []

        if not cases:
            return "No verifiable investigation records found matching the criteria."

        count = len(cases)
        c_lower = crime_type.lower()
        
        if intent == "FIR_LOOKUP":
            if "cyber" in c_lower or "fraud" in c_lower:
                return "This is a digital investigation involving financial/data fraud. Tracing operations and digital footprint analysis are ongoing."
            if "vehicle" in c_lower or "theft" in c_lower:
                return "This investigation involves property crime. Tracking movement networks and recovery operations are the current focus."
            if "murder" in c_lower or "homicide" in c_lower:
                return "This is a violent crime investigation (Homicide). High-priority forensic and timeline reconstruction is in progress."
            return f"Investigation record retrieved for {crime_type or 'the reported incident'}."
        
        if "cyber" in c_lower or "fraud" in c_lower:
            return f"{count} cybercrime/fraud cases identified. Patterns indicate structured digital exploitation."
        if "vehicle" in c_lower or "theft" in c_lower:
            return f"{count} property crime records identified. Cross-jurisdictional movement tracking is recommended."
        if "murder" in c_lower or "homicide" in c_lower:
            return f"{count} violent crime records retrieved. High-priority focus is required."
            
        return f"{count} records identified matching the investigation profile for {crime_type or 'the requested category'}."

    @classmethod
    def _build_progress(cls, context: Any) -> InvestigationProgress:
        cases = getattr(context, "normalized_cases", []) or []
        tasks = []
        
        has_weapon = False
        has_witness = False
        has_phone = False
        has_financial = False
        
        for c in cases:
            if hasattr(c, "evidence"):
                if c.evidence.has_weapon: has_weapon = True
                if c.evidence.has_witness: has_witness = True
                if c.evidence.has_phone: has_phone = True
                if c.evidence.has_financial_trail: has_financial = True
                
        tasks.append(InvestigationTask("Crime Scene", "Completed"))
        tasks.append(InvestigationTask("Weapon Recovery", "Completed" if has_weapon else "Pending"))
        tasks.append(InvestigationTask("Witness Interview", "Completed" if has_witness else "Pending"))
        tasks.append(InvestigationTask("CDR", "Completed" if has_phone else "Pending"))
        tasks.append(InvestigationTask("Forensics", "Completed" if has_weapon or has_phone or has_financial else "Pending"))
        
        if not cases:
            tasks.append(InvestigationTask("Chargesheet", "Pending"))
            tasks.append(InvestigationTask("Arrest", "Pending"))
        else:
            status = cases[0].status.upper()
            tasks.append(InvestigationTask("Chargesheet", "Completed" if status in ["CLOSED", "CHARGE SHEETED", "CHARGESHEETED"] else "Pending"))
            tasks.append(InvestigationTask("Arrest", "Completed" if status in ["ARRESTED", "RECOVERED", "CLOSED", "CHARGE SHEETED", "CHARGESHEETED"] else "Pending"))
            
        completed = sum(1 for t in tasks if t.status == "Completed")
        pct = int((completed / len(tasks)) * 100) if tasks else 0
        
        return InvestigationProgress(tasks=tasks, completion_pct=pct)

    @classmethod
    def _build_evidence(cls, context: Any) -> tuple[List[EvidenceItem], List[EvidenceItem]]:
        collected: List[EvidenceItem] = []
        missing: List[EvidenceItem] = []
        
        cases = getattr(context, "normalized_cases", []) or []
        if not cases:
            return collected, missing
            
        first = cases[0]
        ev = first.evidence
        
        has_weapon = ev.has_weapon
        has_vehicle = ev.has_vehicle
        has_witness = ev.has_witness
        has_phone = ev.has_phone
        has_financial = ev.has_financial_trail
        
        if has_weapon:
            collected.append(EvidenceItem("Weapon Recovered", "Verified", "High", "Forensic Lab / Seizure Memo"))
        if has_vehicle:
            collected.append(EvidenceItem("Vehicle Identified", "Verified", "High", "RTO / CCTV Database"))
        if has_witness:
            collected.append(EvidenceItem("Witness Statements", "Pending Verification", "Medium", "Field Officer Report"))
        if has_phone:
            collected.append(EvidenceItem("Mobile Number / CDR", "Verified", "High", "Telecom Operator"))
        if has_financial:
            collected.append(EvidenceItem("Financial Trail", "Verified", "High", "Bank Records"))
            
        # Add basic FIR data
        collected.append(EvidenceItem("FIR Report", "Verified", "High", "Case Master"))

        crime_type = cls._get_crime_type(context).lower()
        
        # Determine missing critical based on crime type
        if "murder" in crime_type or "homicide" in crime_type:
            if not has_weapon: missing.append(EvidenceItem("Murder Weapon", "Missing", "High", "Crime Scene"))
            if not has_witness: missing.append(EvidenceItem("Eyewitness", "Missing", "High", "Neighborhood Canvas"))
        elif "vehicle" in crime_type or "theft" in crime_type:
            if not has_vehicle: missing.append(EvidenceItem("Stolen Vehicle Trace", "Missing", "High", "ANPR / Toll Data"))
            missing.append(EvidenceItem("CCTV Footage", "Missing", "Medium", "Incident Area Cameras"))
        elif "cyber" in crime_type or "fraud" in crime_type:
            if not has_phone: missing.append(EvidenceItem("Suspect IP / Phone", "Missing", "High", "Service Provider Logs"))
            missing.append(EvidenceItem("Bank Transaction Trail", "Missing", "High", "Financial Institution"))
        
        return collected, missing

    @classmethod
    def _build_priority(cls, context: Any, crime_type: str) -> InvestigationPriority:
        cases = getattr(context, "normalized_cases", []) or []
        pred = getattr(context, "predictive_report", None) or {}
        repeat_risks = pred.get("repeat_offender_risks", []) if pred else []
        
        c_lower = crime_type.lower()
        
        if repeat_risks:
            return InvestigationPriority("IMMEDIATE", "Known repeat offenders identified. Immediate apprehension required to prevent further offenses.")
        
        if "murder" in c_lower or "homicide" in c_lower:
            return InvestigationPriority("IMMEDIATE", "Violent crime with severe threat to public safety. Requires dedicated task force.")
            
        if "cyber" in c_lower or "fraud" in c_lower:
            if getattr(context, "knowledge_graph_report", {}).get("node_count", 0) > 10:
                return InvestigationPriority("HIGH", "Complex organizational network detected. Evidence decay risk is high for digital footprints.")
            return InvestigationPriority("MEDIUM", "Financial fraud. Requires timely requests to banking and telecom nodal officers.")
            
        if "vehicle" in c_lower or "theft" in c_lower:
            return InvestigationPriority("MEDIUM", "Property crime. Rapid dissemination of vehicle details to neighboring borders is needed.")
            
        return InvestigationPriority("MEDIUM", "Standard investigation. Follow routine evidence collection procedures.")

    @classmethod
    def _build_findings_and_risks(cls, context: Any) -> tuple[List[str], List[RiskItem]]:
        findings: List[str] = []
        risks: List[RiskItem] = []
        
        # Risk analysis from Decision Support
        ds = getattr(context, "decision_support_report", None)
        if ds and isinstance(ds, dict):
            ra = ds.get("risk_assessment", {})
            level = ra.get("overall_risk_level", "MEDIUM")
            open_risks = ra.get("open_risks", [])
            
            # Map risks into RiskItem with evidence
            for r in open_risks:
                safe_r = cls._sanitize(r)
                if not safe_r: continue
                # Infer evidence used
                ev = ["Case Master Data"]
                if "weapon" in safe_r.lower(): ev.append("Forensic / Seizure Logs")
                if "timeline" in safe_r.lower(): ev.append("Timeline Analysis")
                if "network" in safe_r.lower() or "cross-fir" in safe_r.lower(): ev.append("Knowledge Graph Engine")
                
                risks.append(RiskItem(level=level, reason=safe_r, evidence_used=ev))

        # Findings
        bundle = getattr(context, "intelligence_bundle", None)
        if bundle:
            pattern = getattr(bundle, "pattern_analysis", None)
            if pattern and cls._is_safe(str(pattern)):
                findings.append(cls._sanitize(str(pattern)))

        results = getattr(context, "search_result", []) or []
        if len(results) > 1:
            findings.append(f"Linked Records: {len(results)} verified records suggest a pattern.")
            
        kg = getattr(context, "knowledge_graph_report", None)
        if kg and isinstance(kg, dict):
            kg_sum = kg.get("summary", "")
            if kg_sum and cls._is_safe(kg_sum):
                clean_kg = cls._sanitize(kg_sum)
                if "knowledge graph" in clean_kg.lower():
                    clean_kg = clean_kg.replace("build knowledge graph", "establish network links")
                findings.append(clean_kg)

        return findings[:3], risks[:3]

    @classmethod
    def _build_recommendations(cls, context: Any) -> List[RecommendedAction]:
        recs = []
        ds = getattr(context, "decision_support", {})
        strats = []
        if isinstance(ds, dict):
            strats = ds.get("strategies", [])
        elif hasattr(ds, "strategies"):
            strats = ds.strategies
            
        for s in strats:
            if isinstance(s, dict):
                recs.append(RecommendedAction(
                    text=s.get("title", ""),
                    evidence=s.get("evidence", ""),
                    reason=s.get("reasoning", ""),
                    risk=s.get("risk", ""),
                    recommendation=s.get("recommendation", ""),
                    expected_impact=s.get("expected_impact", ""),
                    priority=s.get("priority", "MEDIUM"),
                    confidence=s.get("confidence", 0.75),
                    dependencies=s.get("dependencies", [])
                ))
            else:
                recs.append(RecommendedAction(
                    text=getattr(s, "title", "Action"),
                    evidence=getattr(s, "evidence", ""),
                    reason=getattr(s, "reasoning", ""),
                    risk=getattr(s, "risk", ""),
                    recommendation=getattr(s, "recommendation", ""),
                    expected_impact=getattr(s, "expected_impact", ""),
                    priority=str(getattr(s, "priority", "MEDIUM")),
                    confidence=getattr(s, "confidence", 0.75),
                    dependencies=getattr(s, "dependencies", [])
                ))
        return recs

    @classmethod
    def build(cls, context: Any) -> InvestigationBrief:
        brief = InvestigationBrief()
        try:
            cases = getattr(context, "normalized_cases", []) or []
            crime_type = cls._get_crime_type(context)
            
            brief.executive_summary = cls._build_summary(context, crime_type)
            brief.investigation_priority = cls._build_priority(context, crime_type)
            brief.investigation_progress = cls._build_progress(context)
            
            collected, missing = cls._build_evidence(context)
            brief.collected_evidence = collected
            brief.missing_critical_evidence = missing
            
            findings, risks = cls._build_findings_and_risks(context)
            missing_labels = [m.label.lower() for m in missing]
            filtered_findings = []
            for f in findings:
                if not any(m in f.lower() for m in missing_labels):
                    filtered_findings.append(f)
            brief.key_findings = filtered_findings
            brief.risk_assessment = risks
            brief.recommendations = cls._build_recommendations(context)
            
            # Use new ConfidenceCalculator
            conf_score = ConfidenceCalculator.calculate(context)
            brief.confidence_explanation = ConfidenceExplanation(
                score=conf_score.final_score,
                positive_factors=conf_score.positive_factors,
                negative_factors=conf_score.negative_factors,
                calculation_summary=conf_score.calculation_formula
            )
            
            # Map Reasoning Engine Outputs
            reasoning = getattr(context, "investigation_reasoning", None)
            if reasoning:
                brief.correlated_evidence = reasoning.correlated_evidence
                brief.investigation_limitations = reasoning.limitations
                brief.contradictions = reasoning.contradictions
                brief.officer_insights = reasoning.officer_insights
                brief.investigation_conclusion = reasoning.investigation_conclusion
                
            # Global Validation Layer
            brief = ReportConsistencyValidator.validate(brief, context)
                
        except Exception as e:
            logger.error(f"InvestigationBriefBuilder failed: {e}")
            import traceback
            traceback.print_exc()
        return brief
