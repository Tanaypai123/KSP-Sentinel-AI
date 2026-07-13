import re

with open('/Users/tanaysharma/Desktop/KSP-Sentinel-AI/dataset/app/ai/investigation_brief_builder.py', 'r') as f:
    content = f.read()

# We will just replace ALL of `def build` inside `InvestigationBriefBuilder` manually to be absolutely sure.
before, rest = content.split("    @classmethod\n    def build(cls, context: Any) -> InvestigationBrief:", 1)
# we need to find the end of `build` method. It ends with `return brief`
_, after = rest.split("return brief\n", 1)

new_build = """    @classmethod
    def build(cls, context: Any) -> InvestigationBrief:
        brief = InvestigationBrief()
        try:
            cases = getattr(context, "normalized_cases", []) or []
            crime_type = cls._get_crime_type(context)
            
            brief.executive_summary = cls._build_summary(context, crime_type)
            brief.investigation_priority = cls._build_priority(context, crime_type)
            brief.investigation_progress = cls._build_progress(context)
            
            collected, missing = cls._build_evidence(context)
            brief.collected_evidence = collected
            brief.missing_critical_evidence = missing
            
            brief.key_findings = cls._build_findings(context)
            brief.risk_assessment = cls._build_risks(context)
            brief.recommendations = cls._build_recommendations(context)
            
            # Use new ConfidenceCalculator
            conf_score = ConfidenceCalculator.calculate(context)
            brief.confidence_explanation = ConfidenceExplanation(
                score=conf_score.final_score,
                positive_factors=conf_score.positive_factors,
                negative_factors=conf_score.negative_factors,
                calculation_summary=conf_score.calculation_formula
            )
            
            # Map Reasoning Engine Outputs
            reasoning = getattr(context, "investigation_reasoning", None)
            if reasoning:
                brief.correlated_evidence = reasoning.correlated_evidence
                brief.investigation_limitations = reasoning.limitations
                brief.contradictions = reasoning.contradictions
                brief.officer_insights = reasoning.officer_insights
                brief.investigation_conclusion = reasoning.investigation_conclusion
                
            # Global Validation Layer
            brief = ReportConsistencyValidator.validate(brief, context)
                
        except Exception as e:
            logger.error(f"InvestigationBriefBuilder failed: {e}")
            import traceback
            traceback.print_exc()
        return brief
"""

with open('/Users/tanaysharma/Desktop/KSP-Sentinel-AI/dataset/app/ai/investigation_brief_builder.py', 'w') as f:
    f.write(before + new_build + after)
