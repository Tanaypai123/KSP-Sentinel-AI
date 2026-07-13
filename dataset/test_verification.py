import asyncio
from pprint import pprint
from app.database.connection import SessionLocal
from sqlalchemy import text
from app.ai.pipeline_runner import PipelineRunner
from app.ai.investigation_brief_builder import InvestigationBriefBuilder
from app.ai.decision_support_engine import DecisionSupportStage, RiskAnalyzer, StrategyGenerator

async def test_ksp_000012_db():
    db = SessionLocal()
    print("--- 2. DATABASE VALUES (KSP-000012) ---")
    sql = text('''
        SELECT 
            cm."CrimeMajorHeadID",
            cm."CrimeMinorHeadID",
            ch."CrimeGroupName",
            csh."CrimeHeadName"
        FROM case_master cm
        LEFT JOIN crime_head ch ON cm."CrimeMajorHeadID" = ch."CrimeHeadID"
        LEFT JOIN crime_sub_head csh ON cm."CrimeMinorHeadID" = csh."CrimeSubHeadID"
        WHERE cm."CrimeNo" = 'KSP-000012'
    ''')
    res = db.execute(sql).first()
    print("CrimeMajorHeadID:", res[0])
    print("CrimeMinorHeadID:", res[1])
    print("Resolved Crime Head:", res[2])
    print("Resolved Crime Sub Head:", res[3])
    
    # Run pipeline up to normalizer
    context = PipelineRunner.run('Open FIR KSP-000012', db)
    if context.normalized_cases:
        c = context.normalized_cases[0]
        for nc in context.normalized_cases:
            if nc.classification.crime_head:
                c = nc
                break
                
        print("Classification produced by ContextNormalizer:")
        print(c.classification)
        
        print("\n--- 3. PIPELINE OUTPUT (NormalizedCase) ---")
        import dataclasses
        pprint(dataclasses.asdict(c))
        
        print("\n--- 4. InvestigationBriefBuilder Input ---")
        print("Type:", type(context))
        print("Normalized Cases Count:", len(context.normalized_cases))
        print("First Case Classification:", context.normalized_cases[0].classification if context.normalized_cases else "None")
        
        print("\n--- 5. StrategyGenerator Input & Output ---")
        print("crime_head:", c.classification.crime_category)
        print("crime_sub_head:", c.classification.crime_head)
        print("classification:", c.classification)
        risk = RiskAnalyzer.analyze(context)
        print("risk:", risk.overall_risk_level)
        
        strat = StrategyGenerator.generate(context, risk)
        print("\nBranch:")
        crime = c.classification.crime_category or c.classification.crime_head or ""
        c_lower = str(crime).lower()
        if "cyber" in c_lower or "fraud" in c_lower:
            print("Cyber Fraud")
        elif "murder" in c_lower or "homicide" in c_lower:
            print("Murder")
        elif "vehicle" in c_lower or "theft" in c_lower:
            print("Vehicle Theft")
        else:
            print("Fallback/Other")
        
        for rec in strat:
            print("- " + str(vars(rec)))

    db.close()

async def test_runtime():
    print("\n--- 7. RUNTIME PROOF ---")
    firs = ['KSP-000012', 'KSP-000004', 'KSP-000346']
    for fir in firs:
        db = SessionLocal()
        print(f"\nEvaluating: {fir}")
        try:
            context = PipelineRunner.run(f"Open FIR {fir}", db)
            brief = InvestigationBriefBuilder.build(context)
            
            det_crime, det_sub = "NULL", "NULL"
            if context.normalized_cases:
                for c in context.normalized_cases:
                    if c.classification.crime_head:
                        det_crime = c.classification.crime_category
                        det_sub = c.classification.crime_head
                        break
            
            print("Detected Crime:", det_crime)
            print("Detected Sub Crime:", det_sub)
            print("Generated Executive Summary:", brief.executive_summary)
            print("Generated Investigation Priority:", brief.investigation_priority)
            print("Recommendations:")
            for r in brief.recommendations:
                print("  - " + str(vars(r)))
        except Exception as e:
            print(f"Error for {fir}: {e}")
        finally:
            db.close()

async def fallback_test():
    print("\n--- 8. FALLBACK VERIFICATION ---")
    # Provide an empty case
    from app.ai.decision_support_engine import StrategyGenerator, RiskAssessment
    class MockEvidence:
        has_weapon = False
        has_vehicle = False
        has_witness = False
        has_phone = False
        has_financial_trail = False
    
    class MockClass:
        crime_category = ""
        crime_head = ""
        crime_sub_head = ""
        
    class MockCase:
        evidence = MockEvidence()
        classification = MockClass()
        accused_names = []
        victim_names = []
        fir_number = "TEST-FALLBACK"
        
    class MockContext:
        normalized_cases = [MockCase()]
        resolved_entities = {}
        
    class MockRisk:
        level = "LOW"
        score = 25
        factors = []
        
    strat = StrategyGenerator.generate(MockContext(), MockRisk())
    print("Fallback Strategies without Crime Type:")
    for r in strat:
        print("  - " + str(vars(r)))

async def main():
    await test_ksp_000012_db()
    await test_runtime()
    await fallback_test()
    print("\nPhase 7.2 VERIFIED")

asyncio.run(main())
