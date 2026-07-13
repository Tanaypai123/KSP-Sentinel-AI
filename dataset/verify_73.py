import asyncio
from app.database.connection import SessionLocal
from app.ai.pipeline_runner import PipelineRunner
from app.ai.response_formatter import ResponseFormatter

async def main():
    queries = [
        "Open FIR KSP-000004", # Theft
        "Open FIR KSP-000123", # Cyber Fraud
    ]
    for q in queries:
        print(f"\n======================================")
        print(f"QUERY: {q}")
        print(f"======================================\n")
        db = SessionLocal()
        try:
            context = PipelineRunner.run(q, db)
            formatted_response = ResponseFormatter.format(context)
            print(formatted_response)
        except Exception as e:
            import traceback
            traceback.print_exc()
        finally:
            db.close()

asyncio.run(main())
