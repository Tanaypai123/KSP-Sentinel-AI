import re

with open('/Users/tanaysharma/Desktop/KSP-Sentinel-AI/dataset/app/ai/decision_support_engine.py', 'r') as f:
    content = f.read()

new_strategy_generator = """class StrategyGenerator:
    @classmethod
    def generate(cls, context: Any, risk: RiskAssessment) -> List[InvestigationStrategy]:
        strategies: List[InvestigationStrategy] = []
        results = context.search_result or []
        entities = context.resolved_entities or {}
        kg = getattr(context, "knowledge_graph_report", None) or {}
        timeline = getattr(context, "timeline_report", None) or {}
        pred = getattr(context, "predictive_report", None) or {}
        
        fir_ids = [r.get("crime_no") for r in results if r.get("crime_no")]
        
        # Get crime type
        crime = entities.get("crime_head") or ""
        if not crime and results:
            crime = results[0].get("crime_category") or results[0].get("crime_type") or ""
        c_lower = str(crime).lower()

        # Dynamic Cyber Strategies
        if "cyber" in c_lower or "fraud" in c_lower:
            strategies.append(InvestigationStrategy(
                strategy_type=StrategyType.VERIFY_MOBILE_RECORDS,
                title="Trace Suspect IP and Freeze Accounts",
                reason="Digital footprint indicates online fraud mechanism.",
                supporting_evidence=["Entity extracted: Cyber Fraud"],
                supporting_fir_ids=fir_ids[:3],
                confidence=0.90,
                priority=Priority.IMMEDIATE,
                dependencies=["Bank Nodal Officer Contact"],
                warnings=["Funds may be siphoned across jurisdictions rapidly."]
            ))
            strategies.append(InvestigationStrategy(
                strategy_type=StrategyType.CHECK_FINANCIAL_TRAIL,
                title="Obtain Transaction Logs from Gateway",
                reason="Financial routing must be established to track beneficiaries.",
                supporting_evidence=["Transaction patterns detected"],
                supporting_fir_ids=fir_ids[:3],
                confidence=0.85,
                priority=Priority.HIGH,
                dependencies=["Court Order"],
                warnings=[]
            ))
            
        # Dynamic Vehicle Theft Strategies
        elif "vehicle" in c_lower or "theft" in c_lower:
            strategies.append(InvestigationStrategy(
                strategy_type=StrategyType.CROSS_MATCH_VEHICLES,
                title="Check ANPR Cameras and Toll Plazas",
                reason="Property movement implies transit across jurisdictional borders.",
                supporting_evidence=["Stolen vehicle identified in case records"],
                supporting_fir_ids=fir_ids[:3],
                confidence=0.88,
                priority=Priority.HIGH,
                dependencies=["Vehicle Number"],
                warnings=["Fake plates may be in use."]
            ))
            
        # Dynamic Murder Strategies
        elif "murder" in c_lower or "homicide" in c_lower:
            strategies.append(InvestigationStrategy(
                strategy_type=StrategyType.RECOVER_WEAPON,
                title="Recover Murder Weapon and DNA Profiling",
                reason="Violent crime requires concrete forensic linking.",
                supporting_evidence=["Homicide reported in FIR"],
                supporting_fir_ids=fir_ids[:3],
                confidence=0.95,
                priority=Priority.IMMEDIATE,
                dependencies=["Forensic Team"],
                warnings=["Biological evidence degrades rapidly."]
            ))
            strategies.append(InvestigationStrategy(
                strategy_type=StrategyType.REINTERVIEW_WITNESS,
                title="Reconstruct Victim Timeline",
                reason="Victim's last 24 hours are critical to establishing motive.",
                supporting_evidence=["Timeline analysis"],
                supporting_fir_ids=fir_ids[:3],
                confidence=0.85,
                priority=Priority.HIGH,
                dependencies=[],
                warnings=[]
            ))
            
        # Generic fallback strategies
        else:
            accused_names = [r.get("accused_name") for r in results if r.get("accused_name")]
            if accused_names:
                strategies.append(InvestigationStrategy(
                    strategy_type=StrategyType.INTERVIEW_SUSPECT,
                    title="Interview Identified Suspect(s)",
                    reason=f"Records confirm {len(accused_names)} accused individual(s).",
                    supporting_evidence=[f"Accused: {', '.join(accused_names[:3])}"],
                    supporting_fir_ids=fir_ids[:3],
                    confidence=0.85,
                    priority=Priority.HIGH,
                    dependencies=["Accused Apprehension"],
                    warnings=[]
                ))
            strategies.append(InvestigationStrategy(
                strategy_type=StrategyType.REVIEW_FORENSIC_EVIDENCE,
                title="Standard Evidence Collection",
                reason="Initial stages require basic forensic processing.",
                supporting_evidence=["FIR Registered"],
                supporting_fir_ids=fir_ids[:3],
                confidence=0.70,
                priority=Priority.MEDIUM,
                dependencies=[],
                warnings=[]
            ))

        return strategies[:MAX_STRATEGIES]"""

# Replace from "class StrategyGenerator:" up to the end of the generate method
pattern = r"class StrategyGenerator:.*?return strategies\[:MAX_STRATEGIES\]"
new_content = re.sub(pattern, new_strategy_generator, content, flags=re.DOTALL)

with open('/Users/tanaysharma/Desktop/KSP-Sentinel-AI/dataset/app/ai/decision_support_engine.py', 'w') as f:
    f.write(new_content)

print("Patched successfully")
