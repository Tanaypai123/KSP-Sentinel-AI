from typing import Dict, Any, List

class RecommendationEngine:
    @staticmethod
    def generate_recommendations(results: List[Dict[str, Any]], entities: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Analyzes crime details and generates evidence-backed investigation recommendations.
        """
        if not results:
            return []
            
        entities = entities or {}

        recommendations = []
        
        # Analyze the first result to base the core recommendations on
        target = results[0]
        
        crime_group = target.get("crime_group_name", "") or target.get("crime_head", "") or entities.get("crime_head", "")
        crime_cat = target.get("crime_category", "") or target.get("crime_minor_head", "") or entities.get("crime_category", "")
        facts = (target.get("brief_facts") or "").lower()
        accused_list = target.get("accused_names", []) or target.get("accused_name", "")
        
        crime_str = f"{crime_group} {crime_cat}".strip().lower()
        victim_list = target.get("victim_names", [])
        
        # Determine logical evidence rules
        has_digital = any(k in facts for k in ["online", "upi", "bank", "otp", "password", "cyber", "whatsapp", "call", "phone"])
        has_location = target.get("latitude") and target.get("longitude")
        has_violence = any(k in crime_str for k in ["murder", "assault", "rape", "kidnap"]) or any(k in facts for k in ["blood", "weapon", "knife", "gun"])
        has_theft = any(k in crime_str for k in ["theft", "robbery", "burglary", "dacoity"]) or any(k in facts for k in ["stole", "snatch", "gold", "cash", "bike"])
        is_missing = any(k in crime_str for k in ["missing"])
        has_accused = bool(accused_list)
        
        # Generate Recommendations based on crime properties
        if has_theft and not has_digital:
            recommendations.append({
                "action": "CCTV Suggestions",
                "priority": "HIGH",
                "reason": "Identify escape routes and suspect appearance.",
                "confidence": "HIGH",
                "evidence": "Crime involves physical property theft/robbery."
            })
            recommendations.append({
                "action": "Fingerprint Suggestions",
                "priority": "HIGH",
                "reason": "Extract latent prints from point of entry.",
                "confidence": "HIGH",
                "evidence": "Physical property/premises accessed."
            })
            
        if has_violence:
            recommendations.append({
                "action": "Evidence Collection",
                "priority": "CRITICAL",
                "reason": "Secure biological evidence and weapon traces immediately.",
                "confidence": "HIGH",
                "evidence": "Violent crime indicated."
            })
            if not has_accused:
                recommendations.append({
                    "action": "Recommended Interviews",
                    "priority": "HIGH",
                    "reason": "Interview immediate family and known associates of the victim.",
                    "confidence": "MEDIUM",
                    "evidence": "Suspect unknown in violent crime."
                })
                
        if has_digital or "fraud" in crime_str or "cyber" in crime_str:
            recommendations.append({
                "action": "Digital Evidence",
                "priority": "HIGH",
                "reason": "Preserve transaction logs and trace IP addresses.",
                "confidence": "HIGH",
                "evidence": "Digital/Financial Modus Operandi detected."
            })
            recommendations.append({
                "action": "CDR Suggestions",
                "priority": "HIGH",
                "reason": "Analyze Call Detail Records for suspect communication.",
                "confidence": "HIGH",
                "evidence": "Phone/Online medium involved."
            })
            
        if is_missing:
            recommendations.append({
                "action": "CDR Suggestions",
                "priority": "CRITICAL",
                "reason": "Trace last cell tower location of the missing person.",
                "confidence": "HIGH",
                "evidence": "Person reported missing."
            })
            recommendations.append({
                "action": "Immediate Actions",
                "priority": "HIGH",
                "reason": "Alert local hospitals and transport hubs.",
                "confidence": "HIGH",
                "evidence": "Standard operating procedure for missing persons."
            })

        # Base generic checks
        if has_accused:
            recommendations.append({
                "action": "Vehicle Verification",
                "priority": "MEDIUM",
                "reason": "Verify RTO records for vehicles registered to suspects.",
                "confidence": "MEDIUM",
                "evidence": "Suspect identities are known."
            })

        # Insufficient Evidence Fallback
        if not recommendations:
            recommendations.append({
                "action": "Preliminary Investigation",
                "priority": "LOW",
                "reason": "Additional evidence required to formulate specific investigative strategy.",
                "confidence": "LOW",
                "evidence": "Insufficient distinct markers in FIR."
            })

        return recommendations
