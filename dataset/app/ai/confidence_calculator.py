import logging
from dataclasses import dataclass, field
from typing import List, Any

logger = logging.getLogger(__name__)

@dataclass
class ConfidenceScore:
    base_score: float
    witness_weight: float
    forensic_weight: float
    timeline_weight: float
    digital_weight: float
    knowledge_graph_weight: float
    penalties: float
    
    positive_factors: List[str] = field(default_factory=list)
    negative_factors: List[str] = field(default_factory=list)
    final_score: float = 0.0
    calculation_formula: str = ""

class ConfidenceCalculator:
    """
    Computes explainable, deterministic confidence scoring based on verified evidence vectors.
    """
    
    @staticmethod
    def calculate(context: Any) -> ConfidenceScore:
        cases = getattr(context, "normalized_cases", []) or []
        if not cases:
            return ConfidenceScore(
                base_score=0.1, witness_weight=0, forensic_weight=0,
                timeline_weight=0, digital_weight=0, knowledge_graph_weight=0,
                penalties=0, final_score=0.1, calculation_formula="Base(0.1)"
            )
            
        pos = []
        neg = []
        
        base_score = 0.20
        pos.append(f"Base confidence established from {len(cases)} active case records.")
        
        has_weapon = False
        has_vehicle = False
        has_witness = False
        has_phone = False
        has_financial = False
        has_timeline_verified = False
        
        for c in cases:
            if hasattr(c, "evidence"):
                if c.evidence.has_weapon: has_weapon = True
                if c.evidence.has_vehicle: has_vehicle = True
                if c.evidence.has_witness: has_witness = True
                if c.evidence.has_phone: has_phone = True
                if c.evidence.has_financial_trail: has_financial = True
            if hasattr(c, "timeline") and not getattr(c.timeline, "has_gaps", True):
                has_timeline_verified = True
                
        kg_report = getattr(context, "knowledge_graph_report", {})
        kg_nodes = kg_report.get("node_count", 0) if isinstance(kg_report, dict) else 0

        w_witness = 0.15 if has_witness else 0.0
        w_forensic = 0.25 if has_weapon else 0.0
        w_digital = 0.20 if (has_phone or has_financial) else 0.0
        w_timeline = 0.10 if has_timeline_verified else 0.0
        w_kg = 0.10 if kg_nodes > 1 else 0.0
        
        if w_witness > 0: pos.append("Verified witness statements (+15%).")
        if w_forensic > 0: pos.append("Physical/Forensic evidence recovered (+25%).")
        if w_digital > 0: pos.append("Digital/Financial footprint verified (+20%).")
        if w_timeline > 0: pos.append("Timeline sequence mathematically contiguous (+10%).")
        if w_kg > 0: pos.append("Knowledge Graph confirmed entity connections (+10%).")
        
        penalties = 0.0
        reasoning = getattr(context, "investigation_reasoning", None)
        if reasoning:
            if reasoning.contradictions and reasoning.contradictions[0].description != "No conflicting evidence detected.":
                penalties += 0.20
                neg.append("Direct contradictions detected across evidence sources (-20%).")
                
            if not has_weapon and not has_witness and not has_phone:
                penalties += 0.15
                neg.append("Critical core evidence domains missing (-15%).")

        if not has_timeline_verified:
            neg.append("Timeline gaps prevent sequence verification.")
        if not has_witness:
            neg.append("No independent eyewitness corroboration.")

        total = base_score + w_witness + w_forensic + w_timeline + w_digital + w_kg - penalties
        total = max(0.1, min(1.0, total))
        
        formula = f"Base(0.20) + Witness({w_witness}) + Forensic({w_forensic}) + Digital({w_digital}) + Timeline({w_timeline}) + KG({w_kg}) - Penalties({penalties}) = {total:.2f}"

        return ConfidenceScore(
            base_score=base_score,
            witness_weight=w_witness,
            forensic_weight=w_forensic,
            timeline_weight=w_timeline,
            digital_weight=w_digital,
            knowledge_graph_weight=w_kg,
            penalties=penalties,
            positive_factors=pos,
            negative_factors=neg,
            final_score=total,
            calculation_formula=formula
        )
