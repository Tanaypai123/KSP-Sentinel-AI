from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

# Import individual engines
from app.ai.crime_pattern_analyzer import CrimePatternAnalyzer
from app.ai.similarity_engine import SimilarityEngine
from app.ai.repeat_offender_engine import RepeatOffenderEngine
from app.ai.network_engine import NetworkEngine
from app.ai.hotspot_engine import HotspotEngine
from app.ai.recommendation_engine import RecommendationEngine

@dataclass
class IntelligenceBundle:
    pattern_analysis: Optional[str] = None
    similar_cases: List[Dict[str, Any]] = field(default_factory=list)
    repeat_offender: Optional[Dict[str, Any]] = None
    network: Optional[Dict[str, Any]] = None
    hotspots: Optional[Dict[str, Any]] = None
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    execution_trace: List[str] = field(default_factory=list)

class IntelligenceEngine:
    """
    Orchestrates the execution of all AI sub-engines.
    Prevents monolithic evaluation by selectively invoking only the required engines
    based on the intent and available data.
    """

    @staticmethod
    def run(
        search_result: List[Dict[str, Any]],
        conversation_state: Any,
        intent_result: Any,
        db: Session
    ) -> IntelligenceBundle:
        intent = intent_result.intent
        confidence = intent_result.confidence
        
        # Get query and entities from conversation_state
        raw_query = conversation_state.last_query or ""
        entities = conversation_state.last_entities or {}
        
        bundle = IntelligenceBundle(confidence=confidence)
        
        if not search_result:
            return bundle

        # Dynamic execution maps
        
        # 1. HOTSPOT / SEARCH_LOCATION -> Pattern -> Hotspot
        if intent == "HOTSPOT":
            bundle.hotspots = HotspotEngine.analyze_hotspots(search_result)
            bundle.execution_trace.append("Hotspot")
            # Replace the search_result list elements in-place
            search_result.clear()
            search_result.append({"hotspot_data": bundle.hotspots})
            
        elif intent == "SEARCH_LOCATION":
            # Pattern
            if len(search_result) > 1:
                bundle.pattern_analysis = CrimePatternAnalyzer.build_pattern_summary(search_result)
                bundle.execution_trace.append("Pattern")
            # Hotspot
            bundle.hotspots = HotspotEngine.analyze_hotspots(search_result)
            bundle.execution_trace.append("Hotspot")
            
        # 2. NETWORK_SEARCH -> Network
        elif intent == "NETWORK_SEARCH":
            active_fir = conversation_state.active_fir
            if active_fir:
                fir_no = active_fir.get("crime_no") or active_fir.get("fir_no")
                if fir_no:
                    bundle.network = NetworkEngine.build_network("FIR", fir_no, db)
                    bundle.execution_trace.append("Network")
                    search_result.clear()
                    search_result.append({"network_data": bundle.network})
            
        # 3. SEARCH_ACCUSED -> RepeatOffender -> Network -> Recommendation
        elif intent == "SEARCH_ACCUSED":
            # RepeatOffender
            accused_name = None
            for accused_record in search_result:
                name = accused_record.get("accused_name")
                if name:
                    accused_name = name
                off_res = RepeatOffenderEngine.analyze_accused(accused_record.get("accused_name"), db)
                accused_record["officer_summary"] = off_res.get("officer_summary", "")
                accused_record["linked_firs"] = off_res.get("linked_firs", [])
                
            bundle.execution_trace.append("RepeatOffender")
            bundle.repeat_offender = {
                "results": search_result
            }
            
            # Network
            # Find network for the primary accused
            if accused_name:
                bundle.network = NetworkEngine.build_network("ACCUSED", accused_name, db)
                bundle.execution_trace.append("Network")
                
            # Recommendation
            bundle.recommendations = RecommendationEngine.generate_recommendations(search_result, entities)
            bundle.execution_trace.append("Recommendation")
            
        # 4. COMPARE_CASES / SIMILAR_CASES -> Similarity -> Pattern
        elif intent == "SEARCH_CASES" and ("similar" in raw_query.lower() or intent_result.is_similar_search):
            active_fir = conversation_state.active_fir
            if active_fir:
                scored = SimilarityEngine.find_top_similar(active_fir, search_result)
                new_results = []
                for c, score, expl in scored:
                    c["_similarity_score"] = score
                    c["_similarity_explanation"] = expl
                    new_results.append(c)
                
                # Update search_result list in-place
                search_result.clear()
                search_result.extend(new_results)
                
                bundle.similar_cases = search_result
                bundle.execution_trace.append("Similarity")
                
                # Pattern
                if len(search_result) > 1:
                    bundle.pattern_analysis = CrimePatternAnalyzer.build_pattern_summary(search_result)
                    bundle.execution_trace.append("Pattern")

        # 5. Default Case Search / Police Station Search / FIR Lookup
        else:
            # Pattern
            if intent in ["SEARCH_CASES", "SEARCH_POLICE_STATION"] and len(search_result) > 1:
                bundle.pattern_analysis = CrimePatternAnalyzer.build_pattern_summary(search_result)
                bundle.execution_trace.append("Pattern")
            # Recommendation
            if intent in ["SEARCH_CASES", "FIR_LOOKUP", "SEARCH_POLICE_STATION"]:
                bundle.recommendations = RecommendationEngine.generate_recommendations(search_result, entities)
                bundle.execution_trace.append("Recommendation")

        # Set backward compatible _intelligence_report in results[0]
        if search_result:
            search_result[0]["_intelligence_report"] = {
                "pattern_summary": bundle.pattern_analysis,
                "similar_cases": bundle.similar_cases,
                "network_data": bundle.network,
                "hotspot_data": bundle.hotspots,
                "recommendations": bundle.recommendations
            }

        return bundle
