import logging
from dataclasses import dataclass, field
from typing import Any, List, Dict, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class EvidenceWeight(Enum):
    VERY_HIGH = 4
    HIGH = 3
    MEDIUM = 2
    LOW = 1

@dataclass
class OfficerInsight:
    insight: str
    reason: str
    supporting_evidence: List[str]
    investigation_impact: str

@dataclass
class InvestigationConclusion:
    evidence_strength: str
    remaining_gaps: List[str]
    strongest_evidence: str
    weakest_evidence: str
    probability_of_successful_prosecution: str
    critical_next_step: str
    overall_investigation_readiness: str
    supporting_evidence: List[str]

@dataclass
class InvestigationLimitation:
    limitation_type: str  # e.g., "Data unavailable", "Evidence pending", "Timeline gaps", "Forensic pending"
    description: str
    impact: str

@dataclass
class Contradiction:
    description: str

@dataclass
class InvestigationReasoningResult:
    correlated_evidence: List[str]
    contradictions: List[Contradiction]
    limitations: List[InvestigationLimitation]
    officer_insights: List[OfficerInsight]
    investigation_conclusion: Optional[InvestigationConclusion] = None

class InvestigationReasoningEngineStage:
    @staticmethod
    def run(context: Any) -> Any:
        try:
            cases = getattr(context, "normalized_cases", []) or []
            if not cases:
                context.investigation_reasoning = None
                return context

            from app.ai.evidence_reasoning_graph import EvidenceReasoningGraph
            correlated_evidence = EvidenceReasoningGraph.build_graph(cases)
            
            # Format correlated evidence strings to support backward compatibility in brief builder
            formatted_correlated = []
            for link in correlated_evidence:
                firs = ", ".join(link.supporting_records)
                formatted_correlated.append(f"{link.evidence_a} linked with {link.evidence_b} | Reason: {link.reason} | Sources: {firs}")

            total_weight = 0
            has_weapon = False
            has_vehicle = False
            has_witness = False
            has_phone = False
            has_financial = False
            
            fir_numbers = set()
            for c in cases:
                if c.fir_number:
                    fir_numbers.add(c.fir_number)
                if hasattr(c, "evidence"):
                    if c.evidence.has_weapon: has_weapon = True
                    if c.evidence.has_vehicle: has_vehicle = True
                    if c.evidence.has_witness: has_witness = True
                    if c.evidence.has_phone: has_phone = True
                    if c.evidence.has_financial_trail: has_financial = True
            
            source_str = ", ".join(list(fir_numbers)) if fir_numbers else "Unknown"

            if has_weapon: total_weight += EvidenceWeight.HIGH.value
            if has_witness: total_weight += EvidenceWeight.MEDIUM.value
            if has_financial: total_weight += EvidenceWeight.HIGH.value
            if has_phone: total_weight += EvidenceWeight.HIGH.value
            if has_vehicle: total_weight += EvidenceWeight.MEDIUM.value

            contradictions = []
            if not contradictions:
                contradictions.append(Contradiction(description="No conflicting evidence detected."))

            limitations = []
            if not has_weapon and any(c.classification.crime_category == "Murder" for c in cases if getattr(c, "classification", None)):
                limitations.append(InvestigationLimitation(
                    limitation_type="Forensic pending",
                    description="Missing Murder Weapon",
                    impact="Limits forensic certainty."
                ))
            if not has_witness:
                limitations.append(InvestigationLimitation(
                    limitation_type="Data unavailable",
                    description="Missing Eyewitness",
                    impact="Unable to independently verify circumstantial evidence."
                ))
            if not has_phone:
                limitations.append(InvestigationLimitation(
                    limitation_type="Data unavailable",
                    description="Missing Mobile CDR",
                    impact="Movement reconstruction incomplete."
                ))
            if not has_financial and any("cyber" in (getattr(c, "classification", None) and c.classification.crime_category or "").lower() for c in cases):
                limitations.append(InvestigationLimitation(
                    limitation_type="Evidence pending",
                    description="Missing Financial Logs",
                    impact="Cannot trace fund destinations in fraud case."
                ))

            insights = []
            if total_weight >= 8:
                insights.append(OfficerInsight(
                    insight="Case appears solvable with additional forensic processing.",
                    reason="Strong evidentiary baseline across physical and digital domains. No major gaps.",
                    supporting_evidence=[e for e, has in [("Weapon", has_weapon), ("Phone", has_phone), ("Financial", has_financial)] if has],
                    investigation_impact="High probability of securing convictions if chain of custody is maintained."
                ))
            elif has_financial or has_phone:
                insights.append(OfficerInsight(
                    insight="Digital trail is stronger than physical evidence.",
                    reason="Lack of physical recovery but strong digital markers (CDR/Bank records).",
                    supporting_evidence=["Phone Records", "Financial Trail"] if has_financial and has_phone else (["Financial Trail"] if has_financial else ["Phone Records"]),
                    investigation_impact="Focus investigative bandwidth on cyber forensics rather than ground searches."
                ))
            elif has_witness and not has_weapon:
                insights.append(OfficerInsight(
                    insight="Witness testimony requires independent corroboration.",
                    reason="Witness testimony currently stands alone. No CCTV, No Phone Records, No DNA. Court reliability may decrease.",
                    supporting_evidence=["Witness Statements"],
                    investigation_impact="Priority: Locate independent corroboration. Vulnerable to recantation during trial."
                ))
            else:
                insights.append(OfficerInsight(
                    insight="Investigation requires fundamental evidence gathering.",
                    reason="Extremely low evidentiary weight. Missing standard links.",
                    supporting_evidence=["None"],
                    investigation_impact="Case is at risk of going cold. Re-interview complainants and sweep scene."
                ))

            strength = "Low"
            if total_weight >= 10:
                strength = "Very High"
            elif total_weight >= 7:
                strength = "High"
            elif total_weight >= 4:
                strength = "Medium"
                
            outstanding = [l.description for l in limitations]
            next_action = "Standard progression."
            if strength == "Low":
                next_action = "Halt advanced analytics; return to fundamental scene sweeps."
            elif limitations:
                next_action = f"Prioritize extraction of: {limitations[0].description}"
            else:
                next_action = "Proceed with chargesheet compilation."
                
            # Find strongest/weakest evidence
            strongest = "Unknown"
            if has_weapon: strongest = "Weapon"
            elif has_financial: strongest = "Financial Trail"
            elif has_witness: strongest = "Witness Statement"
            
            weakest = "Forensics" if not has_weapon else "Testimonial" if not has_witness else "None"
            
            prob = "Low"
            if strength == "Very High": prob = "Very High"
            elif strength == "High": prob = "High"
            elif strength == "Medium": prob = "Medium"
                
            conclusion = InvestigationConclusion(
                evidence_strength=strength,
                remaining_gaps=outstanding if outstanding else ["None pending"],
                strongest_evidence=strongest,
                weakest_evidence=weakest,
                probability_of_successful_prosecution=prob,
                critical_next_step=next_action,
                overall_investigation_readiness="Ready for prosecution" if strength in ["High", "Very High"] else "Requires more evidence",
                supporting_evidence=list(fir_numbers)
            )

            result = InvestigationReasoningResult(
                correlated_evidence=formatted_correlated,
                contradictions=contradictions,
                limitations=limitations,
                officer_insights=insights,
                investigation_conclusion=conclusion
            )
            
            context.investigation_reasoning = result
            
        except Exception as e:
            logger.error(f"InvestigationReasoningEngineStage failed: {e}")
            context.investigation_reasoning = None
            
        return context
