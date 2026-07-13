from app.database.connection import SessionLocal
from app.ai.pipeline_runner import PipelineRunner
from app.ai.conversation_engine import ConversationEngine

db = SessionLocal()

# Bug 11: Previous FIR
print("="*60)
print("BUG 11: Previous FIR")
sid = "bug11"
ConversationEngine.reset(sid)
PipelineRunner.run("Open FIR KSP-000070", db, conversation_id=sid)
PipelineRunner.run("Open FIR KSP-000071", db, conversation_id=sid)
state = ConversationEngine.get_state(sid)
print("Active records:", [r.get("crime_no") for r in state._active_records])
ctx = PipelineRunner.run("Show previous FIR", db, conversation_id=sid)
print("Intent:", ctx.intent)
print("Summary:", (ctx.response or {}).get("summary","")[:200])

# Bug 12: Repeat Offender
print("\n"+"="*60)
print("BUG 12: Repeat Offender")
sid2 = "bug12"
ConversationEngine.reset(sid2)
ctx2 = PipelineRunner.run("Show repeat offenders", db, conversation_id=sid2)
print("Intent:", ctx2.intent)
print("Summary:", (ctx2.response or {}).get("summary","")[:300])

# Bug 13: Explain recommendation
print("\n"+"="*60)
print("BUG 13: Explain recommendation")
sid3 = "bug13"
ConversationEngine.reset(sid3)
PipelineRunner.run("Open FIR KSP-000070", db, conversation_id=sid3)
ctx3 = PipelineRunner.run("Explain recommendation", db, conversation_id=sid3)
print("Intent:", ctx3.intent)
print("Summary:", (ctx3.response or {}).get("summary","")[:400])

db.close()
