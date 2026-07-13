import app.ai.intent_router
from app.database.connection import SessionLocal
db = SessionLocal()
res = app.ai.intent_router.IntentRouter.detect('Explain recommendation', True, False)
print('intent:', res.intent)
print('is_conversational:', res.is_conversational)
print('clarification_required:', res.clarification_required)
db.close()
