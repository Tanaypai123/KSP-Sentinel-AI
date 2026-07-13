import re

with open('/Users/tanaysharma/Desktop/KSP-Sentinel-AI/dataset/app/ai/decision_support_engine.py', 'r') as f:
    content = f.read()

# Update InvestigationStrategy
new_strategy = """@dataclass
class InvestigationStrategy:
    title:              str
    evidence:           str
    reasoning:          str
    risk:               str
    recommendation:     str
    expected_impact:    str
    confidence:         float
    priority:           Priority
    dependencies:       List[str]"""

content = re.sub(r"@dataclass\nclass InvestigationStrategy:.*?    warnings:           List\[str\]", new_strategy, content, flags=re.DOTALL)
content = re.sub(r"    def to_dict\(self\) -> Dict\[str, Any\]:.*?            \"warnings\":            self\.warnings,\n        }", """    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "evidence": self.evidence,
            "reasoning": self.reasoning,
            "risk": self.risk,
            "recommendation": self.recommendation,
            "expected_impact": self.expected_impact,
            "confidence": self.confidence,
            "priority": self.priority.value,
            "dependencies": self.dependencies,
        }""", content, flags=re.DOTALL)

# Update strategy generation logic in DecisionSupportEngineStage._build_strategies
new_build_strategies = """    @staticmethod
    def _build_strategies(context: Any, risk: RiskAssessment) -> List[InvestigationStrategy]:
        strategies = []
        cases = getattr(context, "normalized_cases", []) or []
        if not cases:
            return strategies
            
        has_weapon = False
        has_vehicle = False
        has_witness = False
        has_phone = False
        has_financial = False
        has_cyber = False
        has_murder = False
        
        for c in cases:
            if hasattr(c, "evidence"):
                ev = c.evidence
                if ev.has_weapon: has_weapon = True
                if ev.has_vehicle: has_vehicle = True
                if ev.has_witness: has_witness = True
                if ev.has_phone: has_phone = True
                if ev.has_financial_trail: has_financial = True
            cat = getattr(c, "classification", None)
            if cat:
                if cat.crime_category == "Murder": has_murder = True
                if "cyber" in cat.crime_category.lower(): has_cyber = True

        if not has_weapon and has_murder:
            strategies.append(InvestigationStrategy(
                title="Recover Murder Weapon",
                evidence="Weapon Missing from Forensic Logs",
                reasoning="Weapon recovery is critical to establish a definitive ballistic connection.",
                risk="Without weapon, ballistic analysis is impossible, leaving a weak forensic chain.",
                recommendation="Deploy Crime Scene Team to recover murder weapon.",
                expected_impact="Increase forensic confidence.",
                confidence=0.85,
                priority=Priority.IMMEDIATE,
                dependencies=["Crime Scene Team"]
            ))

        if not has_phone:
            strategies.append(InvestigationStrategy(
                title="Verify Mobile Records",
                evidence="No Mobile CDRs Verified",
                reasoning="Mobile logs are required to recreate geographic timeline and associate suspect movements.",
                risk="Without CDR, timeline cannot be mathematically verified.",
                recommendation="File CDR request for all primary suspects.",
                expected_impact="Close timeline gaps and map entity movement.",
                confidence=0.75,
                priority=Priority.HIGH,
                dependencies=["Cyber Cell", "Telecom Operator"]
            ))

        if has_witness and not has_weapon and not has_phone:
            strategies.append(InvestigationStrategy(
                title="Corroborate Witness Testimony",
                evidence="Witness Statements exist but lack independent forensic backing",
                reasoning="Testimonial evidence requires physical anchoring to be court-admissible.",
                risk="Vulnerable to witness recantation.",
                recommendation="Locate secondary independent corroboration (CCTV or physical).",
                expected_impact="Secure conviction by removing dependency on human testimony.",
                confidence=0.80,
                priority=Priority.HIGH,
                dependencies=["Field Officers"]
            ))

        if has_cyber and not has_financial:
            strategies.append(InvestigationStrategy(
                title="Check Financial Trail",
                evidence="Financial logs missing for cyber crime",
                reasoning="Fraud cases hinge on following the money.",
                risk="Unable to identify beneficiaries or freeze illicit funds.",
                recommendation="Request bank statements for reported accounts.",
                expected_impact="Identify ultimate beneficiary and block further transfers.",
                confidence=0.90,
                priority=Priority.IMMEDIATE,
                dependencies=["Financial Crimes Unit", "Banks"]
            ))

        if len(strategies) == 0:
            strategies.append(InvestigationStrategy(
                title="Standard Evidence Collection",
                evidence="Basic case registered",
                reasoning="Initial stages require basic forensic processing.",
                risk="Delayed collection degrades forensic quality.",
                recommendation="Deploy standard evidence collection protocols.",
                expected_impact="Establish evidentiary baseline.",
                confidence=0.70,
                priority=Priority.MEDIUM,
                dependencies=["Field Officers"]
            ))

        return strategies"""

content = re.sub(r"    @staticmethod\n    def _build_strategies.*?return strategies", new_build_strategies, content, flags=re.DOTALL)

with open('/Users/tanaysharma/Desktop/KSP-Sentinel-AI/dataset/app/ai/decision_support_engine.py', 'w') as f:
    f.write(content)
