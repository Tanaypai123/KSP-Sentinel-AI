from app.database.connection import SessionLocal
from app.ai.pipeline_runner import PipelineRunner
from app.ai.investigation_brief_builder import InvestigationBriefBuilder
from app.ai.response_formatter import ResponseFormatter

db = SessionLocal()

print("--- 1. Testing Empty Search ---")
ctx = PipelineRunner.run("Search \"\"", db)
brief = InvestigationBriefBuilder.build(ctx)
print("Brief Exec Summary:", brief.executive_summary)
if brief.confidence_explanation:
    print("Confidence:", brief.confidence_explanation.score)
else:
    print("Confidence: None")

print("\n--- 2. Testing Invalid FIR ID ---")
ctx = PipelineRunner.run("Open FIR KSP-999999", db)
brief = InvestigationBriefBuilder.build(ctx)
print("Brief Exec Summary:", brief.executive_summary)

print("\n--- 3. Testing Ambiguous Follow-Up ---")
ctx = PipelineRunner.run("Who is the accused?", db)
brief = InvestigationBriefBuilder.build(ctx)
print("Brief Exec Summary:", brief.executive_summary)

db.close()
