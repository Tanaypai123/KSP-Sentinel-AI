"""
response_formatter.py
=====================
Enterprise Response Formatter for KSP Sentinel AI.

Transforms the structured InvestigationBrief into a clean, 
professional, officer-friendly markdown report.
"""

from __future__ import annotations

import logging
from typing import Any

from app.ai.investigation_brief_builder import InvestigationBriefBuilder, InvestigationBrief

logger = logging.getLogger(__name__)

class ResponseFormatter:
    """
    Public API to format pipeline context into Officer Briefing Style.
    """

    @staticmethod
    def format(context: Any, mode: str = "officer") -> str:
        if mode == "developer":
            return ResponseFormatter._developer_dump(context)

        # Timeline First/Last Question Intercept
        q_low = getattr(context, "raw_query", "").lower()
        timeline_report = getattr(context, "timeline_report", None)
        events = timeline_report.get("events") if timeline_report else None
        
        # Timeline guard: only intercept for FIR/case-specific timeline queries, not for analytics like REPEAT_OFFENDERS
        intent_val = getattr(context, "intent", "") or ""
        is_timeline_eligible = intent_val in {"FIR_LOOKUP", "SEARCH_ACCUSED", "SEARCH_VICTIMS", "SEARCH_OFFICER", "SEARCH_LOCATION"}
        
        if is_timeline_eligible and events:
            import re
            if re.search(r'\b(first|earliest|start|begin|last|latest|end|conclude)\b', q_low):
                # Exclude placeholder/unavailable timestamps
                invalid_ts = {None, "", "Timestamp unavailable.", "unavailable", "unknown"}
                dated_events = [e for e in events if e.get("timestamp") and e.get("timestamp") not in invalid_ts]
                if dated_events:
                    first_ev = dated_events[0]
                    last_ev = dated_events[-1]
                    
                    if re.search(r'\b(first|earliest|start|begin)\b', q_low):
                        desc = ", ".join(first_ev.get("reason_chain", [])) or "No details available."
                        summary = (
                            f"📅 **Earliest Recorded Event (First):**\n\n"
                            f"• **Event Type:** {first_ev.get('event_type')}\n"
                            f"  **Date:** {first_ev.get('timestamp')}\n"
                            f"  **Details:** {desc}\n\n"
                            f"To view the complete chronological sequence, please refer to the Case Timeline panel."
                        )
                        return summary
                    elif re.search(r'\b(last|latest|end|conclude)\b', q_low):
                        desc = ", ".join(last_ev.get("reason_chain", [])) or "No details available."
                        summary = (
                            f"📅 **Latest Recorded Event (Last):**\n\n"
                            f"• **Event Type:** {last_ev.get('event_type')}\n"
                            f"  **Date:** {last_ev.get('timestamp')}\n"
                            f"  **Details:** {desc}\n\n"
                            f"To view the complete chronological sequence, please refer to the Case Timeline panel."
                        )
                        return summary

        # ── EXPLAIN INTERCEPT ────────────────────────────────────────────
        # "Explain recommendation", "Explain officer insight", "Explain confidence"
        # These should produce a dedicated explanation, not a generic case brief.
        if "explain" in q_low:
            explain_response = ResponseFormatter._render_explain(context, q_low)
            if explain_response:
                return explain_response

        # ── REPEAT OFFENDERS INTERCEPT ───────────────────────────────────
        if getattr(context, "intent", None) == "REPEAT_OFFENDERS":
            results = getattr(context, "search_result", [])
            lines = ["🚨 **REPEAT OFFENDER ANALYSIS**\n"]
            if not results:
                lines.append("No repeat offenders found matching the criteria.")
            else:
                for i, row in enumerate(results, 1):
                    # Data from REPEAT_OFFENDERS SQL intent
                    name = row.get("accused_name", "Unknown")
                    cases = row.get("total_cases", 0)
                    risk = row.get("risk_score", 0)
                    
                    lines.append(f"**{i}. {name}** (Risk Score: {risk})")
                    lines.append(f"   • Total Linked Cases: {cases}")
                    lines.append("")
                lines.append("_Analysis based on confirmed case linkages across the database._")
            return "\n".join(lines)

        # Build the structured brief from context
        brief = InvestigationBriefBuilder.build(context)
        return ResponseFormatter._render(brief)

    @staticmethod
    def _render(brief: InvestigationBrief) -> str:
        sections = []

        # 1. Executive Summary
        if getattr(brief, "executive_summary", None):
            sections.append(f"📋 EXECUTIVE SUMMARY\n\n{brief.executive_summary}")

        # 2. Investigation Priority
        if getattr(brief, "investigation_priority", None):
            prio = brief.investigation_priority
            emoji = {"IMMEDIATE": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(prio.level.upper(), "⚪")
            text = f"🚨 INVESTIGATION PRIORITY\n\nPriority : {emoji} {prio.level.upper()}\n\nReason : {prio.reason}"
            sections.append(text)

        # 3. Investigation Progress
        if getattr(brief, "investigation_progress", None):
            prog = brief.investigation_progress
            text = f"📈 INVESTIGATION PROGRESS\n\nOverall Completion: {prog.completion_pct}%\n\n"
            for t in prog.tasks:
                emoji = "✅" if t.status == "Completed" else "⏳" if t.status == "Pending" else "❌"
                text += f"• {emoji} {t.task}: {t.status}\n"
            sections.append(text.strip())

        # 4. Evidence Summary (Facts Only)
        evidence_text = "🔍 EVIDENCE SUMMARY\n\n"
        if getattr(brief, "collected_evidence", None):
            evidence_text += "**Collected Evidence**\n\n"
            for e in brief.collected_evidence:
                evidence_text += f"• **{e.label}**\n  Status: {e.verification_status} | Strength: {e.strength} | Source: {e.source}\n\n"
        else:
            evidence_text += "**Collected Evidence**\n\nNo verified evidence collected.\n\n"

        if getattr(brief, "missing_critical_evidence", None):
            evidence_text += "**Missing Critical Evidence**\n\n"
            for e in brief.missing_critical_evidence:
                evidence_text += f"• **{e.label}**\n  Status: {e.verification_status} | Target Source: {e.source}\n\n"
        
        sections.append(evidence_text.strip())
        
        # 4.5 Correlated Evidence
        if getattr(brief, 'correlated_evidence', None):
            corr_text = "🔗 EVIDENCE CORRELATION\n\n" + "\n".join(f"• {c}" for c in brief.correlated_evidence)
            sections.append(corr_text)
            
        # 4.6 Contradictions
        if getattr(brief, 'contradictions', None):
            contra_text = "⚠️ CONTRADICTION ANALYSIS\n\n" + "\n".join(f"• {c.description}" for c in brief.contradictions)
            sections.append(contra_text)

        # 5. Risk Assessment (Consequences Only)
        if getattr(brief, "risk_assessment", None):
            risk_text = "⚠️ RISK ASSESSMENT\n\n"
            for r in brief.risk_assessment:
                emoji = {"IMMEDIATE": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(r.level.upper(), "⚪")
                ev_used = ", ".join(r.evidence_used) if r.evidence_used else "System Analysis"
                risk_text += f"**Level:** {emoji} {r.level.upper()}\n**Reason:** {r.reason}\n**Evidence Used:** {ev_used}\n\n"
            sections.append(risk_text.strip())

        # 6. Recommendations (Actions & Chains)
        if getattr(brief, "recommendations", None):
            rec_text = "✅ RECOMMENDED ACTIONS\n\n"
            for i, rec in enumerate(brief.recommendations, 1):
                conf_pct = int(rec.confidence * 100)
                rec_text += f"**{i}. {rec.recommendation}**\n"
                rec_text += f"Priority: {rec.priority}\n"
                rec_text += f"Dependencies: {', '.join(rec.dependencies)}\n"
                rec_text += f"Confidence Gain: +{conf_pct}%\n\n"
                rec_text += f"**Reasoning Chain:**\n"
                rec_text += f"  Evidence: {rec.evidence}\n"
                rec_text += f"  ↓\n"
                rec_text += f"  Reasoning: {rec.reason}\n"
                rec_text += f"  ↓\n"
                rec_text += f"  Risk: {rec.risk}\n"
                rec_text += f"  ↓\n"
                rec_text += f"  Recommendation: {rec.recommendation}\n"
                rec_text += f"  ↓\n"
                rec_text += f"  Expected Impact: {rec.expected_impact}\n\n"
            sections.append(rec_text.strip())
            
        # 7. Officer Insights
        if getattr(brief, 'officer_insights', None):
            insight_text = "🕵️ OFFICER INSIGHTS\n\n"
            for o in brief.officer_insights:
                insight_text += f"**Insight:** {o.insight}\n**Why:** {o.reason}\n**Supporting Evidence:** {', '.join(o.supporting_evidence)}\n**Investigation Impact:** {o.investigation_impact}\n\n"
            sections.append(insight_text.strip())
            
        # 8. Investigation Conclusion
        if getattr(brief, 'investigation_conclusion', None):
            conc = brief.investigation_conclusion
            conc_text = (
                f"⚖️ INVESTIGATION CONCLUSION\n\n"
                f"**Overall Investigation Readiness:** {conc.overall_investigation_readiness}\n"
                f"**Evidence Strength:** {conc.evidence_strength}\n"
                f"**Strongest Evidence:** {conc.strongest_evidence}\n"
                f"**Weakest Evidence:** {conc.weakest_evidence}\n"
                f"**Probability of Successful Prosecution:** {conc.probability_of_successful_prosecution}\n"
                f"**Remaining Gaps:** {', '.join(conc.remaining_gaps)}\n"
                f"**Critical Next Step:** {conc.critical_next_step}\n"
                f"**Supporting Records:** {', '.join(conc.supporting_evidence)}"
            )
            sections.append(conc_text)
            
        # 9. Investigation Limitations
        if getattr(brief, 'investigation_limitations', None):
            lim_text = "🛑 INVESTIGATION LIMITATIONS\n\n"
            for lim in brief.investigation_limitations:
                lim_text += f"**{lim.limitation_type}:** {lim.description}\n**Impact:** {lim.impact}\n\n"
            sections.append(lim_text.strip())

        # 10. Confidence & Explanation
        if getattr(brief, "confidence_explanation", None):
            conf = brief.confidence_explanation
            conf_text = f"📊 CONFIDENCE METRICS\n\n**Final Confidence:** {int(conf.score * 100)}%\n\n"
            if conf.positive_factors:
                conf_text += "**Positive Factors:**\n" + "\n".join(f"• {f}" for f in conf.positive_factors) + "\n\n"
            if conf.negative_factors:
                conf_text += "**Negative Factors:**\n" + "\n".join(f"• {f}" for f in conf.negative_factors) + "\n\n"
            conf_text += f"**Final Formula:**\n{conf.calculation_summary}"
            sections.append(conf_text.strip())

        divider = "\n\n────────────────────────────────────────────\n\n"
        return divider.join(sections).strip() + "\n\n────────────────────────────────────────────"

    @staticmethod
    def format_comparison(context: Any, f1: dict, f2: dict) -> str:
        comp = []
        comp.append("📊 CASE COMPARISON REPORT")
        comp.append("=========================")
        comp.append("")
        
        c1 = f1.get('crime_no') or f1.get('fir_no') or 'Unknown'
        c2 = f2.get('crime_no') or f2.get('fir_no') or 'Unknown'
        comp.append(f"### Cases: **{c1}** vs **{c2}**")
        comp.append("")

        def add_comparison_field(label, key1, key2, dict1, dict2, is_list=False):
            if is_list:
                v1 = ", ".join(dict1.get(key1, [])) if dict1.get(key1) else "None"
                v2 = ", ".join(dict2.get(key2, [])) if dict2.get(key2) else "None"
            else:
                v1 = dict1.get(key1) or "Unknown"
                v2 = dict2.get(key2) or "Unknown"
            
            comp.append(f"• **{label}**:")
            comp.append(f"  - **{c1}**: {v1}")
            comp.append(f"  - **{c2}**: {v2}")
            comp.append("")

        add_comparison_field("Crime Category", "crime_category", "crime_category", f1, f2)
        add_comparison_field("Registration Date", "crime_registered_date", "crime_registered_date", f1, f2)
        add_comparison_field("District", "district_name", "district_name", f1, f2)
        add_comparison_field("Police Station", "police_station_name", "police_station_name", f1, f2)
        add_comparison_field("Investigating Officer", "investigating_officer", "investigating_officer", f1, f2)
        add_comparison_field("Accused Names", "accused_names", "accused_names", f1, f2, is_list=True)
        add_comparison_field("Victim Names", "victim_names", "victim_names", f1, f2, is_list=True)
        add_comparison_field("Case Status", "status_name", "status_name", f1, f2)
        
        # Brief facts summary comparison
        f1_facts = f1.get('brief_facts') or 'No facts registered.'
        f2_facts = f2.get('brief_facts') or 'No facts registered.'
        comp.append("• **Brief Facts / Modus Operandi (MO)**:")
        comp.append(f"  - **{c1}**: {f1_facts}")
        comp.append(f"  - **{c2}**: {f2_facts}")
        comp.append("")

        return "\n".join(comp)

    @staticmethod
    def _render_explain(context: Any, q_low: str) -> str:
        """
        Renders a human-readable explanation for explain-type follow-up queries.
        Topics: recommendation, confidence, officer insight, risk, evidence, findings.
        """
        active_fir = None
        if getattr(context, "conversation_state", None):
            active_fir = getattr(context.conversation_state, "active_fir", None)
        fir_no = (active_fir or {}).get("crime_no") or (active_fir or {}).get("case_no") or "Current Case"

        # Build the brief to get access to all structured data
        brief = InvestigationBriefBuilder.build(context)
        reasoning_result = getattr(context, "reasoning_result", None) or {}

        # ── RECOMMENDATION EXPLAIN ───────────────────────────────────────
        if any(x in q_low for x in ["recommendation", "suggest", "action"]):
            recs = getattr(brief, "recommendations", []) or []
            lines = [f"💡 **RECOMMENDATION EXPLANATION — {fir_no}**\n"]
            if recs:
                chain = reasoning_result.get("reason_chain", [])
                for i, rec in enumerate(recs, 1):
                    label = getattr(rec, "action", None) or str(rec)
                    lines.append(f"**{i}. {label}**")
                    priority = getattr(rec, "priority", None)
                    if priority:
                        lines.append(f"   _Priority_: {priority}")
                    evidence = getattr(rec, "evidence_basis", None)
                    if evidence:
                        lines.append(f"   _Evidence Basis_: {evidence}")
                    if chain and i <= len(chain):
                        lines.append(f"   _Reasoning_: {chain[i-1]}")
                    lines.append("")
                lines.append("_All recommendations are generated from verified database records only._")
            else:
                lines.append("No specific recommendations have been generated for this case yet.")
                lines.append("Recommendations are produced after evidence analysis. Try opening the full case report first.")
            return "\n".join(lines)

        # ── CONFIDENCE EXPLAIN ───────────────────────────────────────────
        if any(x in q_low for x in ["confidence", "score", "certainty", "accuracy"]):
            conf = getattr(context, "confidence", {}) or {}
            final = conf.get("final", 0.5)
            conf_pct = int(final * 100)
            lines = [f"📊 **CONFIDENCE SCORE EXPLANATION — {fir_no}**\n"]
            lines.append(f"**Final Confidence: {conf_pct}%**\n")
            lines.append("**Score Breakdown:**\n")
            conf_metrics = getattr(context, "confidence_metrics", {}) or {}
            if conf_metrics:
                for k, v in conf_metrics.items():
                    if k != "final":
                        lines.append(f"• **{k}**: {v}")
            else:
                intent_conf = getattr(getattr(context, "intent_result", None), "confidence", 0.5)
                lines.append(f"• Intent Confidence: {int(intent_conf * 100)}%")
                lines.append(f"• Evidence Records Found: {len(getattr(context, 'search_result', []) or [])}")
                lines.append(f"• Hallucination Safe: {'Yes' if getattr(context, 'hallucination_safe', True) else 'No'}")
            chain = reasoning_result.get("reason_chain", [])
            if chain:
                lines.append("\n**Reasoning Path:**")
                for step in chain:
                    lines.append(f"  - {step}")
            lines.append(f"\n**Conclusion**: {reasoning_result.get('conclusion', 'Standard case processed normally.')}")
            return "\n".join(lines)

        # ── OFFICER INSIGHT EXPLAIN ──────────────────────────────────────
        if any(x in q_low for x in ["officer", "insight", "io", "investigating"]):
            insights = getattr(brief, "officer_insights", []) or []
            lines = [f"👮 **OFFICER INSIGHT EXPLANATION — {fir_no}**\n"]
            if insights:
                for ins in insights:
                    label = getattr(ins, "insight", None) or str(ins)
                    source = getattr(ins, "source", None)
                    lines.append(f"• {label}")
                    if source:
                        lines.append(f"  _Source_: {source}")
                    lines.append("")
            else:
                lines.append("Officer insights are derived from case-specific evidence patterns:")
                chain = reasoning_result.get("reason_chain", [])
                for step in (chain or ["No reasoning chain available."]):
                    lines.append(f"  - {step}")
            lines.append("\n_Source: Investigation Reasoning Engine (deterministic logic, no AI hallucination)_")
            return "\n".join(lines)

        # ── RISK / PRIORITY EXPLAIN ──────────────────────────────────────
        if any(x in q_low for x in ["risk", "danger", "threat", "priority", "limitation"]):
            risk_flags = getattr(brief, "risk_flags", []) or []
            lines = [f"⚠️ **RISK & LIMITATION EXPLANATION — {fir_no}**\n"]
            if risk_flags:
                for flag in risk_flags:
                    level = getattr(flag, "level", "?")
                    reason = getattr(flag, "reason", "")
                    evidence = getattr(flag, "evidence_used", "")
                    emoji = {"IMMEDIATE": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(level.upper(), "⚪")
                    lines.append(f"• **{emoji} {level}** — {reason}")
                    if evidence:
                        lines.append(f"  _Evidence_: {evidence}")
                    lines.append("")
            else:
                lines.append("Risk assessment is based on:")
                lines.append("• Case gravity and crime category")
                lines.append("• Missing critical evidence (weapon, CDR, witnesses)")
                lines.append("• Timeline completeness and arrest status")
                chain = reasoning_result.get("reason_chain", [])
                if chain:
                    lines.append("\n**Supporting Reasoning:**")
                    for step in chain:
                        lines.append(f"  - {step}")
            return "\n".join(lines)

        # ── EVIDENCE EXPLAIN ─────────────────────────────────────────────
        if any(x in q_low for x in ["evidence", "finding", "collected", "forensic", "witness"]):
            collected = getattr(brief, "collected_evidence", []) or []
            missing = getattr(brief, "missing_critical_evidence", []) or []
            lines = [f"🔍 **EVIDENCE EXPLANATION — {fir_no}**\n"]
            if collected:
                lines.append("**Collected Evidence:**\n")
                for ev in collected:
                    label = getattr(ev, "label", str(ev))
                    status = getattr(ev, "verification_status", "")
                    strength = getattr(ev, "strength", "")
                    lines.append(f"• **{label}** — Status: {status} | Strength: {strength}")
            else:
                lines.append("No verified evidence records found for this case.")
            if missing:
                lines.append("\n**Missing Critical Evidence:**\n")
                for ev in missing:
                    label = getattr(ev, "label", str(ev))
                    lines.append(f"• ❌ {label}")
            chain = reasoning_result.get("reason_chain", [])
            if chain:
                lines.append("\n**Investigation Reasoning Chain:**\n")
                for step in chain:
                    lines.append(f"• {step}")
            lines.append("\n_All evidence claims are traced to verified database records only._")
            return "\n".join(lines)

        # No specific topic matched — fall through to normal brief
        return ""

    @staticmethod
    def _developer_dump(context: Any) -> str:
        return "[DEVELOPER MODE — INTERNAL ONLY]\n" + str(context)
