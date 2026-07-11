"""
response_formatter.py
=====================
Enterprise Response Formatter for KSP Sentinel AI.

Transforms raw pipeline outputs into clean, professional,
officer-friendly investigation reports.

NEVER exposes:
  - SQL queries / table names / database filters
  - Pipeline stage names or execution order
  - Confidence math / penalty calculations
  - Debug logs / memory state / stack traces
  - Internal IDs / developer warnings / raw JSON

ALWAYS shows (only when data is present):
  - Executive Summary
  - FIR Details
  - People Involved
  - Evidence
  - Related Cases
  - Timeline
  - AI Findings
  - Risk Assessment
  - Recommended Actions
  - Warnings
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal data models (clean, dev-detail-free)
# ---------------------------------------------------------------------------

@dataclass
class FIRDetail:
    fir_number: str = ""
    crime_type: str = ""
    status: str = ""
    district: str = ""
    police_station: str = ""
    date: str = ""


@dataclass
class PersonSet:
    accused: List[str] = field(default_factory=list)
    victims: List[str] = field(default_factory=list)
    witnesses: List[str] = field(default_factory=list)
    officers: List[str] = field(default_factory=list)


@dataclass
class EvidenceItem:
    label: str
    available: bool = True  # True → ✅, False → ❌


@dataclass
class RelatedCase:
    fir_number: str
    reason: str
    similarity: str


@dataclass
class TimelineEvent:
    description: str


@dataclass
class RiskInfo:
    level: str = "UNKNOWN"          # LOW / MEDIUM / HIGH / CRITICAL
    confidence_pct: float = 0.0
    reasons: List[str] = field(default_factory=list)


@dataclass
class RecommendedAction:
    text: str
    priority: str = "MEDIUM"


@dataclass
class OfficerReport:
    """Normalised, dev-detail-free report object."""
    executive_summary: str = ""
    fir_details: Optional[FIRDetail] = None
    people: Optional[PersonSet] = None
    evidence: List[EvidenceItem] = field(default_factory=list)
    related_cases: List[RelatedCase] = field(default_factory=list)
    timeline: List[TimelineEvent] = field(default_factory=list)
    ai_findings: List[str] = field(default_factory=list)
    risk: Optional[RiskInfo] = None
    recommended_actions: List[RecommendedAction] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Section Renderers
# ---------------------------------------------------------------------------

class SummaryRenderer:
    @staticmethod
    def render(report: OfficerReport) -> str:
        text = report.executive_summary.strip() if report.executive_summary else ""
        
        lines = ["📋 EXECUTIVE SUMMARY\n"]
        if text:
            lines.append(text + "\n")
            
        fir = report.fir_details
        if fir:
            if fir.fir_number:
                lines.append(f"FIR : {fir.fir_number}")
            if fir.crime_type:
                lines.append(f"Crime : {fir.crime_type}")
            if fir.status:
                lines.append(f"Status : {fir.status}")
            if fir.district:
                lines.append(f"District : {fir.district}")
            lines.append("")
            
        risk = report.risk
        if risk:
            level_emoji = {
                "LOW": "🟢",
                "MEDIUM": "🟡",
                "HIGH": "🔴",
                "CRITICAL": "🔴",
            }.get(risk.level.upper(), "⚪")
            lines.append(f"Overall Risk : {level_emoji} {risk.level.capitalize()}")
            lines.append(f"Confidence : {int(risk.confidence_pct)}%")

        return "\n".join(lines).strip()


class FIRRenderer:
    @staticmethod
    def render(fir: Optional[FIRDetail]) -> str:
        if not fir:
            return ""
        lines = []
        if fir.fir_number:
            lines.append(f"• FIR Number: {fir.fir_number}")
        if fir.crime_type:
            lines.append(f"• Crime Type: {fir.crime_type}")
        if fir.status:
            lines.append(f"• Status: {fir.status}")
        if fir.district:
            lines.append(f"• District: {fir.district}")
        if fir.police_station:
            lines.append(f"• Police Station: {fir.police_station}")
        if fir.date:
            lines.append(f"• Date: {fir.date}")
        if not lines:
            return ""
        return "📁 FIR DETAILS\n==============\n" + "\n".join(lines) + "\n"


class EntityRenderer:
    @staticmethod
    def render(people: Optional[PersonSet]) -> str:
        if not people:
            return ""
        sections = []
        if people.accused:
            acc = "\n".join(f"• {a}" for a in people.accused)
            sections.append(f"Accused\n{acc}")
        if people.victims:
            vic = "\n".join(f"• {v}" for v in people.victims)
            sections.append(f"Victims\n{vic}")
        if people.witnesses:
            wit = "\n".join(f"• {w}" for w in people.witnesses)
            sections.append(f"Witnesses\n{wit}")
        if people.officers:
            off = "\n".join(f"• {o}" for o in people.officers)
            sections.append(f"Investigating Officers\n{off}")
        if not sections:
            return ""
        return "👥 PEOPLE INVOLVED\n\n" + "\n\n".join(sections) + "\n"


class EvidenceRenderer:
    @staticmethod
    def render(evidence: List[EvidenceItem]) -> str:
        header = "🔍 VERIFIED EVIDENCE\n\n"
        if not evidence:
            return header + "❌ No verified evidence available\n"
        lines = []
        for item in evidence:
            icon = "✅" if item.available else "❌"
            lines.append(f"{icon} {item.label}")
        return header + "\n".join(lines) + "\n"


class CorrelationRenderer:
    @staticmethod
    def render(cases: List[RelatedCase]) -> str:
        if not cases:
            return ""
        header = "🔗 RELATED CASES\n\n"
        lines = []
        for c in cases[:5]:           # cap at 5
            lines.append(
                f"• {c.fir_number} - {c.reason} (Similarity: {c.similarity})"
            )
        return header + "\n".join(lines) + "\n"


class TimelineRenderer:
    @staticmethod
    def render(events: List[TimelineEvent]) -> str:
        if not events:
            return ""
        header = "📅 INVESTIGATION TIMELINE\n\n"
        lines = []
        for e in events[:6]:
            parts = e.description.split(" — ", 1)
            if len(parts) == 2:
                date_str, desc = parts
                lines.append(f"{date_str}\n• {desc}")
            else:
                lines.append(f"• {e.description}")
        return header + "\n\n".join(lines) + "\n"


class FindingsRenderer:
    @staticmethod
    def render(findings: List[str]) -> str:
        if not findings:
            return ""
        header = "🧠 AI FINDINGS\n\n"
        lines = [f"• {f}" for f in findings]
        return header + "\n".join(lines) + "\n"


class RiskRenderer:
    @staticmethod
    def render(risk: Optional[RiskInfo]) -> str:
        if not risk:
            return ""
        level_emoji = {
            "LOW": "🟢",
            "MEDIUM": "🟡",
            "HIGH": "🔴",
            "CRITICAL": "🔴",
        }.get(risk.level.upper(), "⚪")
        
        reasons_text = ""
        if risk.reasons:
            reasons_text = "Reason\n\n" + "\n".join([f"• {r}" for r in risk.reasons])
        else:
            reasons_text = "Reason\n\n• Investigation incomplete"
            
        return (
            "⚠️ RISK ASSESSMENT\n\n"
            f"Risk Level : {level_emoji} {risk.level.capitalize()}\n\n"
            f"{reasons_text}\n"
        )


class RecommendationRenderer:
    @staticmethod
    def render(actions: List[RecommendedAction]) -> str:
        if not actions:
            return ""
        header = "✅ RECOMMENDED ACTIONS\n\n"
        lines = []
        priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        sorted_actions = sorted(
            actions[:5],
            key=lambda a: priority_order.get(a.priority.upper(), 2)
        )
        for i, action in enumerate(sorted_actions, 1):
            lines.append(f"{i}. {action.text}")
        return header + "\n".join(lines) + "\n"


class WarningRenderer:
    @staticmethod
    def render(warnings: List[str]) -> str:
        if not warnings:
            return ""
        header = "⚠️ WARNINGS\n\n"
        lines = [f"• {w}" for w in warnings]
        return header + "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# OfficerReportBuilder  — normalises raw ExecutionContext data → OfficerReport
# ---------------------------------------------------------------------------

class OfficerReportBuilder:
    """
    Consumes raw pipeline data from ExecutionContext fields
    and builds a clean OfficerReport with all developer details stripped.
    """

    # Fields that are never allowed in any user-facing string
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
        """Return True if the text is safe to show an officer."""
        if not text:
            return True
        lower = text.lower()
        return not any(p in lower for p in cls._DEV_PATTERNS)

    @classmethod
    def _sanitize(cls, text: str) -> str:
        """Strip lines that contain developer-only content."""
        lines = text.splitlines()
        safe = [l for l in lines if cls._is_safe(l)]
        return "\n".join(safe).strip()

    # ------------------------------------------------------------------
    # Executive Summary
    # ------------------------------------------------------------------
    @classmethod
    def _build_summary(cls, context: Any) -> str:
        intent = getattr(context, "intent", "") or ""
        results = getattr(context, "search_result", []) or []
        entities = getattr(context, "resolved_entities", {}) or {}

        conversational_intents = {
            "GREETING", "GOODBYE", "THANKS", "HELP",
            "BOT_IDENTITY", "BOT_CAPABILITIES", "UNKNOWN", "GENERAL_CHAT"
        }

        if intent in conversational_intents:
            # Use existing conversational response text
            existing_resp = getattr(context, "response", None) or {}
            return cls._sanitize(existing_resp.get("summary", ""))

        if not results:
            return "No matching investigation records were found for your query."

        count = len(results)
        crime = (entities.get("crime_head") or "case").replace("_", " ").lower()
        district = entities.get("district") or "the jurisdiction"

        if intent == "SEARCH_ACCUSED":
            return f"{count} accused profile(s) identified matching the investigation criteria."
        if intent == "SEARCH_VICTIMS":
            return f"{count} victim record(s) retrieved for the active investigation."
        if intent == "FIR_LOOKUP":
            ids = entities.get("identifiers", [])
            fir_num = ids[0] if ids else "requested case"
            return f"Investigation record retrieved for FIR {fir_num}."
        if intent == "NETWORK_SEARCH":
            return "Criminal network graph successfully generated for the investigation."
        if intent == "HOTSPOT":
            return "Crime hotspot intelligence report generated for the requested area."
        if intent == "AGGREGATE_COUNT":
            return f"Statistical count computed: {count} record(s) match the specified criteria."
        return (
            f"{count} {crime} record(s) identified in {district} "
            "matching your investigation criteria."
        )

    # ------------------------------------------------------------------
    # FIR Details (only for single-record or FIR_LOOKUP)
    # ------------------------------------------------------------------
    @classmethod
    def _build_fir_detail(cls, context: Any) -> Optional[FIRDetail]:
        results = getattr(context, "search_result", []) or []
        intent = getattr(context, "intent", "") or ""
        if intent not in ("FIR_LOOKUP",) or not results:
            return None
        r = results[0]
        return FIRDetail(
            fir_number=str(r.get("crime_no") or r.get("fir_no") or ""),
            crime_type=str(r.get("crime_category") or r.get("crime_type") or ""),
            status=str(r.get("status_name") or ""),
            district=str(r.get("district_name") or ""),
            police_station=str(r.get("police_station_name") or ""),
            date=str(r.get("crime_registered_date") or r.get("date") or ""),
        )

    # ------------------------------------------------------------------
    # People Involved
    # ------------------------------------------------------------------
    @classmethod
    def _build_people(cls, context: Any) -> Optional[PersonSet]:
        results = getattr(context, "search_result", []) or []
        if not results:
            return None
        accused, victims, witnesses = [], [], []
        for r in results[:10]:
            names = r.get("accused_names") or []
            if not names and r.get("accused_name"):
                names = [r["accused_name"]]
            accused.extend([n for n in names if n and n not in accused])

            vnames = r.get("victim_names") or []
            if not vnames and r.get("victim_name"):
                vnames = [r["victim_name"]]
            victims.extend([v for v in vnames if v and v not in victims])

        if not accused and not victims:
            return None
        ps = PersonSet()
        ps.accused = accused[:10]
        ps.victims = victims[:10]
        ps.witnesses = witnesses
        return ps

    # ------------------------------------------------------------------
    # Evidence
    # ------------------------------------------------------------------
    @classmethod
    def _build_evidence(cls, context: Any) -> List[EvidenceItem]:
        results = getattr(context, "search_result", []) or []
        items: List[EvidenceItem] = []
        seen: set = set()

        for r in results[:5]:
            # Physical evidence
            for key, label in [
                ("evidence_list", None),
                ("cctv_available", "CCTV Footage"),
                ("mobile_records", "Mobile Records"),
                ("witnesses_available", "Witness Statements"),
                ("weapon_recovered", "Weapon Recovered"),
                ("fingerprints", "Fingerprints"),
                ("forensic_report", "Forensic Report"),
            ]:
                val = r.get(key)
                if val is None:
                    continue
                if key == "evidence_list" and isinstance(val, list):
                    for e in val:
                        if e and e not in seen:
                            seen.add(e)
                            items.append(EvidenceItem(label=str(e), available=True))
                elif isinstance(val, bool):
                    lab = label or key.replace("_", " ").title()
                    if lab not in seen:
                        seen.add(lab)
                        items.append(EvidenceItem(label=lab, available=val))
                elif val:
                    lab = label or key.replace("_", " ").title()
                    if lab not in seen:
                        seen.add(lab)
                        items.append(EvidenceItem(label=str(val), available=True))

        # Evidence from correlation engine
        ev_corr = getattr(context, "evidence_correlation", None)
        if ev_corr and isinstance(ev_corr, dict):
            for item in ev_corr.get("evidence_items", [])[:5]:
                label = item.get("description") or item.get("type") or ""
                if label and label not in seen:
                    seen.add(label)
                    items.append(EvidenceItem(label=label, available=True))

        return items

    # ------------------------------------------------------------------
    # Related Cases
    # ------------------------------------------------------------------
    @classmethod
    def _build_related(cls, context: Any) -> List[RelatedCase]:
        cases: List[RelatedCase] = []
        # From similarity engine
        sim = getattr(context, "similarity_report", None)
        if sim and isinstance(sim, dict):
            for c in sim.get("similar_cases", [])[:5]:
                fno = str(c.get("fir_no") or c.get("crime_no") or "")
                reason = str(c.get("reason") or c.get("similarity_reason") or "Similar crime profile")
                score = c.get("similarity_score") or c.get("score") or 0
                sim_str = f"{float(score)*100:.0f}%" if isinstance(score, (int, float)) else str(score)
                if fno:
                    cases.append(RelatedCase(fir_number=fno, reason=reason, similarity=sim_str))
        # From results with _similarity_score
        if not cases:
            results = getattr(context, "search_result", []) or []
            for r in results[:5]:
                if r.get("_similarity_score"):
                    fno = str(r.get("fir_no") or r.get("crime_no") or "")
                    expl = str(r.get("_similarity_explanation") or "Similar case pattern")
                    score = r.get("_similarity_score", 0)
                    sim_str = f"{float(score)*100:.0f}%" if isinstance(score, (int, float)) else str(score)
                    if fno:
                        cases.append(RelatedCase(fir_number=fno, reason=expl, similarity=sim_str))
        return cases

    # ------------------------------------------------------------------
    # Timeline
    # ------------------------------------------------------------------
    @classmethod
    def _build_timeline(cls, context: Any) -> List[TimelineEvent]:
        events: List[TimelineEvent] = []
        tl = getattr(context, "timeline_report", None)
        if not tl or not isinstance(tl, dict):
            return events
        for ev in tl.get("events", [])[:6]:
            desc = ev.get("description") or ev.get("event") or ""
            ts = ev.get("timestamp") or ev.get("date") or ""
            label = f"{ts} — {desc}".strip(" —") if ts else desc
            if label:
                events.append(TimelineEvent(description=label))
        return events

    # ------------------------------------------------------------------
    # AI Findings (sanitised reasoning + pattern)
    # ------------------------------------------------------------------
    @classmethod
    def _build_findings(cls, context: Any) -> List[str]:
        findings: List[str] = []

        # Crime pattern
        bundle = getattr(context, "intelligence_bundle", None)
        if bundle:
            pattern = getattr(bundle, "pattern_analysis", None)
            if pattern and cls._is_safe(str(pattern)):
                findings.append(cls._sanitize(str(pattern)))

        # Custom officer-friendly record finding
        results = getattr(context, "search_result", []) or []
        count = len(results)
        if count == 1:
            findings.append("One verified FIR was found.")
        elif count > 1:
            findings.append(f"{count} verified records were found.")
        else:
            findings.append("No supporting evidence or verified records found.")

        kg = getattr(context, "knowledge_graph_report", None)
        if kg and isinstance(kg, dict):
            kg_sum = kg.get("summary", "")
            if kg_sum and cls._is_safe(kg_sum):
                clean_kg = cls._sanitize(kg_sum)
                if "knowledge graph" in clean_kg.lower():
                    clean_kg = clean_kg.replace("build knowledge graph", "establish network links")
                findings.append(clean_kg)

        return findings[:5]

    # ------------------------------------------------------------------
    # Risk Assessment
    # ------------------------------------------------------------------
    @classmethod
    def _build_risk(cls, context: Any) -> Optional[RiskInfo]:
        ds = getattr(context, "decision_support_report", None)
        if ds and isinstance(ds, dict):
            ra = ds.get("risk_assessment", {})
            level = ra.get("overall_risk_level", "")
            if level:
                conf = context.confidence.get("final", 0.5) if hasattr(context, "confidence") else 0.5
                open_risks = ra.get("open_risks", [])
                safe_risks = [cls._sanitize(r) for r in open_risks if cls._is_safe(r) and r]
                return RiskInfo(level=level.upper(), confidence_pct=conf * 100, reasons=safe_risks[:3])

        # Fallback: confidence metrics
        cm = getattr(context, "confidence_metrics", None)
        if cm and isinstance(cm, dict):
            risk = cm.get("risk", "MEDIUM")
            conf = cm.get("confidence", 0.5)
            return RiskInfo(level=str(risk).upper(), confidence_pct=float(conf) * 100, reasons=[])

        # Minimal fallback
        conf_val = 0.5
        if hasattr(context, "confidence") and isinstance(context.confidence, dict):
            conf_val = context.confidence.get("final", 0.5) or 0.5
        return RiskInfo(level="MEDIUM", confidence_pct=conf_val * 100, reasons=[])

    # ------------------------------------------------------------------
    # Recommended Actions
    # ------------------------------------------------------------------
    @classmethod
    def _build_recommendations(cls, context: Any) -> List[RecommendedAction]:
        actions: List[RecommendedAction] = []

        # From intelligence bundle
        bundle = getattr(context, "intelligence_bundle", None)
        if bundle:
            rec_list = getattr(bundle, "recommendations", []) or []
            for r in rec_list[:5]:
                act = r.get("action") or ""
                prio = r.get("priority") or "MEDIUM"
                if act and cls._is_safe(act):
                    actions.append(RecommendedAction(text=act, priority=prio))

        # From decision support
        ds = getattr(context, "decision_support_report", None)
        if ds and isinstance(ds, dict) and len(actions) < 5:
            for strat in ds.get("strategies", [])[:5 - len(actions)]:
                title = strat.get("title") or strat.get("description") or ""
                prio = strat.get("priority") or "MEDIUM"
                if title and cls._is_safe(title):
                    actions.append(RecommendedAction(text=title, priority=prio))

        # From hotspot data
        if not actions:
            bundle = getattr(context, "intelligence_bundle", None)
            if bundle:
                hs = getattr(bundle, "hotspots", None)
                if isinstance(hs, dict):
                    for rec in hs.get("recommendations", [])[:5]:
                        if rec and cls._is_safe(str(rec)):
                            actions.append(RecommendedAction(text=str(rec), priority="MEDIUM"))

        return actions[:5]

    # ------------------------------------------------------------------
    # Warnings (investigation-only, never developer messages)
    # ------------------------------------------------------------------
    @classmethod
    def _build_warnings(cls, context: Any) -> List[str]:
        safe_warnings: List[str] = []
        for w in getattr(context, "warnings", []):
            text = str(w)
            if cls._is_safe(text):
                safe_warnings.append(text)

        # Hallucination guard alert
        if not getattr(context, "hallucination_safe", True):
            safe_warnings.insert(
                0,
                "Some information could not be independently verified. "
                "Please cross-reference before taking action."
            )

        return safe_warnings[:5]

    # ------------------------------------------------------------------
    # Main build
    # ------------------------------------------------------------------
    @classmethod
    def build(cls, context: Any) -> OfficerReport:
        return OfficerReport(
            executive_summary=cls._build_summary(context),
            fir_details=cls._build_fir_detail(context),
            people=cls._build_people(context),
            evidence=cls._build_evidence(context),
            related_cases=cls._build_related(context),
            timeline=cls._build_timeline(context),
            ai_findings=cls._build_findings(context),
            risk=cls._build_risk(context),
            recommended_actions=cls._build_recommendations(context),
            warnings=cls._build_warnings(context),
        )


# ---------------------------------------------------------------------------
# ResponseFormatter  — top-level class; composes the final markdown string
# ---------------------------------------------------------------------------

class ResponseFormatter:
    """
    Public API.

    Usage::

        from app.ai.response_formatter import ResponseFormatter
        formatted_markdown = ResponseFormatter.format(context)
    """

    @staticmethod
    def format(context: Any, mode: str = "officer") -> str:
        """
        Parameters
        ----------
        context : ExecutionContext
            The fully-populated pipeline context after all stages have run.
        mode : str
            "officer"  → Clean, concise, professional (default, production).
            "developer"→ Returns a debug dump (NEVER use in production).

        Returns
        -------
        str  — Formatted markdown string ready for the UI.
        """
        if mode == "developer":
            # Raw developer dump — internal use only
            return ResponseFormatter._developer_dump(context)

        report = OfficerReportBuilder.build(context)
        return ResponseFormatter._render(report)

    @staticmethod
    def format_comparison(context: Any, f1: dict, f2: dict) -> str:
        comp = []
        comp.append("CASE COMPARISON")
        comp.append("===============")
        
        comp.append("• Crime Number:")
        comp.append(f"  - Case 1: {f1.get('crime_no') or 'Unknown'}")
        comp.append(f"  - Case 2: {f2.get('crime_no') or 'Unknown'}")
        
        comp.append("• Crime Type:")
        comp.append(f"  - Case 1: {f1.get('crime_category') or f1.get('crime_head') or 'Unknown'}")
        comp.append(f"  - Case 2: {f2.get('crime_category') or f2.get('crime_head') or 'Unknown'}")
        
        comp.append("• District:")
        comp.append(f"  - Case 1: {f1.get('district_name') or f1.get('district') or 'Unknown'}")
        comp.append(f"  - Case 2: {f2.get('district_name') or f2.get('district') or 'Unknown'}")
        
        comp.append("• Police Station:")
        comp.append(f"  - Case 1: {f1.get('police_station_name') or f1.get('police_station') or 'Unknown'}")
        comp.append(f"  - Case 2: {f2.get('police_station_name') or f2.get('police_station') or 'Unknown'}")
        
        comp.append("• Status:")
        comp.append(f"  - Case 1: {f1.get('status_name') or f1.get('status') or 'Unknown'}")
        comp.append(f"  - Case 2: {f2.get('status_name') or f2.get('status') or 'Unknown'}")
        
        comp.append("• Registration Date:")
        comp.append(f"  - Case 1: {f1.get('crime_registered_date') or f1.get('date') or 'Unknown'}")
        comp.append(f"  - Case 2: {f2.get('crime_registered_date') or f2.get('date') or 'Unknown'}")
        
        a1 = ", ".join(f1.get('accused_names', [])) if f1.get('accused_names') else f1.get('accused_name', 'Unknown')
        a2 = ", ".join(f2.get('accused_names', [])) if f2.get('accused_names') else f2.get('accused_name', 'Unknown')
        comp.append("• Accused:")
        comp.append(f"  - Case 1: {a1}")
        comp.append(f"  - Case 2: {a2}")
        
        v1 = ", ".join(f1.get('victim_names', [])) if f1.get('victim_names') else f1.get('victim_name', 'Unknown')
        v2 = ", ".join(f2.get('victim_names', [])) if f2.get('victim_names') else f2.get('victim_name', 'Unknown')
        comp.append("• Victims:")
        comp.append(f"  - Case 1: {v1}")
        comp.append(f"  - Case 2: {v2}")
        
        return "\n".join(comp)

    # ------------------------------------------------------------------
    @staticmethod
    def _render(report: OfficerReport) -> str:
        sections: List[str] = []

        s = SummaryRenderer.render(report)
        if s:
            sections.append(s)

        # People Involved
        s = EntityRenderer.render(report.people)
        if s:
            sections.append(s)

        # Verified Evidence
        s = EvidenceRenderer.render(report.evidence)
        if s:
            sections.append(s)

        # Investigation Timeline
        s = TimelineRenderer.render(report.timeline)
        if s:
            sections.append(s)

        # AI Findings
        s = FindingsRenderer.render(report.ai_findings)
        if s:
            sections.append(s)

        # Risk Assessment
        s = RiskRenderer.render(report.risk)
        if s:
            sections.append(s)

        # Recommended Actions
        s = RecommendationRenderer.render(report.recommended_actions)
        if s:
            sections.append(s)

        # Related Cases
        s = CorrelationRenderer.render(report.related_cases)
        if s:
            sections.append(s)

        # Warnings
        s = WarningRenderer.render(report.warnings)
        if s:
            sections.append(s)

        divider = "\n\n────────────────────────────────────────────\n\n"
        return divider.join(sections).strip() + "\n\n────────────────────────────────────────────"

    # ------------------------------------------------------------------
    @staticmethod
    def _developer_dump(context: Any) -> str:
        """
        Raw verbose output for internal debugging.
        This mode MUST NEVER be exposed to officers or in production.
        """
        lines = ["[DEVELOPER MODE — INTERNAL ONLY]\n"]
        for attr in [
            "intent", "raw_query", "resolved_entities", "search_result",
            "confidence", "reasoning_result", "confidence_metrics",
            "evidence_correlation", "timeline_report", "knowledge_graph_report",
            "decision_support_report", "similarity_report", "multi_agent_report",
            "predictive_report", "warnings", "executed_stages", "skipped_stages",
            "hallucination_violations",
        ]:
            val = getattr(context, attr, None)
            lines.append(f"**{attr}:** `{repr(val)}`\n")
        return "\n".join(lines)
