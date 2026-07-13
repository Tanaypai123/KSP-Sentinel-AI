import re

with open('/Users/tanaysharma/Desktop/KSP-Sentinel-AI/dataset/app/ai/investigation_brief_builder.py', 'r') as f:
    content = f.read()

# Update build method to include Validator and Calculator
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
        return brief"""

content = re.sub(r"    @classmethod\n    def build\(cls, context: Any\) -> InvestigationBrief:.*?        return brief", new_build, content, flags=re.DOTALL)

# Update _build_progress
new_progress_method = """    @classmethod
    def _build_progress(cls, context: Any) -> InvestigationProgress:
        cases = getattr(context, "normalized_cases", []) or []
        tasks = []
        
        has_weapon = False
        has_witness = False
        has_phone = False
        has_financial = False
        
        for c in cases:
            if hasattr(c, "evidence"):
                if c.evidence.has_weapon: has_weapon = True
                if c.evidence.has_witness: has_witness = True
                if c.evidence.has_phone: has_phone = True
                if c.evidence.has_financial_trail: has_financial = True
                
        tasks.append(InvestigationTask("Crime Scene", "Completed"))
        tasks.append(InvestigationTask("Weapon Recovery", "Completed" if has_weapon else "Pending"))
        tasks.append(InvestigationTask("Witness Interview", "Completed" if has_witness else "Pending"))
        tasks.append(InvestigationTask("CDR", "Completed" if has_phone else "Pending"))
        tasks.append(InvestigationTask("Forensics", "Completed" if has_weapon or has_phone or has_financial else "Pending"))
        
        if not cases:
            tasks.append(InvestigationTask("Chargesheet", "Pending"))
            tasks.append(InvestigationTask("Arrest", "Pending"))
        else:
            status = cases[0].status.upper()
            tasks.append(InvestigationTask("Chargesheet", "Completed" if status in ["CLOSED", "CHARGE SHEETED", "CHARGESHEETED"] else "Pending"))
            tasks.append(InvestigationTask("Arrest", "Completed" if status in ["ARRESTED", "RECOVERED", "CLOSED", "CHARGE SHEETED", "CHARGESHEETED"] else "Pending"))
            
        completed = sum(1 for t in tasks if t.status == "Completed")
        pct = int((completed / len(tasks)) * 100) if tasks else 0
        
        return InvestigationProgress(tasks=tasks, completion_pct=pct)"""

content = re.sub(r"    @classmethod\n    def _build_progress.*?return InvestigationProgress\(\"Preliminary Enquiry\", 15, \"Scene Examination / Data Request\"\)", new_progress_method, content, flags=re.DOTALL)

# Update _build_recommendations
new_rec_method = """    @classmethod
    def _build_recommendations(cls, context: Any) -> List[RecommendedAction]:
        recs = []
        ds = getattr(context, "decision_support", {})
        strats = []
        if isinstance(ds, dict):
            strats = ds.get("strategies", [])
        elif hasattr(ds, "strategies"):
            strats = ds.strategies
            
        for s in strats:
            if isinstance(s, dict):
                recs.append(RecommendedAction(
                    text=s.get("title", ""),
                    evidence=s.get("evidence", ""),
                    reason=s.get("reasoning", ""),
                    risk=s.get("risk", ""),
                    recommendation=s.get("recommendation", ""),
                    expected_impact=s.get("expected_impact", ""),
                    priority=s.get("priority", "MEDIUM"),
                    confidence=s.get("confidence", 0.75),
                    dependencies=s.get("dependencies", [])
                ))
            else:
                recs.append(RecommendedAction(
                    text=getattr(s, "title", "Action"),
                    evidence=getattr(s, "evidence", ""),
                    reason=getattr(s, "reasoning", ""),
                    risk=getattr(s, "risk", ""),
                    recommendation=getattr(s, "recommendation", ""),
                    expected_impact=getattr(s, "expected_impact", ""),
                    priority=getattr(s, "priority", "MEDIUM"),
                    confidence=getattr(s, "confidence", 0.75),
                    dependencies=getattr(s, "dependencies", [])
                ))
        return recs"""

content = re.sub(r"    @classmethod\n    def _build_recommendations.*?return recs", new_rec_method, content, flags=re.DOTALL)

# Also remove _build_confidence method as we replaced it directly in build()
content = re.sub(r"    @classmethod\n    def _build_confidence\(cls, context: Any\) -> ConfidenceExplanation:.*?(?=    @classmethod|$)", "", content, flags=re.DOTALL)

with open('/Users/tanaysharma/Desktop/KSP-Sentinel-AI/dataset/app/ai/investigation_brief_builder.py', 'w') as f:
    f.write(content)
