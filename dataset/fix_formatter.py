with open('/Users/tanaysharma/Desktop/KSP-Sentinel-AI/dataset/app/ai/response_formatter.py', 'w') as f:
    f.write('''"""
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

        # Build the structured brief from context
        brief = InvestigationBriefBuilder.build(context)
        return ResponseFormatter._render(brief)

    @staticmethod
    def _render(brief: InvestigationBrief) -> str:
        sections = []

        # 1. Executive Summary
        if brief.executive_summary:
            sections.append(f"📋 EXECUTIVE SUMMARY\\n\\n{brief.executive_summary}")

        # 2. Investigation Priority
        if brief.investigation_priority:
            prio = brief.investigation_priority
            emoji = {"IMMEDIATE": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(prio.level.upper(), "⚪")
            text = f"🚨 INVESTIGATION PRIORITY\\n\\nPriority : {emoji} {prio.level.upper()}\\n\\nReason : {prio.reason}"
            sections.append(text)

        # 3. Investigation Progress
        if brief.investigation_progress:
            prog = brief.investigation_progress
            text = (
                "📈 INVESTIGATION PROGRESS\\n\\n"
                f"Current Stage : {prog.current_stage}\\n\\n"
                f"Completion    : {prog.completion_pct}%\\n\\n"
                f"Next Stage    : {prog.next_stage}"
            )
            sections.append(text)

        # 4. Evidence Summary (Collected vs Missing Critical)
        evidence_text = "🔍 EVIDENCE SUMMARY\\n\\n"
        if brief.collected_evidence:
            evidence_text += "**Collected Evidence**\\n\\n"
            for e in brief.collected_evidence:
                evidence_text += f"• **{e.label}**\\n  Status: {e.verification_status} | Strength: {e.strength} | Source: {e.source}\\n\\n"
        else:
            evidence_text += "**Collected Evidence**\\n\\nNo verified evidence collected.\\n\\n"

        if brief.missing_critical_evidence:
            evidence_text += "**Missing Critical Evidence**\\n\\n"
            for e in brief.missing_critical_evidence:
                evidence_text += f"• **{e.label}**\\n  Status: {e.verification_status} | Target Source: {e.source}\\n\\n"
        
        sections.append(evidence_text.strip())
        
        # 4.5 Correlated Evidence
        if hasattr(brief, 'correlated_evidence') and brief.correlated_evidence:
            corr_text = "🔗 EVIDENCE CORRELATION\\n\\n" + "\\n".join(f"• {c}" for c in brief.correlated_evidence)
            sections.append(corr_text)
            
        # 4.6 Contradictions
        if hasattr(brief, 'contradictions') and brief.contradictions:
            contra_text = "⚠️ CONTRADICTION ANALYSIS\\n\\n" + "\\n".join(f"• {c.description}" for c in brief.contradictions)
            sections.append(contra_text)

        # 5. Key Findings
        if brief.key_findings:
            findings_text = "🧠 KEY FINDINGS\\n\\n" + "\\n".join(f"• {f}" for f in brief.key_findings)
            sections.append(findings_text)

        # 6. Risk Assessment
        if brief.risk_assessment:
            risk_text = "⚠️ RISK ASSESSMENT\\n\\n"
            for r in brief.risk_assessment:
                emoji = {"IMMEDIATE": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(r.level.upper(), "⚪")
                ev_used = ", ".join(r.evidence_used) if r.evidence_used else "System Analysis"
                risk_text += f"**Level:** {emoji} {r.level.upper()}\\n**Reason:** {r.reason}\\n**Evidence Used:** {ev_used}\\n\\n"
            sections.append(risk_text.strip())

        # 7. Recommendations
        if brief.recommendations:
            rec_text = "✅ RECOMMENDED ACTIONS\\n\\n"
            for i, rec in enumerate(brief.recommendations, 1):
                conf = getattr(rec, "confidence", 0.75)
                conf_pct = int(conf * 100)
                rec_text += f"**{i}. {rec.text}**\\nPriority: {rec.priority}\\nConfidence: {conf_pct}%\\nReason: {rec.reason}\\nSupporting Evidence: {', '.join(rec.supporting_evidence)}\\n\\n"
            sections.append(rec_text.strip())
            
        # 7.1 Officer Insights
        if hasattr(brief, 'officer_insights') and brief.officer_insights:
            insight_text = "🕵️ OFFICER INSIGHTS\\n\\n"
            for o in brief.officer_insights:
                insight_text += f"**Insight:** {o.insight}\\n**Reason:** {o.reason}\\n**Supporting Evidence:** {', '.join(o.supporting_evidence)}\\n**Investigation Impact:** {o.investigation_impact}\\n\\n"
            sections.append(insight_text.strip())
            
        # 7.2 Investigation Conclusion
        if hasattr(brief, 'investigation_conclusion') and brief.investigation_conclusion:
            conc = brief.investigation_conclusion
            conc_text = f"⚖️ INVESTIGATION CONCLUSION\\n\\n**Case Strength:** {conc.case_strength}\\n**Reason:** {conc.reason}\\n**Outstanding Tasks:** {', '.join(conc.outstanding_tasks)}\\n**Recommended Next Action:** {conc.recommended_next_action}\\n**Supporting Evidence:** {', '.join(conc.supporting_evidence)}"
            sections.append(conc_text)
            
        # 7.3 Investigation Limitations
        if hasattr(brief, 'investigation_limitations') and brief.investigation_limitations:
            lim_text = "🛑 INVESTIGATION LIMITATIONS\\n\\n"
            for lim in brief.investigation_limitations:
                lim_text += f"**{lim.limitation_type}:** {lim.description}\\n**Impact:** {lim.impact}\\n\\n"
            sections.append(lim_text.strip())

        # 8. Confidence & Explanation
        if brief.confidence_explanation:
            conf = brief.confidence_explanation
            conf_text = f"📊 CONFIDENCE METRICS\\n\\n**Overall Confidence:** {int(conf.score * 100)}%\\n\\n"
            if conf.positive_factors:
                conf_text += "**Positive Factors:**\\n" + "\\n".join(f"• {f}" for f in conf.positive_factors) + "\\n\\n"
            if conf.negative_factors:
                conf_text += "**Negative Factors:**\\n" + "\\n".join(f"• {f}" for f in conf.negative_factors) + "\\n\\n"
            conf_text += f"**Calculation Summary:**\\n{conf.calculation_summary}"
            sections.append(conf_text.strip())

        divider = "\\n\\n────────────────────────────────────────────\\n\\n"
        return divider.join(sections).strip() + "\\n\\n────────────────────────────────────────────"

    @staticmethod
    def format_comparison(context: Any, f1: dict, f2: dict) -> str:
        # Standard comparison logic remains unchanged
        comp = []
        comp.append("CASE COMPARISON")
        comp.append("===============")
        comp.append("• Crime Number:")
        comp.append(f"  - Case 1: {f1.get('crime_no') or 'Unknown'}")
        comp.append(f"  - Case 2: {f2.get('crime_no') or 'Unknown'}")
        comp.append("• Crime Type:")
        comp.append(f"  - Case 1: {f1.get('crime_category') or f1.get('crime_head') or 'Unknown'}")
        comp.append(f"  - Case 2: {f2.get('crime_category') or f2.get('crime_head') or 'Unknown'}")
        comp.append("• Status:")
        comp.append(f"  - Case 1: {f1.get('status_name') or f1.get('status') or 'Unknown'}")
        comp.append(f"  - Case 2: {f2.get('status_name') or f2.get('status') or 'Unknown'}")
        return "\\n".join(comp)

    @staticmethod
    def _developer_dump(context: Any) -> str:
        return "[DEVELOPER MODE — INTERNAL ONLY]\\n" + str(context)
''')
