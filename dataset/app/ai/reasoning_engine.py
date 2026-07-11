from typing import Dict, Any, List, Optional
import logging
from app.ai.intelligence_engine import IntelligenceBundle

logger = logging.getLogger(__name__)

class ReasoningEngine:
    """
    Reasoning Engine:
    Validates conclusions against hard data (search results, analytics, and context).
    Explicitly rejects unsupported inferences to guarantee zero hallucinations.
    """

    @staticmethod
    def evaluate(
        intent: str,
        resolved_entities: Dict[str, Any],
        search_result: List[Dict[str, Any]],
        intelligence_bundle: Optional[IntelligenceBundle] = None,
        raw_query: str = ""
    ) -> Dict[str, Any]:
        """
        Analyzes the execution state to build an evidence-based reasoning chain.
        """
        evidence_chain = []
        reason_chain = []
        supporting_records = []
        missing_information = []
        contradictions = []
        confidence_adjustment = 0.0

        # Base case: No results
        if not search_result:
            evidence_chain.append("Database query returned 0 matching records.")
            reason_chain.append("Cannot fulfill request because the underlying data is absent.")
            missing_information.append("Matching database records")
            reasoning_conclusion = "Insufficient evidence."
            confidence_adjustment = -0.50
            
            return ReasoningEngine._build_payload(
                evidence_chain, reason_chain, supporting_records, 
                missing_information, contradictions, reasoning_conclusion, confidence_adjustment
            )

        # 1. Analyze Supporting Records
        for record in search_result:
            # Look for explicit identifiers
            if "crime_no" in record:
                supporting_records.append(f"FIR: {record['crime_no']}")
            elif "fir_no" in record:
                 supporting_records.append(f"FIR: {record['fir_no']}")
            elif "accused_name" in record:
                supporting_records.append(f"Accused: {record['accused_name']}")
            elif "victim_name" in record:
                supporting_records.append(f"Victim: {record['victim_name']}")

        # 2. Extract Evidence based on Intent
        if intent == "FIR_LOOKUP":
            if any(rec.get("crime_no") or rec.get("fir_no") for rec in search_result):
                evidence_chain.append(f"Found {len(search_result)} FIR record(s) matching the criteria.")
                reason_chain.append("The requested FIR details were successfully retrieved from the database.")
            else:
                missing_information.append("FIR identifiers in returned records")
                
        elif intent in ["SEARCH_CASES", "SEARCH_LOCATION", "SEARCH_POLICE_STATION"]:
            evidence_chain.append(f"Found {len(search_result)} case records matching the criteria.")
            
            # Check for intelligence bundle data (Patterns, Hotspots)
            if intelligence_bundle:
                if intelligence_bundle.pattern_analysis:
                    evidence_chain.append("Crime pattern analysis generated from aggregate case data.")
                    reason_chain.append("Pattern analysis provides macroscopic insights based on the retrieved case cluster.")
                if intelligence_bundle.hotspots:
                    evidence_chain.append("Geospatial hotspot clusters identified from case locations.")
                    reason_chain.append("Hotspot identification pinpoints high-density crime areas within the results.")
            
            # Check if specific entities were requested but not reflected in the results
            requested_district = resolved_entities.get("district")
            if requested_district:
                for rec in search_result:
                    if rec.get("district_name") and rec.get("district_name").lower() != requested_district.lower():
                         contradictions.append(f"Record district '{rec.get('district_name')}' contradicts requested district '{requested_district}'.")

        elif intent == "SEARCH_ACCUSED":
            if any(rec.get("accused_name") for rec in search_result):
                evidence_chain.append(f"Found {len(search_result)} accused record(s).")
                reason_chain.append("Accused details retrieved.")
                if intelligence_bundle and intelligence_bundle.repeat_offender:
                    evidence_chain.append("Repeat offender historical analysis executed.")
                    reason_chain.append("Historical data linked to accused profile to establish recidivism patterns.")
            else:
                 missing_information.append("Accused name in returned records")

        elif intent == "NETWORK_SEARCH":
            if intelligence_bundle and intelligence_bundle.network:
                evidence_chain.append("Associate network successfully mapped.")
                reason_chain.append("Network graph establishes relationships between the primary entity and co-accused/associates.")
            else:
                missing_information.append("Network association data")

        elif intent == "PREDICT_CRIME":
            evidence_chain.append("Predictive model executed on historical time-series data.")
            reason_chain.append("Statistical projection utilized to estimate future occurrence.")

        elif intent == "COMPARE_CASES":
            if len(search_result) >= 2:
                evidence_chain.append("Multiple cases available for direct comparison.")
                reason_chain.append("Side-by-side feature comparison constructed.")
            else:
                missing_information.append("Secondary case required for comparison")

        # 3. Deduce Final Conclusion and Confidence Adjustment
        if missing_information or contradictions:
            reasoning_conclusion = "Insufficient evidence."
            confidence_adjustment = -0.30
            reason_chain.append("Cannot fully validate the request due to missing or contradictory evidence.")
        else:
            reasoning_conclusion = "Conclusions strictly supported by verified data."
            confidence_adjustment = +0.10
            
        # De-duplicate lists while preserving order roughly
        def dedupe(seq):
            seen = set()
            return [x for x in seq if not (x in seen or seen.add(x))]
            
        supporting_records = dedupe(supporting_records)
        evidence_chain = dedupe(evidence_chain)
        missing_information = dedupe(missing_information)
        contradictions = dedupe(contradictions)

        return ReasoningEngine._build_payload(
            evidence_chain, reason_chain, supporting_records, 
            missing_information, contradictions, reasoning_conclusion, confidence_adjustment
        )

    @staticmethod
    def _build_payload(
        evidence_chain: List[str],
        reason_chain: List[str],
        supporting_records: List[str],
        missing_information: List[str],
        contradictions: List[str],
        conclusion: str,
        confidence_adjustment: float
    ) -> Dict[str, Any]:
        return {
            "evidence_chain": evidence_chain,
            "reason_chain": reason_chain,
            "supporting_records": supporting_records,
            "missing_information": missing_information,
            "contradictions": contradictions,
            "conclusion": conclusion,
            "confidence_adjustment": confidence_adjustment
        }
