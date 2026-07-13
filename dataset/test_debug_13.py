from app.database.connection import SessionLocal
from app.ai.pipeline_runner import PipelineRunner
from app.ai.conversation_engine import ConversationEngine
from app.ai.response_formatter import ResponseFormatter

db = SessionLocal()
sid = "debug13"
ConversationEngine.reset(sid)
PipelineRunner.run("Open FIR KSP-000070", db, conversation_id=sid)
ctx = PipelineRunner.run("Explain recommendation", db, conversation_id=sid)
print("Intent:", ctx.intent)
print("raw_query:", ctx.raw_query)
print("response keys:", (ctx.response or {}).keys())
# Check if ResponseFormatter.format was called
q_low = ctx.raw_query.lower()
print("explain in q_low:", "explain" in q_low)
result = ResponseFormatter._render_explain(ctx, q_low)
print("_render_explain result:", result[:300] if result else "(empty)")
db.close()
