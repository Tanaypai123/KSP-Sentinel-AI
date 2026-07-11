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
    CRITICAL = "CRITICAL"
    HIGH     = "HIGH"
    MEDIUM   = "MEDIUM"
    LOW      = "LOW"

# Numeric value used for deterministic sort order (lower = higher priority)
PRIORITY_ORDER: Dict[str, int] = {
    Priority.CRITICAL: 0,
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
    """A single deterministic, evidence-backed investigation strategy."""
    strategy_type:      StrategyType
    title:              str
    reason:             str
    supporting_evidence: List[str]
    supporting_fir_ids: List[str]
    confidence:         float          # 0.0–1.0
    priority:           Priority
    dependencies:       List[str]
    warnings:           List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_type":       self.strategy_type.value,
            "title":               self.title,
            "reason":              self.reason,
            "supporting_evidence": self.supporting_evidence,
            "supporting_fir_ids":  self.supporting_fir_ids,
            "confidence":          round(self.confidence, 4),
            "priority":            self.priority.value,
            "dependencies":        self.dependencies,
            "warnings":            self.warnings,
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
    overall_risk_level:     str         # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"

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
        critical = self.priority_ranking.get(Priority.CRITICAL.value, [])
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
        # Collect what's present in records
        has_weapon  = any(r.get("weapon_type") or r.get("weapon") for r in results)
        has_vehicle = any(r.get("vehicle_no") or r.get("vehicle") for r in results)
        has_phone   = (kg_report.get("node_count", 0) > 0 and
                       "Phone" in str(kg_report.get("summary", "")))
        has_accused = any(r.get("accused_name") for r in results)
        has_victim  = any(r.get("victim_name") for r in results)

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
            overall_risk = "CRITICAL"
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
    Generates up to 10 deterministic investigation strategies.
    Each strategy is gated on verified pipeline evidence.
    No fabrication is possible — all conditions check specific context fields.
    """

    @classmethod
    def generate(cls, context: Any, risk: RiskAssessment) -> List[InvestigationStrategy]:
        strategies: List[InvestigationStrategy] = []
        results      = context.search_result or []
        entities     = context.resolved_entities or {}
        corr         = getattr(context, "evidence_correlation", None) or {}
        kg           = getattr(context, "knowledge_graph_report", None) or {}
        timeline     = getattr(context, "timeline_report", None) or {}
        similarity   = getattr(context, "similarity_report", None) or {}
        pred         = getattr(context, "predictive_report", None) or {}
        multi        = getattr(context, "multi_agent_report", None) or {}
        reasoning    = getattr(context, "reasoning_result", None) or {}
        intel        = getattr(context, "intelligence_bundle", None)
        conf_metrics = getattr(context, "confidence_metrics", None) or {}
        conf_score   = conf_metrics.get("confidence", context.confidence.get("final", 0.50) if context.confidence else 0.50)

        fir_ids = [r.get("crime_no") for r in results if r.get("crime_no")]

        # ── Strategy 1: Interview Suspect ─────────────────────────────────────
        accused_names = []
        for r in results:
            name = r.get("accused_name") or (
                r.get("accused_names", [None])[0] if isinstance(r.get("accused_names"), list) else None
            )
            if name and name not in accused_names:
                accused_names.append(name)

        repeat_risks = pred.get("repeat_offender_risks", []) if pred else []

        if accused_names or repeat_risks:
            evidence_items = []
            if accused_names:
                evidence_items.append(f"Accused identified: {', '.join(accused_names[:3])}")
            if repeat_risks:
                evidence_items.append(f"Repeat offender risk detected for {len(repeat_risks)} suspect(s)")
            if multi:
                evidence_items.append(f"Multi-agent corroboration: {multi.get('evidence_summary', 'confirmed')}")

            priority = Priority.CRITICAL if repeat_risks else Priority.HIGH
            strategies.append(InvestigationStrategy(
                strategy_type       = StrategyType.INTERVIEW_SUSPECT,
                title               = "Interview Identified Suspect(s)",
                reason              = (
                    f"Database records confirm {len(accused_names)} accused individual(s). "
                    + ("Repeat offender pattern detected." if repeat_risks else "")
                ),
                supporting_evidence = evidence_items,
                supporting_fir_ids  = fir_ids[:5],
                confidence          = min(0.95, 0.70 + 0.05 * len(accused_names)),
                priority            = priority,
                dependencies        = ["FIR retrieval", "Accused identification"],
                warnings            = (
                    ["Accused may be repeat offender — coordinate with Crime Records Bureau"]
                    if repeat_risks else []
                ),
            ))

        # ── Strategy 2: Collect CCTV ──────────────────────────────────────────
        has_location = bool(entities.get("district") or entities.get("police_station"))
        has_time_gap = timeline.get("gaps") and len(timeline["gaps"]) > 0 if timeline else False
        hotspots     = getattr(intel, "hotspots", None) if intel else None

        if has_location or has_time_gap or hotspots:
            evidence_items = []
            if has_location:
                loc = entities.get("district") or entities.get("police_station")
                evidence_items.append(f"Location context: {loc}")
            if has_time_gap:
                evidence_items.append(f"Timeline gaps identified: {len(timeline['gaps'])} unaccounted intervals")
            if hotspots and isinstance(hotspots, dict):
                zones = hotspots.get("risk_zones", [])
                if zones:
                    evidence_items.append(f"Hotspot zones: {', '.join(str(z) for z in zones[:2])}")

            strategies.append(InvestigationStrategy(
                strategy_type       = StrategyType.COLLECT_CCTV,
                title               = "Collect CCTV Footage from Incident Area",
                reason              = (
                    "Location and/or timeline gaps indicate CCTV coverage may capture "
                    "suspect movement or vehicle transit."
                ),
                supporting_evidence = evidence_items,
                supporting_fir_ids  = fir_ids[:3],
                confidence          = 0.80 if has_time_gap else 0.65,
                priority            = Priority.HIGH if has_time_gap else Priority.MEDIUM,
                dependencies        = ["Location confirmed", "Approximate incident time established"],
                warnings            = ["CCTV retention period may have elapsed for older FIRs"],
            ))

        # ── Strategy 3: Verify Mobile Records ────────────────────────────────
        kg_node_types  = kg.get("node_types", {}) if isinstance(kg, dict) else {}
        phone_nodes    = kg_node_types.get("Phone", 0)
        corr_edges     = corr.get("edges", []) if corr else []
        phone_in_corr  = any("Phone" in str(e) for e in corr_edges)

        if phone_nodes > 0 or phone_in_corr or entities.get("phone"):
            evidence_items = []
            if phone_nodes > 0:
                evidence_items.append(f"Knowledge Graph: {phone_nodes} phone node(s) identified")
            if phone_in_corr:
                evidence_items.append("Evidence Correlation: phone link detected across FIRs")
            if entities.get("phone"):
                evidence_items.append(f"Entity extracted: phone={entities['phone']}")

            strategies.append(InvestigationStrategy(
                strategy_type       = StrategyType.VERIFY_MOBILE_RECORDS,
                title               = "Verify Mobile Call Records (CDR)",
                reason              = (
                    "Phone numbers identified in the knowledge graph or evidence "
                    "correlation. CDR verification can establish communication links."
                ),
                supporting_evidence = evidence_items,
                supporting_fir_ids  = fir_ids[:4],
                confidence          = 0.85,
                priority            = Priority.HIGH,
                dependencies        = ["Phone number confirmed", "Court order / legal authorization"],
                warnings            = ["CDR request requires judicial authorization"],
            ))

        # ── Strategy 4: Check Financial Trail ────────────────────────────────
        has_repeat     = bool(repeat_risks)
        org_nodes      = kg_node_types.get("Organization", 0)
        gang_in_results = any(r.get("gang_name") or r.get("organization") for r in results)

        if has_repeat or org_nodes > 0 or gang_in_results:
            evidence_items = []
            if has_repeat:
                evidence_items.append(f"Repeat offender: {len(repeat_risks)} suspect(s) with escalation risk")
            if org_nodes > 0:
                evidence_items.append(f"Organization nodes in graph: {org_nodes}")
            if gang_in_results:
                evidence_items.append("Gang/organization affiliation detected in records")

            strategies.append(InvestigationStrategy(
                strategy_type       = StrategyType.CHECK_FINANCIAL_TRAIL,
                title               = "Investigate Financial Trail",
                reason              = (
                    "Repeat offender pattern or organizational links suggest structured "
                    "criminal activity. Financial trail may reveal funding sources."
                ),
                supporting_evidence = evidence_items,
                supporting_fir_ids  = fir_ids[:4],
                confidence          = 0.75,
                priority            = Priority.HIGH if has_repeat else Priority.MEDIUM,
                dependencies        = ["Accused identity confirmed", "Organizational link established"],
                warnings            = ["Financial investigation requires bank cooperation order"],
            ))

        # ── Strategy 5: Cross-Match Vehicles ─────────────────────────────────
        vehicle_nodes   = kg_node_types.get("Vehicle", 0)
        vehicle_in_corr = any("Vehicle" in str(e) for e in corr_edges)
        vehicle_entity  = entities.get("vehicle") or entities.get("vehicle_no")
        vehicle_in_rec  = any(r.get("vehicle_no") or r.get("vehicle_type") for r in results)

        if vehicle_nodes > 0 or vehicle_in_corr or vehicle_entity or vehicle_in_rec:
            evidence_items = []
            if vehicle_nodes > 0:
                evidence_items.append(f"Knowledge Graph: {vehicle_nodes} vehicle node(s)")
            if vehicle_in_corr:
                evidence_items.append("Vehicle link detected across multiple FIRs")
            if vehicle_entity:
                evidence_items.append(f"Vehicle entity: {vehicle_entity}")
            if vehicle_in_rec and not vehicle_nodes and not vehicle_in_corr and not vehicle_entity:
                veh_nos = [r.get("vehicle_no") or r.get("vehicle_type") for r in results
                           if r.get("vehicle_no") or r.get("vehicle_type")]
                evidence_items.append(f"Vehicle in FIR records: {', '.join(str(v) for v in veh_nos[:3])}")

            strategies.append(InvestigationStrategy(
                strategy_type       = StrategyType.CROSS_MATCH_VEHICLES,
                title               = "Cross-Match Vehicle Records (RTO/Vahan)",
                reason              = (
                    "Vehicle evidence identified across FIRs. Cross-matching with RTO/Vahan "
                    "database can identify owner and movement history."
                ),
                supporting_evidence = evidence_items,
                supporting_fir_ids  = fir_ids[:5],
                confidence          = 0.88,
                priority            = Priority.HIGH,
                dependencies        = ["Vehicle number identified"],
                warnings            = ["Vehicle may have been re-registered or scrapped"],
            ))

        # ── Strategy 6: Analyze Crime Hotspot ────────────────────────────────
        has_hotspot_data = hotspots and (
            isinstance(hotspots, dict) and (
                hotspots.get("risk_zones") or hotspots.get("peak_hours")
            )
        )
        has_hotspot_list = isinstance(hotspots, list) and len(hotspots) > 0
        district_multi   = len(set(r.get("district_name") for r in results if r.get("district_name"))) > 1

        if has_hotspot_data or has_hotspot_list or district_multi:
            evidence_items = []
            if has_hotspot_data and isinstance(hotspots, dict):
                zones = hotspots.get("risk_zones", [])
                peak  = hotspots.get("peak_hours", [])
                if zones:
                    evidence_items.append(f"Risk zones: {', '.join(str(z) for z in zones[:3])}")
                if peak:
                    evidence_items.append(f"Peak hours: {', '.join(str(h) for h in peak[:3])}")
            if district_multi:
                evidence_items.append("Cases span multiple districts — geographic spread detected")

            strategies.append(InvestigationStrategy(
                strategy_type       = StrategyType.ANALYZE_HOTSPOT,
                title               = "Conduct Crime Hotspot Analysis",
                reason              = (
                    "Hotspot intelligence or multi-district spread indicates geographic "
                    "crime concentration requiring targeted patrol deployment."
                ),
                supporting_evidence = evidence_items,
                supporting_fir_ids  = fir_ids[:5],
                confidence          = 0.80,
                priority            = Priority.MEDIUM,
                dependencies        = ["Minimum 3 cases in target area"],
                warnings            = [],
            ))

        # ── Strategy 7: Recover Weapon ───────────────────────────────────────
        weapon_nodes   = kg_node_types.get("Weapon", 0)
        weapon_in_corr = any("Weapon" in str(e) for e in corr_edges)
        weapon_entity  = entities.get("weapon") or entities.get("weapon_type")
        weapon_in_rec  = any(r.get("weapon_type") or r.get("weapon") for r in results)

        if weapon_nodes > 0 or weapon_in_corr or weapon_entity or weapon_in_rec:
            evidence_items = []
            if weapon_nodes > 0:
                evidence_items.append(f"Knowledge Graph: {weapon_nodes} weapon node(s)")
            if weapon_in_corr:
                evidence_items.append("Weapon linked across multiple FIRs in evidence correlation")
            if weapon_entity:
                evidence_items.append(f"Weapon entity: {weapon_entity}")
            if weapon_in_rec and not weapon_nodes and not weapon_in_corr and not weapon_entity:
                wep_types = [r.get("weapon_type") or r.get("weapon") for r in results
                             if r.get("weapon_type") or r.get("weapon")]
                evidence_items.append(f"Weapon in FIR records: {', '.join(str(w) for w in wep_types[:3])}")

            strategies.append(InvestigationStrategy(
                strategy_type       = StrategyType.RECOVER_WEAPON,
                title               = "Initiate Weapon Recovery Operation",
                reason              = (
                    "Weapon identified in knowledge graph or case records. "
                    "Recovery is essential for forensic analysis and charge framing."
                ),
                supporting_evidence = evidence_items,
                supporting_fir_ids  = fir_ids[:5],
                confidence          = 0.85,
                priority            = Priority.CRITICAL if weapon_nodes > 1 else Priority.HIGH,
                dependencies        = ["Weapon type identified", "Last known location"],
                warnings            = ["Weapon may be concealed — deploy K9 unit if required"],
            ))

        # ── Strategy 8: Re-Interview Witness ──────────────────────────────────
        witness_nodes     = kg_node_types.get("Witness", 0)
        witness_in_tl     = "witness" in str(timeline).lower()
        sim_recommendations = []
        if isinstance(similarity, dict):
            for sim_case in similarity.get("top_matches", [])[:3]:
                for rec in (sim_case.get("recommendations", []) if isinstance(sim_case, dict) else []):
                    if isinstance(rec, dict) and "witness" in rec.get("title", "").lower():
                        sim_recommendations.append(rec.get("title", "Witness follow-up"))

        if witness_nodes > 0 or witness_in_tl or sim_recommendations:
            evidence_items = []
            if witness_nodes > 0:
                evidence_items.append(f"Knowledge Graph: {witness_nodes} witness node(s) identified")
            if witness_in_tl:
                evidence_items.append("Witness referenced in timeline reconstruction")
            if sim_recommendations:
                evidence_items.append("Similar case recommends witness follow-up")

            strategies.append(InvestigationStrategy(
                strategy_type       = StrategyType.REINTERVIEW_WITNESS,
                title               = "Re-Interview Identified Witnesses",
                reason              = (
                    "Witness evidence identified. Re-interview may reveal additional "
                    "details missed in initial recording."
                ),
                supporting_evidence = evidence_items,
                supporting_fir_ids  = fir_ids[:3],
                confidence          = 0.78,
                priority            = Priority.HIGH,
                dependencies        = ["Witness identity confirmed", "Witness availability"],
                warnings            = ["Witness may have changed statement — record carefully"],
            ))

        # ── Strategy 9: Check Nearby FIRs ────────────────────────────────────
        sim_matches = []
        if isinstance(similarity, dict):
            sim_matches = similarity.get("top_matches", [])
        sim_score_ok = isinstance(similarity, dict) and similarity.get("similarity_pct", 0) >= 20

        if sim_matches or sim_score_ok:
            evidence_items = []
            if sim_matches:
                evidence_items.append(f"{len(sim_matches)} similar FIR(s) identified by Case Similarity Engine")
                for m in sim_matches[:2]:
                    if isinstance(m, dict) and m.get("fir_id"):
                        evidence_items.append(f"Similar FIR: {m['fir_id']} (score: {m.get('similarity_pct', 0):.1f}%)")
            if sim_score_ok:
                evidence_items.append(f"Similarity score ≥ 20% — MO pattern match confirmed")

            strategies.append(InvestigationStrategy(
                strategy_type       = StrategyType.CHECK_NEARBY_FIRS,
                title               = "Cross-Reference Nearby Similar FIRs",
                reason              = (
                    "Case Similarity Engine identified verified matching investigations. "
                    "Nearby FIR cross-referencing may reveal shared suspects or MO."
                ),
                supporting_evidence = evidence_items,
                supporting_fir_ids  = fir_ids[:5],
                confidence          = 0.82,
                priority            = Priority.MEDIUM,
                dependencies        = ["Similar case records available"],
                warnings            = [],
            ))

        # ── Strategy 10: Review Forensic Evidence ────────────────────────────
        open_cases   = [r for r in results if r.get("status_name", "").upper() in
                        ("OPEN", "PENDING", "UNDER INVESTIGATION", "ACTIVE")]
        low_conf     = conf_score < 0.70
        long_pending = timeline.get("event_count", 0) > 3 and timeline.get("dated_event_count", 0) > 0

        if open_cases or (low_conf and results):
            evidence_items = []
            if open_cases:
                evidence_items.append(f"{len(open_cases)} case(s) with open/pending status")
            if low_conf:
                evidence_items.append(f"System confidence below threshold: {conf_score * 100:.1f}%")
            if long_pending:
                evidence_items.append(f"Extended investigation detected: {timeline.get('event_count', 0)} timeline events")
            if reasoning.get("conclusion"):
                evidence_items.append(f"Reasoning: {reasoning['conclusion']}")

            strategies.append(InvestigationStrategy(
                strategy_type       = StrategyType.REVIEW_FORENSIC_EVIDENCE,
                title               = "Comprehensive Forensic Evidence Review",
                reason              = (
                    "Case remains open with insufficient confidence or extended timeline. "
                    "Full forensic review may close evidence gaps."
                ),
                supporting_evidence = evidence_items,
                supporting_fir_ids  = [r.get("crime_no") for r in open_cases[:5] if r.get("crime_no")],
                confidence          = 0.72,
                priority            = Priority.MEDIUM if not low_conf else Priority.HIGH,
                dependencies        = ["Forensic lab access", "Original case file"],
                warnings            = ["Biological evidence degrades — prioritize if case is recent"],
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
        # Sort: primary key = priority order (CRITICAL=0..LOW=3), secondary = confidence DESC
        sorted_strats = sorted(
            strategies,
            key=lambda s: (PRIORITY_ORDER[s.priority], -s.confidence)
        )

        # Build priority → [titles] mapping
        ranking: Dict[str, List[str]] = {
            Priority.CRITICAL.value: [],
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
        """Returns rejection reason string, or None if valid."""
        if s.confidence < cls.MIN_CONFIDENCE:
            return f"confidence {s.confidence:.2f} below minimum {cls.MIN_CONFIDENCE}"
        if not s.supporting_evidence:
            return "no supporting evidence provided"
        if not s.title.strip():
            return "strategy title is empty"
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
            overall_risk_level     = "CRITICAL",
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
        n_crit  = sum(1 for s in strategies if s.priority == Priority.CRITICAL)
        n_high  = sum(1 for s in strategies if s.priority == Priority.HIGH)
        fir_ids = [r.get("crime_no") for r in results[:3] if r.get("crime_no")]
        fir_str = ", ".join(fir_ids) if fir_ids else "N/A"

        return (
            f"Decision Support Engine evaluated {len(results)} verified record(s) "
            f"across {intent} intent. "
            f"Generated {n_strat} investigation strateg{'y' if n_strat == 1 else 'ies'} "
            f"({n_crit} CRITICAL, {n_high} HIGH priority). "
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
                    "overall_risk_level": "CRITICAL",
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
