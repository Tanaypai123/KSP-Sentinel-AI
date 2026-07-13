from app.database.connection import SessionLocal
from app.ai.pipeline_runner import PipelineRunner
from app.ai.conversation_engine import ConversationEngine
from app.ai.response_formatter import ResponseFormatter
import app.ai.response_formatter as rf_mod

# Monkey-patch to trace
_orig = ResponseFormatter.format
def _traced_format(context, mode="officer"):
    q = getattr(context, 'raw_query', '')
    q_low = q.lower()
    print(f"  [FORMATTER] raw_query='{q}' explain_in_q={('explain' in q_low)}")
    result = _orig(context, mode=mode)
    print(f"  [FORMATTER] result[:100]={result[:100]!r}")
    return result
ResponseFormatter.format = staticmethod(_traced_format)

db = SessionLocal()
sid = "trace_exp"
ConversationEngine.reset(sid)
PipelineRunner.run("Open FIR KSP-000070", db, conversation_id=sid)
ctx = PipelineRunner.run("Explain recommendation", db, conversation_id=sid)
db.close()
