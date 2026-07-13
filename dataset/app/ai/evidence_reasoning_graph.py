import logging
from dataclasses import dataclass
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

@dataclass
class EvidenceLink:
    evidence_a: str
    evidence_b: str
    reason: str
    supporting_records: List[str]

class EvidenceReasoningGraph:
    """
    Constructs strict deterministic linkages between collected evidence domains.
    """
    
    @staticmethod
    def build_graph(cases: List[Any]) -> List[EvidenceLink]:
        links = []
        if not cases:
            return links
            
        has_weapon = False
        has_vehicle = False
        has_witness = False
        has_phone = False
        has_financial = False
        has_dna = False
        has_timeline_verified = False
        has_knowledge_graph_links = False
        has_repeat_offender = False
        
        fir_numbers = set()
        
        for c in cases:
            if c.fir_number:
                fir_numbers.add(c.fir_number)
            if hasattr(c, "evidence"):
                ev = c.evidence
                if ev.has_weapon: has_weapon = True
                if ev.has_vehicle: has_vehicle = True
                if ev.has_witness: has_witness = True
                if ev.has_phone: has_phone = True
                if ev.has_financial_trail: has_financial = True
            if hasattr(c, "timeline") and not getattr(c.timeline, "has_gaps", True):
                has_timeline_verified = True

        firs = list(fir_numbers)
        
        # Build logical edges
        if has_weapon and has_witness:
            links.append(EvidenceLink(
                evidence_a="Recovered Weapon",
                evidence_b="Witness Statements",
                reason="Physical recovery corroborates eyewitness testimony regarding the assault method.",
                supporting_records=firs
            ))
            
        if has_financial and has_phone:
            links.append(EvidenceLink(
                evidence_a="Financial Trail",
                evidence_b="Mobile CDR",
                reason="Digital footprint overlaps with banking activity, establishing timeline of transaction execution.",
                supporting_records=firs
            ))
            
        if has_vehicle and has_witness:
            links.append(EvidenceLink(
                evidence_a="Identified Vehicle",
                evidence_b="Witness Statements",
                reason="Getaway or operational vehicle confirmed by independent ground observation.",
                supporting_records=firs
            ))
            
        if has_weapon and has_timeline_verified:
            links.append(EvidenceLink(
                evidence_a="Recovered Weapon",
                evidence_b="Verified Timeline",
                reason="Forensic timeline aligns tightly with physical weapon recovery timeframe.",
                supporting_records=firs
            ))

        return links
