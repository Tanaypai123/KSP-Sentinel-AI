import logging
from typing import Any

logger = logging.getLogger(__name__)

class ReportConsistencyValidator:
    """
    Acts as a global validation layer ensuring no logical contradictions 
    exist across Evidence, Risks, and Insights.
    """

    @staticmethod
    def validate(brief: Any, context: Any) -> Any:
        # Check ground truth
        has_witness = any("Witness" in e.label for e in brief.collected_evidence) if getattr(brief, "collected_evidence", None) else False
        has_weapon = any("Weapon" in e.label for e in brief.collected_evidence) if getattr(brief, "collected_evidence", None) else False
        has_vehicle = any("Vehicle" in e.label for e in brief.collected_evidence) if getattr(brief, "collected_evidence", None) else False

        # 1. Validate Risk Assessment against Evidence
        if getattr(brief, "risk_assessment", None):
            valid_risks = []
            for r in brief.risk_assessment:
                # If risk says "No witness" but we have a witness, drop it
                if "No witness" in r.reason and has_witness:
                    continue
                if "No vehicle" in r.reason and has_vehicle:
                    continue
                if "Weapon not recovered" in r.reason and has_weapon:
                    continue
                valid_risks.append(r)
            brief.risk_assessment = valid_risks

        # 2. Validate Officer Insights
        if getattr(brief, "officer_insights", None):
            valid_insights = []
            for i in brief.officer_insights:
                if "Witness testimony requires independent corroboration" in i.insight and not has_witness:
                    continue
                if "Physical recovery corroborates" in i.insight and not has_weapon:
                    continue
                valid_insights.append(i)
            brief.officer_insights = valid_insights

        # 3. Validate Investigation Limitations
        if getattr(brief, "investigation_limitations", None):
            valid_limits = []
            for lim in brief.investigation_limitations:
                if "Missing Murder Weapon" in lim.description and has_weapon:
                    continue
                if "Missing Eyewitness" in lim.description and has_witness:
                    continue
                valid_limits.append(lim)
            brief.investigation_limitations = valid_limits

        return brief
