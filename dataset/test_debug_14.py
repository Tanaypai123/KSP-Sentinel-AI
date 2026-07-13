from app.database.connection import SessionLocal
from app.ai.pipeline_runner import PipelineRunner
from app.ai.conversation_engine import ConversationEngine

db = SessionLocal()
sid = "bug14"
ConversationEngine.reset(sid)
PipelineRunner.run("Open FIR KSP-000070", db, conversation_id=sid)
ctx = PipelineRunner.run("Generate report", db, conversation_id=sid)
print("Intent:", ctx.intent)
if ctx.response:
    print("Summary:", ctx.response.get("summary")[:200])
