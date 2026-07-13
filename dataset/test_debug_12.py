from app.database.connection import SessionLocal
from app.ai.pipeline_runner import PipelineRunner
from app.ai.conversation_engine import ConversationEngine

db = SessionLocal()
sid2 = "debug12"
ConversationEngine.reset(sid2)
ctx2 = PipelineRunner.run("Show repeat offenders", db, conversation_id=sid2)
print("Intent:", ctx2.intent)
print("timeline_report:", ctx2.timeline_report)
print("search_result count:", len(ctx2.search_result or []))
print("search_result[0]:", (ctx2.search_result or [{}])[0] if ctx2.search_result else "NONE")
print("Summary:", (ctx2.response or {}).get("summary","")[:400])
db.close()
