with open('/Users/tanaysharma/Desktop/KSP-Sentinel-AI/dataset/app/ai/response_formatter.py', 'r') as f:
    content = f.read()

import re

# We will completely rewrite `_render`
new_render = """    @staticmethod
    def _render(brief: InvestigationBrief) -> str:
        sections = []

        # 1. Executive Summary
        if getattr(brief, "executive_summary", None):
            sections.append(f"📋 EXECUTIVE SUMMARY\\n\\n{brief.executive_summary}")

        # 2. Investigation Priority
        if getattr(brief, "investigation_priority", None):
            prio = brief.investigation_priority
            emoji = {"IMMEDIATE": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(prio.level.upper(), "⚪")
            text = f"🚨 INVESTIGATION PRIORITY\\n\\nPriority : {emoji} {prio.level.upper()}\\n\\nReason : {prio.reason}"
            sections.append(text)

        # 3. Investigation Progress
        if getattr(brief, "investigation_progress", None):
            prog = brief.investigation_progress
            text = f"📈 INVESTIGATION PROGRESS\\n\\nOverall Completion: {prog.completion_pct}%\\n\\n"
            for t in prog.tasks:
                emoji = "✅" if t.status == "Completed" else "⏳" if t.status == "Pending" else "❌"
                text += f"• {emoji} {t.task}: {t.status}\\n"
            sections.append(text.strip())

        # 4. Evidence Summary (Facts Only)
        evidence_text = "🔍 EVIDENCE SUMMARY\\n\\n"
        if getattr(brief, "collected_evidence", None):
            evidence_text += "**Collected Evidence**\\n\\n"
            for e in brief.collected_evidence:
                evidence_text += f"• **{e.label}**\\n  Status: {e.verification_status} | Strength: {e.strength} | Source: {e.source}\\n\\n"
        else:
            evidence_text += "**Collected Evidence**\\n\\nNo verified evidence collected.\\n\\n"

        if getattr(brief, "missing_critical_evidence", None):
            evidence_text += "**Missing Critical Evidence**\\n\\n"
            for e in brief.missing_critical_evidence:
                evidence_text += f"• **{e.label}**\\n  Status: {e.verification_status} | Target Source: {e.source}\\n\\n"
        
        sections.append(evidence_text.strip())
        
        # 4.5 Correlated Evidence
        if getattr(brief, 'correlated_evidence', None):
            corr_text = "🔗 EVIDENCE CORRELATION\\n\\n" + "\\n".join(f"• {c}" for c in brief.correlated_evidence)
            sections.append(corr_text)
            
        # 4.6 Contradictions
        if getattr(brief, 'contradictions', None):
            contra_text = "⚠️ CONTRADICTION ANALYSIS\\n\\n" + "\\n".join(f"• {c.description}" for c in brief.contradictions)
            sections.append(contra_text)

        # 5. Risk Assessment (Consequences Only)
        if getattr(brief, "risk_assessment", None):
            risk_text = "⚠️ RISK ASSESSMENT\\n\\n"
            for r in brief.risk_assessment:
                emoji = {"IMMEDIATE": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(r.level.upper(), "⚪")
                ev_used = ", ".join(r.evidence_used) if r.evidence_used else "System Analysis"
                risk_text += f"**Level:** {emoji} {r.level.upper()}\\n**Reason:** {r.reason}\\n**Evidence Used:** {ev_used}\\n\\n"
            sections.append(risk_text.strip())

        # 6. Recommendations (Actions & Chains)
        if getattr(brief, "recommendations", None):
            rec_text = "✅ RECOMMENDED ACTIONS\\n\\n"
            for i, rec in enumerate(brief.recommendations, 1):
                conf_pct = int(rec.confidence * 100)
                rec_text += f"**{i}. {rec.recommendation}**\\n"
                rec_text += f"Priority: {rec.priority}\\n"
                rec_text += f"Dependencies: {', '.join(rec.dependencies)}\\n"
                rec_text += f"Confidence Gain: +{conf_pct}%\\n\\n"
                rec_text += f"**Reasoning Chain:**\\n"
                rec_text += f"  Evidence: {rec.evidence}\\n"
                rec_text += f"  ↓\\n"
                rec_text += f"  Reasoning: {rec.reason}\\n"
                rec_text += f"  ↓\\n"
                rec_text += f"  Risk: {rec.risk}\\n"
                rec_text += f"  ↓\\n"
                rec_text += f"  Recommendation: {rec.recommendation}\\n"
                rec_text += f"  ↓\\n"
                rec_text += f"  Expected Impact: {rec.expected_impact}\\n\\n"
            sections.append(rec_text.strip())
            
        # 7. Officer Insights
        if getattr(brief, 'officer_insights', None):
            insight_text = "🕵️ OFFICER INSIGHTS\\n\\n"
            for o in brief.officer_insights:
                insight_text += f"**Insight:** {o.insight}\\n**Why:** {o.reason}\\n**Supporting Evidence:** {', '.join(o.supporting_evidence)}\\n**Investigation Impact:** {o.investigation_impact}\\n\\n"
            sections.append(insight_text.strip())
            
        # 8. Investigation Conclusion
        if getattr(brief, 'investigation_conclusion', None):
            conc = brief.investigation_conclusion
            conc_text = (
                f"⚖️ INVESTIGATION CONCLUSION\\n\\n"
                f"**Overall Investigation Readiness:** {conc.overall_investigation_readiness}\\n"
                f"**Evidence Strength:** {conc.evidence_strength}\\n"
                f"**Strongest Evidence:** {conc.strongest_evidence}\\n"
                f"**Weakest Evidence:** {conc.weakest_evidence}\\n"
                f"**Probability of Successful Prosecution:** {conc.probability_of_successful_prosecution}\\n"
                f"**Remaining Gaps:** {', '.join(conc.remaining_gaps)}\\n"
                f"**Critical Next Step:** {conc.critical_next_step}\\n"
                f"**Supporting Records:** {', '.join(conc.supporting_evidence)}"
            )
            sections.append(conc_text)
            
        # 9. Investigation Limitations
        if getattr(brief, 'investigation_limitations', None):
            lim_text = "🛑 INVESTIGATION LIMITATIONS\\n\\n"
            for lim in brief.investigation_limitations:
                lim_text += f"**{lim.limitation_type}:** {lim.description}\\n**Impact:** {lim.impact}\\n\\n"
            sections.append(lim_text.strip())

        # 10. Confidence & Explanation
        if getattr(brief, "confidence_explanation", None):
            conf = brief.confidence_explanation
            conf_text = f"📊 CONFIDENCE METRICS\\n\\n**Final Confidence:** {int(conf.score * 100)}%\\n\\n"
            if conf.positive_factors:
                conf_text += "**Positive Factors:**\\n" + "\\n".join(f"• {f}" for f in conf.positive_factors) + "\\n\\n"
            if conf.negative_factors:
                conf_text += "**Negative Factors:**\\n" + "\\n".join(f"• {f}" for f in conf.negative_factors) + "\\n\\n"
            conf_text += f"**Final Formula:**\\n{conf.calculation_summary}"
            sections.append(conf_text.strip())

        divider = "\\n\\n────────────────────────────────────────────\\n\\n"
        return divider.join(sections).strip() + "\\n\\n────────────────────────────────────────────\"\"\"
        """

content = re.sub(r"    @staticmethod\n    def _render\(brief: InvestigationBrief\) -> str:.*?    @staticmethod\n    def format_comparison", new_render + "\n    @staticmethod\n    def format_comparison", content, flags=re.DOTALL)

with open('/Users/tanaysharma/Desktop/KSP-Sentinel-AI/dataset/app/ai/response_formatter.py', 'w') as f:
    f.write(content)
