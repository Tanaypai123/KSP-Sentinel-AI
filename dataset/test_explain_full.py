from app.database.connection import SessionLocal
from app.ai.pipeline_runner import PipelineRunner
from app.ai.conversation_engine import ConversationEngine

db = SessionLocal()
sid = "explain_full"
ConversationEngine.reset(sid)
PipelineRunner.run("Open FIR KSP-000070", db, conversation_id=sid)
ctx = PipelineRunner.run("Explain recommendation", db, conversation_id=sid)
# Print full summary
summary = (ctx.response or {}).get("summary", "")
print("FULL SUMMARY:")
print(summary[:600])
db.close()
