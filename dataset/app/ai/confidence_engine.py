from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class ConfidenceEngine:
    """
    Confidence Engine:
    Calculates a verifiable, objective confidence score for every AI response based on
    Execution Metrics, Analytics Coverage, Evidence Count, and Reasoning Completeness.
    Never fabricates confidence.
    """

    @staticmethod
    def calculate(
        intent: str,
        intent_confidence: float,
        search_result: List[Dict[str, Any]],
        intelligence_bundle_trace: List[str],
        reasoning_result: Dict[str, Any],
        pipeline_warnings: List[str],
        clarification_required: bool
    ) -> Dict[str, Any]:
        
        explanation = []
        missing_data = []
        
        # 1. Base Score from Entity/Intent Quality
        base_score = intent_confidence
        explanation.append(f"Base confidence initialized to {base_score:.2f} from intent classifier.")
        
        # 2. Conversation Resolution Override
        if clarification_required:
            explanation.append("Clarification required. Confidence in asking follow-up is 1.00.")
            return ConfidenceEngine._build_payload(1.0, "LOW", missing_data, explanation)
            
        if intent in ["GREETING", "GOODBYE", "THANKS", "HELP", "BOT_IDENTITY", "BOT_CAPABILITIES", "GENERAL_CHAT"]:
            explanation.append("Conversational intent detected. Standard confidence applies.")
            return ConfidenceEngine._build_payload(base_score, "LOW", missing_data, explanation)

        # 3. Evidence Count
        evidence_count = len(search_result)
        if evidence_count == 0:
            base_score *= 0.5
            explanation.append("Zero database records retrieved (-50% penalty).")
        elif evidence_count == 1:
            base_score *= 0.9
            explanation.append("Only a single database record retrieved (-10% penalty).")
        else:
            explanation.append(f"Robust evidence count ({evidence_count} records) retrieved (+0% penalty).")

        # 4. Analytics Coverage
        if pipeline_warnings:
            penalty = len(pipeline_warnings) * 0.1
            base_score -= penalty
            explanation.append(f"Pipeline encountered {len(pipeline_warnings)} analytic failure(s) (-{penalty:.2f} penalty).")
        else:
            if intelligence_bundle_trace:
                explanation.append(f"Analytics successfully executed: {', '.join(intelligence_bundle_trace)}.")
            else:
                explanation.append("No advanced analytics triggered for this query.")

        # 5. Reasoning Completeness
        if reasoning_result:
            # Add missing data
            missing_info = reasoning_result.get("missing_information", [])
            if missing_info:
                missing_data.extend(missing_info)
                explanation.append(f"Reasoning engine detected missing data: {', '.join(missing_info)}.")
                
            contradictions = reasoning_result.get("contradictions", [])
            if contradictions:
                explanation.append(f"Reasoning engine detected contradictions: {', '.join(contradictions)}.")
                
            # Apply reasoning adjustment
            adj = reasoning_result.get("confidence_adjustment", 0.0)
            base_score += adj
            if adj < 0:
                explanation.append(f"Reasoning engine applied negative adjustment ({adj:.2f}) due to insufficient/contradictory evidence.")
            elif adj > 0:
                explanation.append(f"Reasoning engine applied positive adjustment (+{adj:.2f}) due to verified evidence chain.")
        
        # Final Score Bounding
        final_score = max(0.0, min(1.0, base_score))
        
        # Risk Classification
        if final_score >= 0.85:
            risk = "LOW"
        elif final_score >= 0.60:
            risk = "MEDIUM"
        else:
            risk = "HIGH"
            
        explanation.append(f"Final confidence calculated as {final_score:.2f} with {risk} risk classification.")
        
        return ConfidenceEngine._build_payload(final_score, risk, missing_data, explanation)

    @staticmethod
    def _build_payload(confidence: float, risk: str, missing_data: List[str], explanation: List[str]) -> Dict[str, Any]:
        return {
            "confidence": confidence,
            "risk": risk,
            "missing_data": missing_data,
            "explanation": explanation
        }
