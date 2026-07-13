with open('/Users/tanaysharma/Desktop/KSP-Sentinel-AI/dataset/app/ai/investigation_brief_builder.py', 'w') as f:
    f.write('''import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from app.ai.decision_support_engine import DecisionSupportStage
from app.ai.investigation_reasoning_engine import Contradiction, InvestigationLimitation, OfficerInsight, InvestigationConclusion

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
class InvestigationProgress:
    current_stage: str = "Initial Enquiry"
    completion_pct: int = 10
    next_stage: str = "Evidence Collection"

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
    priority: str
    reason: str
    supporting_evidence: List[str] = field(default_factory=list)

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
        return "\\n".join(safe).strip()

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
        if not cases:
            return InvestigationProgress("Intake", 0, "FIR Registration")
            
        first = cases[0]
        status = first.status.upper()
        
        if status in ["CLOSED", "CHARGE SHEETED", "CHARGESHEETED"]:
            return InvestigationProgress("Closed / Court Proceedings", 100, "Trial")
        if status in ["ARRESTED", "RECOVERED"]:
            return InvestigationProgress("Suspect Processing", 75, "Filing Charge Sheet")
            
        # Analyze timeline explicitly
        tl = first.timeline
        if tl.chargesheet_date:
            return InvestigationProgress("Closed / Court Proceedings", 100, "Trial")
        if tl.arrest_date:
            return InvestigationProgress("Suspect Processing", 75, "Filing Charge Sheet")
        if tl.incident_from_date:
            return InvestigationProgress("Active Field Investigation", 35, "Witness/Forensic Verification")
            
        # Analyze timeline
        timeline = getattr(context, "timeline_report", None) or {}
        events = timeline.get("event_count", 0)
        
        if events > 5:
            return InvestigationProgress("Advanced Evidence Collection", 60, "Suspect Apprehension")
        elif events > 2:
            return InvestigationProgress("Active Field Investigation", 35, "Witness/Forensic Verification")
        else:
            return InvestigationProgress("Preliminary Enquiry", 15, "Scene Examination / Data Request")

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
        actions: List[RecommendedAction] = []
        ds = getattr(context, "decision_support_report", None)
        
        if ds and isinstance(ds, dict):
            strats = ds.get("strategies", [])
            for s in strats:
                if isinstance(s, dict):
                    title = s.get("title", "")
                    reason = s.get("reason", "Based on investigation protocols.")
                    prio = s.get("priority", "MEDIUM")
                    ev = s.get("supporting_evidence", ["Case assessment"])
                    # NEW: Add confidence explicitly if Decision Support Engine provided it, else default
                    conf = s.get("confidence", 0.75)
                    if title and cls._is_safe(title):
                        actions.append(RecommendedAction(text=title, priority=prio, reason=reason, supporting_evidence=ev))
        # Note: DecisionSupportStage outputs InvestigationStrategy objects, so if ds is the actual report object, 
        # we might need to handle properties vs dictionary get. Let's handle properties.
        elif ds and hasattr(ds, "strategies"):
            for s in ds.strategies:
                # s is InvestigationStrategy
                title = getattr(s, "action", getattr(s, "title", str(s)))
                reason = getattr(s, "reason", "Based on investigation protocols.")
                prio = str(getattr(s, "priority", "MEDIUM")).replace("Priority.", "")
                ev = getattr(s, "supporting_evidence", ["Case assessment"])
                conf = getattr(s, "confidence", 0.75)
                # Map to RecommendedAction but we can add confidence to RecommendedAction!
                if title and cls._is_safe(title):
                    ra = RecommendedAction(text=title, priority=prio, reason=reason, supporting_evidence=ev)
                    # We will monkey-patch confidence onto the action for the formatter
                    ra.confidence = conf
                    actions.append(ra)
                        
        return actions[:5]

    @classmethod
    def _build_confidence(cls, context: Any) -> ConfidenceExplanation:
        cm = getattr(context, "confidence_metrics", None) or {}
        score = cm.get("confidence", 0.5)
        if hasattr(context, "confidence") and isinstance(context.confidence, dict):
            score = context.confidence.get("final", score)
            
        pos = []
        neg = []
        
        cases = getattr(context, "normalized_cases", []) or []
        if cases:
            pos.append(f"Verified against {len(cases)} active database records.")
            first_ev = cases[0].evidence
            if first_ev.has_weapon or first_ev.has_financial_trail:
                pos.append("Physical/Financial evidence verified.")
        
        kg = getattr(context, "knowledge_graph_report", None)
        if kg and isinstance(kg, dict) and kg.get("node_count", 0) > 0:
            pos.append("Cross-entity network links successfully established.")
            
        if cases and not cases[0].timeline.has_gaps:
            pos.append("Temporal reconstruction confirmed logical event sequence.")
        else:
            neg.append("Timeline gaps reduce certainty of event sequence.")
            
        corr = getattr(context, "evidence_correlation", None) or {}
        if not corr:
            neg.append("No independent multi-source corroboration found.")
            
        summary = "Confidence is high due to multi-source verification." if float(score) > 0.7 else "Confidence is moderate due to missing links or timeline gaps."
            
        return ConfidenceExplanation(
            score=float(score),
            positive_factors=pos,
            negative_factors=neg,
            calculation_summary=summary
        )

    @classmethod
    def build(cls, context: Any) -> InvestigationBrief:
        crime_type = cls._get_crime_type(context)
        collected, missing = cls._build_evidence(context)
        findings, risks = cls._build_findings_and_risks(context)
        
        missing_labels = [m.label.lower() for m in missing]
        filtered_findings = []
        for f in findings:
            if not any(m in f.lower() for m in missing_labels):
                filtered_findings.append(f)
                
        reasoning = getattr(context, "investigation_reasoning", None)
        
        correlated_evidence = reasoning.correlated_evidence if reasoning else []
        limitations = reasoning.limitations if reasoning else []
        contradictions = reasoning.contradictions if reasoning else []
        insights = reasoning.officer_insights if reasoning else []
        conclusion = reasoning.investigation_conclusion if reasoning else None

        return InvestigationBrief(
            executive_summary=cls._build_summary(context, crime_type),
            investigation_priority=cls._build_priority(context, crime_type),
            investigation_progress=cls._build_progress(context),
            collected_evidence=collected,
            missing_critical_evidence=missing,
            key_findings=filtered_findings,
            risk_assessment=risks,
            recommendations=cls._build_recommendations(context),
            confidence_explanation=cls._build_confidence(context),
            correlated_evidence=correlated_evidence,
            investigation_limitations=limitations,
            contradictions=contradictions,
            officer_insights=insights,
            investigation_conclusion=conclusion
        )
''')
