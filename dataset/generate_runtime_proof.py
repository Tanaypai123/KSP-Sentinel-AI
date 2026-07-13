import asyncio
from pprint import pprint
from app.database.connection import SessionLocal
from app.ai.pipeline_runner import PipelineRunner
from app.ai.investigation_brief_builder import InvestigationBriefBuilder
from app.ai.response_formatter import ResponseFormatter

async def main():
    queries = [
        "Open FIR KSP-000012", # Murder
        "Open FIR KSP-000004", # Theft
        "Open FIR KSP-000123", # Cyber Fraud
        "Open FIR KSP-000346", # Kidnapping
    ]
    
    for q in queries:
        print(f"\n===========================================================")
        print(f"RUNTIME PROOF FOR QUERY: '{q}'")
        print(f"===========================================================\n")
        
        db = SessionLocal()
        try:
            context = PipelineRunner.run(q, db)
            
            print("--- 1. PIPELINE EXECUTION ORDER ---")
            trace = getattr(context, 'execution_trace', [])
            for step in trace:
                print(f"-> {step}")
                
            print("\n--- 2. CONTEXT.INVESTIGATION_REASONING OBJECT ---")
            reasoning = getattr(context, 'investigation_reasoning', None)
            pprint(reasoning)
            
            print("\n--- 3. INVESTIGATION BRIEF OBJECT ---")
            brief = InvestigationBriefBuilder.build(context)
            pprint(brief)
            
            print("\n--- 4. FINAL RENDERED RESPONSE ---")
            formatted_response = ResponseFormatter.format(context)
            print(formatted_response)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
        finally:
            db.close()

asyncio.run(main())
