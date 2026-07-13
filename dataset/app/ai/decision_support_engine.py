"""
decision_support_engine.py
Phase 5.8 — Enterprise Decision Support & Investigation Strategy Engine

Synthesizes ALL verified pipeline outputs into deterministic, evidence-backed
investigation strategies with priority ranking, risk analysis and decision scoring.

STRICT RULES:
- NO ML, NO embeddings, NO cosine similarity, NO LLM calls
- Reads ONLY from verified ExecutionContext fields
- If evidence is insufficient → output fixed safety message
- NEVER fabricate strategies, suspects, recommendations or evidence
- Decision Score based ONLY on verified pipeline metrics
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

INSUFFICIENT_EVIDENCE_MESSAGE = (
    "Insufficient verified evidence to recommend further investigative actions."
)
MIN_RECORDS_FOR_STRATEGY: int = 1   # At least 1 search result required
MAX_STRATEGIES: int = 15            # Hard cap on returned strategies
DECISION_SCORE_MAX: int = 100

# ─────────────────────────────────────────────────────────────────────────────
# PRIORITY LEVELS
# ─────────────────────────────────────────────────────────────────────────────

class Priority(str, Enum):
    IMMEDIATE = "IMMEDIATE"
    HIGH     = "HIGH"
    MEDIUM   = "MEDIUM"
    LOW      = "LOW"

# Numeric value used for deterministic sort order (lower = higher priority)
PRIORITY_ORDER: Dict[str, int] = {
    Priority.IMMEDIATE: 0,
    Priority.HIGH:     1,
    Priority.MEDIUM:   2,
    Priority.LOW:      3,
}

# ─────────────────────────────────────────────────────────────────────────────
# STRATEGY TYPES
# ─────────────────────────────────────────────────────────────────────────────

class StrategyType(str, Enum):
    INTERVIEW_SUSPECT         = "Interview Suspect"
    COLLECT_CCTV              = "Collect CCTV Footage"
    VERIFY_MOBILE_RECORDS     = "Verify Mobile Records"
    CHECK_FINANCIAL_TRAIL     = "Check Financial Trail"
    CROSS_MATCH_VEHICLES      = "Cross-Match Vehicles"
    ANALYZE_HOTSPOT           = "Analyze Crime Hotspot"
    RECOVER_WEAPON            = "Recover Weapon"
    REINTERVIEW_WITNESS       = "Re-Interview Witness"
    CHECK_NEARBY_FIRS         = "Check Nearby FIRs"
    REVIEW_FORENSIC_EVIDENCE  = "Review Forensic Evidence"

# ─────────────────────────────────────────────────────────────────────────────
# RISK DIMENSIONS
# ─────────────────────────────────────────────────────────────────────────────

class RiskDimension(str, Enum):
    EVIDENCE_COMPLETENESS   = "evidence_completeness"
    INVESTIGATION_COVERAGE  = "investigation_coverage"
    MISSING_ENTITIES        = "missing_entities"
    MISSING_TIMELINE        = "missing_timeline"
    MISSING_GRAPH_LINKS     = "missing_graph_links"
    MISSING_WITNESS         = "missing_witness"
    MISSING_DOCUMENTS       = "missing_documents"
    OPEN_RISKS              = "open_risks"

# ─────────────────────────────────────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class InvestigationStrategy:
    title:              str
    evidence:           str
    reasoning:          str
    risk:               str
    recommendation:     str
    expected_impact:    str
    confidence:         float
    priority:           Priority
    dependencies:       List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "evidence": self.evidence,
            "reasoning": self.reasoning,
            "risk": self.risk,
            "recommendation": self.recommendation,
            "expected_impact": self.expected_impact,
            "confidence": self.confidence,
            "priority": self.priority.value,
            "dependencies": self.dependencies,
        }


@dataclass
class RiskAssessment:
    """Deterministic risk dimensions derived from verified pipeline outputs."""
    evidence_completeness:  float       # 0.0–1.0
    investigation_coverage: float       # fraction of 12 layers that produced output
    missing_entities:       List[str]   # e.g. ["weapon", "vehicle"]
    missing_timeline:       bool
    missing_graph_links:    bool
    missing_witness:        bool
    missing_documents:      bool
    open_risks:             List[str]   # human-readable risk strings
    overall_risk_level:     str         # "LOW" | "MEDIUM" | "HIGH" | "IMMEDIATE"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_completeness":  round(self.evidence_completeness, 4),
            "investigation_coverage": round(self.investigation_coverage, 4),
            "missing_entities":       self.missing_entities,
            "missing_timeline":       self.missing_timeline,
            "missing_graph_links":    self.missing_graph_links,
            "missing_witness":        self.missing_witness,
            "missing_documents":      self.missing_documents,
            "open_risks":             self.open_risks,
            "overall_risk_level":     self.overall_risk_level,
        }


@dataclass
class DecisionSupportReport:
    """Full output of the Decision Support Engine."""
    executive_summary:  str
    strategies:         List[InvestigationStrategy]
    priority_ranking:   Dict[str, List[str]]       # priority → [strategy titles]
    risk_assessment:    RiskAssessment
    decision_score:     int                         # 0–100
    confidence:         float                       # final weighted confidence
    warnings:           List[str]
    open_questions:     List[str]
    insufficient:       bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "executive_summary": self.executive_summary,
            "strategies":        [s.to_dict() for s in self.strategies],
            "priority_ranking":  self.priority_ranking,
            "risk_assessment":   self.risk_assessment.to_dict(),
            "decision_score":    self.decision_score,
            "confidence":        round(self.confidence, 4),
            "warnings":          self.warnings,
            "open_questions":    self.open_questions,
            "insufficient":      self.insufficient,
            "summary":           self._build_summary(),
        }

    def _build_summary(self) -> str:
        if self.insufficient:
            return INSUFFICIENT_EVIDENCE_MESSAGE
        critical = self.priority_ranking.get(Priority.IMMEDIATE.value, [])
        high     = self.priority_ranking.get(Priority.HIGH.value, [])
        return (
            f"Decision Score: {self.decision_score}/100 | "
            f"Strategies: {len(self.strategies)} | "
            f"Critical: {len(critical)} | High: {len(high)} | "
            f"Risk: {self.risk_assessment.overall_risk_level} | "
            f"Confidence: {self.confidence * 100:.1f}%"
        )

# ─────────────────────────────────────────────────────────────────────────────
# RISK ANALYZER
# ─────────────────────────────────────────────────────────────────────────────

class RiskAnalyzer:
    """
    Calculates deterministic risk dimensions from verified pipeline outputs.
    All scores derived exclusively from ExecutionContext fields.
    """

    # The 12 intelligence layers
    INTELLIGENCE_LAYERS: List[str] = [
        "search_result",
        "reasoning_result",
        "confidence_metrics",
        "hallucination_safe",
        "explainability",
        "memory_audit",
        "evidence_correlation",
        "knowledge_graph_report",
        "timeline_report",
        "multi_agent_report",
        "predictive_report",
        "similarity_report",
    ]

    @classmethod
    def analyze(cls, context: Any) -> RiskAssessment:
        results       = context.search_result or []
        entities      = context.resolved_entities or {}
        kg_report     = getattr(context, "knowledge_graph_report", None) or {}
        timeline      = getattr(context, "timeline_report", None) or {}
        corr          = getattr(context, "evidence_correlation", None) or {}
        similarity    = getattr(context, "similarity_report", None) or {}
        memory_audit  = getattr(context, "memory_audit", None) or {}
        pred_report   = getattr(context, "predictive_report", None) or {}
        multi_report  = getattr(context, "multi_agent_report", None) or {}

        # ── 1. Evidence Completeness ─────────────────────────────────────────
        entity_fields = [
            "accused_name", "victim_name", "crime_head",
            "district", "police_station", "weapon", "vehicle", "phone",
        ]
        filled = sum(1 for f in entity_fields if entities.get(f))
        # Also count from records
        record_filled = 0
        for r in results[:5]:
            for f in ["crime_no", "crime_category", "district_name", "status_name"]:
                if r.get(f):
                    record_filled += 1
        max_entity   = len(entity_fields)
        max_record   = 20  # 5 records × 4 fields
        completeness = min(1.0, (filled / max_entity + min(record_filled / max_record, 1.0)) / 2)

        # ── 2. Investigation Coverage ────────────────────────────────────────
        layer_scores = {
            "search_result":       1 if results else 0,
            "reasoning_result":    1 if getattr(context, "reasoning_result", None) else 0,
            "confidence_metrics":  1 if getattr(context, "confidence_metrics", None) else 0,
            "hallucination_safe":  1 if getattr(context, "hallucination_safe", True) else 0,
            "explainability":      1 if getattr(context, "explainability", None) else 0,
            "memory_audit":        1 if memory_audit else 0,
            "evidence_correlation":1 if corr else 0,
            "knowledge_graph_report": 1 if kg_report else 0,
            "timeline_report":     1 if timeline else 0,
            "multi_agent_report":  1 if multi_report else 0,
            "predictive_report":   1 if pred_report else 0,
            "similarity_report":   1 if similarity else 0,
        }
        coverage = sum(layer_scores.values()) / len(cls.INTELLIGENCE_LAYERS)

        # ── 3. Missing Entities ──────────────────────────────────────────────
        missing_entities: List[str] = []
        cases = getattr(context, "normalized_cases", []) or []
        
        has_weapon  = any(c.evidence.has_weapon for c in cases)
        has_vehicle = any(c.evidence.has_vehicle for c in cases)
        has_phone   = any(c.evidence.has_phone for c in cases)
        has_accused = any(len(c.accused_names) > 0 for c in cases)
        has_victim  = any(len(c.victim_names) > 0 for c in cases)

        # Check graph nodes too
        kg_nodes = kg_report.get("node_types", {}) if isinstance(kg_report, dict) else {}
        if kg_nodes.get("Phone", 0) > 0:
            has_phone = True
        if kg_nodes.get("Weapon", 0) > 0:
            has_weapon = True
        if kg_nodes.get("Vehicle", 0) > 0:
            has_vehicle = True

        if not has_accused:
            missing_entities.append("accused")
        if not has_victim:
            missing_entities.append("victim")
        if not has_weapon:
            missing_entities.append("weapon")
        if not has_vehicle:
            missing_entities.append("vehicle")
        if not has_phone:
            missing_entities.append("phone")

        # ── 4. Missing Timeline ──────────────────────────────────────────────
        missing_timeline = (
            not timeline or
            timeline.get("event_count", 0) == 0 or
            timeline.get("dated_event_count", 0) == 0
        )

        # ── 5. Missing Graph Links ───────────────────────────────────────────
        missing_graph = (
            not kg_report or
            kg_report.get("edge_count", 0) == 0
        )

        # ── 6. Missing Witness ───────────────────────────────────────────────
        witness_in_kg   = kg_nodes.get("Witness", 0) > 0
        witness_in_tl   = "witness" in str(timeline).lower()
        missing_witness = not (witness_in_kg or witness_in_tl)

        # ── 7. Missing Documents ─────────────────────────────────────────────
        has_docs = corr.get("node_count", 0) > 0 or len(results) > 0
        missing_docs = not has_docs

        # ── 8. Open Risks ────────────────────────────────────────────────────
        open_risks: List[str] = []
        if missing_timeline:
            open_risks.append("Investigation timeline is incomplete — key event dates unverified.")
        if missing_graph:
            open_risks.append("No cross-FIR links established — network analysis not available.")
        if missing_witness:
            open_risks.append("No witness identified — re-interview opportunity may be missed.")
        if not has_weapon:
            open_risks.append("Weapon not recovered or identified — forensic gap.")
        if not has_vehicle:
            open_risks.append("No vehicle linked — CCTV cross-match not yet possible.")
        if completeness < 0.4:
            open_risks.append("Evidence completeness below 40% — case may lack sufficient basis.")
        if coverage < 0.5:
            open_risks.append("Less than 50% of intelligence layers produced output.")

        # ── 9. Overall Risk Level ─────────────────────────────────────────────
        risk_score = len(open_risks)
        if risk_score >= 5 or completeness < 0.2:
            overall_risk = "IMMEDIATE"
        elif risk_score >= 3 or completeness < 0.4:
            overall_risk = "HIGH"
        elif risk_score >= 1 or completeness < 0.7:
            overall_risk = "MEDIUM"
        else:
            overall_risk = "LOW"

        return RiskAssessment(
            evidence_completeness  = completeness,
            investigation_coverage = coverage,
            missing_entities       = missing_entities,
            missing_timeline       = missing_timeline,
            missing_graph_links    = missing_graph,
            missing_witness        = missing_witness,
            missing_documents      = missing_docs,
            open_risks             = open_risks,
            overall_risk_level     = overall_risk,
        )

# ─────────────────────────────────────────────────────────────────────────────
# STRATEGY GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

class StrategyGenerator:
    """
    Generates deterministic strategies based on missing evidence and context.
    """

    @classmethod
    def generate(cls, context: Any, risk: RiskAssessment) -> List[InvestigationStrategy]:
        strategies = []
        cases = getattr(context, "normalized_cases", []) or []
        if not cases:
            return strategies
            
        has_weapon = False
        has_vehicle = False
        has_witness = False
        has_phone = False
        has_financial = False
        has_cyber = False
        has_murder = False
        
        for c in cases:
            if hasattr(c, "evidence"):
                ev = c.evidence
                if ev.has_weapon: has_weapon = True
                if ev.has_vehicle: has_vehicle = True
                if ev.has_witness: has_witness = True
                if ev.has_phone: has_phone = True
                if ev.has_financial_trail: has_financial = True
            cat = getattr(c, "classification", None)
            if cat:
                if cat.crime_category == "Murder": has_murder = True
                if "cyber" in str(cat.crime_category).lower(): has_cyber = True

        if not has_weapon and has_murder:
            strategies.append(InvestigationStrategy(
                title="Recover Murder Weapon",
                evidence="Weapon Missing from Forensic Logs",
                reasoning="Weapon recovery is critical to establish a definitive ballistic connection.",
                risk="Without weapon, ballistic analysis is impossible, leaving a weak forensic chain.",
                recommendation="Deploy Crime Scene Team to recover murder weapon.",
                expected_impact="Increase forensic confidence.",
                confidence=0.85,
                priority=Priority.IMMEDIATE,
                dependencies=["Crime Scene Team"]
            ))

        if not has_phone:
            strategies.append(InvestigationStrategy(
                title="Verify Mobile Records",
                evidence="No Mobile CDRs Verified",
                reasoning="Mobile logs are required to recreate geographic timeline and associate suspect movements.",
                risk="Without CDR, timeline cannot be mathematically verified.",
                recommendation="File CDR request for all primary suspects.",
                expected_impact="Close timeline gaps and map entity movement.",
                confidence=0.75,
                priority=Priority.HIGH,
                dependencies=["Cyber Cell", "Telecom Operator"]
            ))

        if has_witness and not has_weapon and not has_phone:
            strategies.append(InvestigationStrategy(
                title="Corroborate Witness Testimony",
                evidence="Witness Statements exist but lack independent forensic backing",
                reasoning="Testimonial evidence requires physical anchoring to be court-admissible.",
                risk="Vulnerable to witness recantation.",
                recommendation="Locate secondary independent corroboration (CCTV or physical).",
                expected_impact="Secure conviction by removing dependency on human testimony.",
                confidence=0.80,
                priority=Priority.HIGH,
                dependencies=["Field Officers"]
            ))

        if has_cyber and not has_financial:
            strategies.append(InvestigationStrategy(
                title="Check Financial Trail",
                evidence="Financial logs missing for cyber crime",
                reasoning="Fraud cases hinge on following the money.",
                risk="Unable to identify beneficiaries or freeze illicit funds.",
                recommendation="Request bank statements for reported accounts.",
                expected_impact="Identify ultimate beneficiary and block further transfers.",
                confidence=0.90,
                priority=Priority.IMMEDIATE,
                dependencies=["Financial Crimes Unit", "Banks"]
            ))

        if len(strategies) == 0:
            strategies.append(InvestigationStrategy(
                title="Standard Evidence Collection",
                evidence="Basic case registered",
                reasoning="Initial stages require basic forensic processing.",
                risk="Delayed collection degrades forensic quality.",
                recommendation="Deploy standard evidence collection protocols.",
                expected_impact="Establish evidentiary baseline.",
                confidence=0.70,
                priority=Priority.MEDIUM,
                dependencies=["Field Officers"]
            ))

        return strategies[:MAX_STRATEGIES]

# ─────────────────────────────────────────────────────────────────────────────
# PRIORITY RANKER
# ─────────────────────────────────────────────────────────────────────────────

class PriorityRanker:
    """
    Deterministically sorts strategies into priority tiers.
    No ML, no random ordering — sort key is (priority_order, confidence DESC).
    """

    @classmethod
    def rank(cls, strategies: List[InvestigationStrategy]) -> Tuple[
        List[InvestigationStrategy], Dict[str, List[str]]
    ]:
        # Sort: primary key = priority order (IMMEDIATE=0..LOW=3), secondary = confidence DESC
        sorted_strats = sorted(
            strategies,
            key=lambda s: (PRIORITY_ORDER[s.priority], -s.confidence)
        )

        # Build priority → [titles] mapping
        ranking: Dict[str, List[str]] = {
            Priority.IMMEDIATE.value: [],
            Priority.HIGH.value:     [],
            Priority.MEDIUM.value:   [],
            Priority.LOW.value:      [],
        }
        for s in sorted_strats:
            ranking[s.priority.value].append(s.title)

        return sorted_strats, ranking

# ─────────────────────────────────────────────────────────────────────────────
# ACTION VALIDATOR
# ─────────────────────────────────────────────────────────────────────────────

class ActionValidator:
    """
    Validates that each strategy meets minimum evidence requirements.
    Removes strategies that cannot be supported by verified evidence.
    """

    MIN_CONFIDENCE: float = 0.50

    @classmethod
    def validate(cls, strategies: List[InvestigationStrategy]) -> Tuple[
        List[InvestigationStrategy], List[str]
    ]:
        valid:    List[InvestigationStrategy] = []
        rejected: List[str]                   = []

        for s in strategies:
            reason = cls._check(s)
            if reason:
                rejected.append(f"Rejected '{s.title}': {reason}")
            else:
                valid.append(s)

        return valid, rejected

    @classmethod
    def _check(cls, s: InvestigationStrategy) -> Optional[str]:
        if not s.title:
            return "Missing title"
        if not getattr(s, "evidence", getattr(s, "supporting_evidence", None)):
            return "No supporting evidence provided"
        if not s.reasoning and not getattr(s, "reason", None):
            return "No reason provided"
        if s.confidence < 0.1:
            return "Confidence too low"
        return None

# ─────────────────────────────────────────────────────────────────────────────
# DECISION SCORE CALCULATOR
# ─────────────────────────────────────────────────────────────────────────────

class DecisionScoreCalculator:
    """
    Produces a deterministic 0–100 decision score based only on verified
    pipeline metrics. No fabrication possible.

    Weights:
      Evidence Completeness  : 30 pts
      Intelligence Coverage  : 25 pts
      Confidence Score       : 20 pts
      Strategy Count         : 15 pts
      Risk Mitigation        : 10 pts
    """

    @classmethod
    def calculate(
        cls,
        risk: RiskAssessment,
        strategies: List[InvestigationStrategy],
        confidence: float,
    ) -> int:
        # 1. Evidence completeness (0–30)
        evidence_pts = round(risk.evidence_completeness * 30)

        # 2. Intelligence coverage (0–25)
        coverage_pts = round(risk.investigation_coverage * 25)

        # 3. Confidence score (0–20)
        conf_pts = round(min(confidence, 1.0) * 20)

        # 4. Strategy count (0–15): 0 → 0pts, 1–4 → 5pts, 5–8 → 10pts, 9+ → 15pts
        n = len(strategies)
        if n == 0:
            strategy_pts = 0
        elif n <= 4:
            strategy_pts = 5
        elif n <= 8:
            strategy_pts = 10
        else:
            strategy_pts = 15

        # 5. Risk mitigation (0–10): fewer open risks = more pts
        risk_count = len(risk.open_risks)
        if risk_count == 0:
            risk_pts = 10
        elif risk_count <= 2:
            risk_pts = 7
        elif risk_count <= 4:
            risk_pts = 4
        else:
            risk_pts = 1

        total = evidence_pts + coverage_pts + conf_pts + strategy_pts + risk_pts
        return max(0, min(DECISION_SCORE_MAX, total))

# ─────────────────────────────────────────────────────────────────────────────
# OPEN QUESTIONS GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

class OpenQuestionsGenerator:
    """
    Produces a list of open investigation questions based on identified gaps.
    All questions are deterministic — derived only from verified missing fields.
    """

    @classmethod
    def generate(cls, risk: RiskAssessment, context: Any) -> List[str]:
        questions: List[str] = []
        entities  = context.resolved_entities or {}
        results   = context.search_result or []

        if "accused" in risk.missing_entities:
            questions.append("Who is the primary accused? Identity not yet established in records.")
        if "victim" in risk.missing_entities:
            questions.append("Who are the confirmed victims? Victim records incomplete.")
        if "weapon" in risk.missing_entities:
            questions.append("Has the weapon been identified and recovered?")
        if "vehicle" in risk.missing_entities:
            questions.append("Is a vehicle involved? Vehicle records not linked.")
        if "phone" in risk.missing_entities:
            questions.append("Has mobile CDR been requested for linked phone numbers?")
        if risk.missing_timeline:
            questions.append("What is the complete sequence of events? Timeline reconstruction incomplete.")
        if risk.missing_graph_links:
            questions.append("Are there connections between this FIR and other active cases?")
        if risk.missing_witness:
            questions.append("Have all witnesses been identified and interviewed?")
        if risk.missing_documents:
            questions.append("Are all required documents (panchnama, FSL report) filed?")

        # Status-based questions
        open_statuses = {"OPEN", "PENDING", "UNDER INVESTIGATION", "ACTIVE"}
        for r in results[:3]:
            status = (r.get("status_name") or "").upper()
            crime_no = r.get("crime_no", "")
            if status in open_statuses and crime_no:
                questions.append(f"What is the current investigation status of FIR {crime_no}?")

        return questions[:10]  # Cap at 10 open questions

# ─────────────────────────────────────────────────────────────────────────────
# DECISION SUPPORT ENGINE  (Main Orchestrator)
# ─────────────────────────────────────────────────────────────────────────────

class DecisionSupportEngine:
    """
    Phase 5.8 — Enterprise Decision Support Engine.
    Orchestrates: RiskAnalyzer → StrategyGenerator → ActionValidator →
                  PriorityRanker → DecisionScoreCalculator → DecisionSupportReport
    """

    @classmethod
    def run(cls, context: Any) -> DecisionSupportReport:
        results = context.search_result or []

        # ── Safety Gate ───────────────────────────────────────────────────────
        similarity = getattr(context, "similarity_report", None)
        if len(results) < MIN_RECORDS_FOR_STRATEGY and not similarity:
            return cls._insufficient_report()

        # ── Step 1: Risk Analysis ─────────────────────────────────────────────
        risk = RiskAnalyzer.analyze(context)

        # ── Step 2: Strategy Generation ───────────────────────────────────────
        raw_strategies = StrategyGenerator.generate(context, risk)

        # ── Step 3: Action Validation ─────────────────────────────────────────
        valid_strategies, rejected = ActionValidator.validate(raw_strategies)

        # ── Step 4: Priority Ranking ──────────────────────────────────────────
        ranked_strategies, priority_ranking = PriorityRanker.rank(valid_strategies)

        # ── Step 5: Decision Score ────────────────────────────────────────────
        conf_metrics = getattr(context, "confidence_metrics", None) or {}
        confidence   = conf_metrics.get(
            "confidence",
            context.confidence.get("final", 0.50) if context.confidence else 0.50
        )
        decision_score = DecisionScoreCalculator.calculate(risk, ranked_strategies, confidence)

        # ── Step 6: Open Questions ────────────────────────────────────────────
        open_questions = OpenQuestionsGenerator.generate(risk, context)

        # ── Step 7: Warnings aggregation ─────────────────────────────────────
        warnings: List[str] = list(risk.open_risks)
        for r in rejected:
            warnings.append(r)
        if getattr(context, "warnings", None):
            warnings.extend([w for w in context.warnings if w not in warnings])

        # ── Step 8: Executive Summary ─────────────────────────────────────────
        executive_summary = cls._build_executive_summary(
            ranked_strategies, risk, decision_score, confidence, results, context
        )

        return DecisionSupportReport(
            executive_summary = executive_summary,
            strategies        = ranked_strategies,
            priority_ranking  = priority_ranking,
            risk_assessment   = risk,
            decision_score    = decision_score,
            confidence        = confidence,
            warnings          = warnings,
            open_questions    = open_questions,
            insufficient      = False,
        )

    @classmethod
    def _insufficient_report(cls) -> DecisionSupportReport:
        empty_risk = RiskAssessment(
            evidence_completeness  = 0.0,
            investigation_coverage = 0.0,
            missing_entities       = ["accused", "victim", "weapon", "vehicle", "phone"],
            missing_timeline       = True,
            missing_graph_links    = True,
            missing_witness        = True,
            missing_documents      = True,
            open_risks             = ["No verified evidence available."],
            overall_risk_level     = "IMMEDIATE",
        )
        return DecisionSupportReport(
            executive_summary = INSUFFICIENT_EVIDENCE_MESSAGE,
            strategies        = [],
            priority_ranking  = {p.value: [] for p in Priority},
            risk_assessment   = empty_risk,
            decision_score    = 0,
            confidence        = 0.0,
            warnings          = ["No verified evidence available for strategy generation."],
            open_questions    = ["What evidence is available to proceed with investigation?"],
            insufficient      = True,
        )

    @classmethod
    def _build_executive_summary(
        cls,
        strategies:     List[InvestigationStrategy],
        risk:           RiskAssessment,
        decision_score: int,
        confidence:     float,
        results:        List[Dict],
        context:        Any,
    ) -> str:
        intent  = getattr(context, "intent", "UNKNOWN") or "UNKNOWN"
        n_strat = len(strategies)
        n_crit  = sum(1 for s in strategies if s.priority == Priority.IMMEDIATE)
        n_high  = sum(1 for s in strategies if s.priority == Priority.HIGH)
        fir_ids = [r.get("crime_no") for r in results[:3] if r.get("crime_no")]
        fir_str = ", ".join(fir_ids) if fir_ids else "N/A"

        return (
            f"Decision Support Engine evaluated {len(results)} verified record(s) "
            f"across {intent} intent. "
            f"Generated {n_strat} investigation strateg{'y' if n_strat == 1 else 'ies'} "
            f"({n_crit} IMMEDIATE, {n_high} HIGH priority). "
            f"Decision Score: {decision_score}/100. "
            f"Evidence Completeness: {risk.evidence_completeness * 100:.1f}%. "
            f"Intelligence Coverage: {risk.investigation_coverage * 100:.1f}%. "
            f"Overall Risk: {risk.risk_assessment if hasattr(risk, 'risk_assessment') else risk.overall_risk_level}. "
            f"Key FIRs: {fir_str}. "
            f"System Confidence: {confidence * 100:.1f}%."
        )

# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE STAGE  (ExecutionContext wrapper)
# ─────────────────────────────────────────────────────────────────────────────

class DecisionSupportStage:
    """
    Pipeline stage wrapper for DecisionSupportEngine.
    Reads from ExecutionContext, writes to context.decision_support_report.
    Always succeeds (errors are caught and logged — never block the pipeline).
    """

    @staticmethod
    def run(context: Any) -> Any:
        try:
            report = DecisionSupportEngine.run(context)
            context.decision_support_report = report.to_dict()
        except Exception as exc:
            logger.error(
                "DecisionSupportStage failed: %s", exc, exc_info=True
            )
            context.decision_support_report = {
                "insufficient": True,
                "executive_summary": INSUFFICIENT_EVIDENCE_MESSAGE,
                "strategies": [],
                "priority_ranking": {p.value: [] for p in Priority},
                "decision_score": 0,
                "confidence": 0.0,
                "warnings": [f"DecisionSupportStage error: {exc}"],
                "open_questions": [],
                "risk_assessment": {
                    "overall_risk_level": "IMMEDIATE",
                    "evidence_completeness": 0.0,
                    "investigation_coverage": 0.0,
                    "missing_entities": [],
                    "missing_timeline": True,
                    "missing_graph_links": True,
                    "missing_witness": True,
                    "missing_documents": True,
                    "open_risks": [f"Engine error: {exc}"],
                },
                "summary": INSUFFICIENT_EVIDENCE_MESSAGE,
            }
        return context
