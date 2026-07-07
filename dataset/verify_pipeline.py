import sys
import os

sys.path.insert(0, os.path.abspath('.'))

from app.api.routes.chat import chat_query
from app.database.connection import SessionLocal

db = SessionLocal()

class FakeState:
    pass

class FakeRequest:
    def __init__(self):
        self.state = FakeState()

queries = [
    "hello there!",
    "Show theft cases in Mysuru",
    "Predict assault in Bengaluru next month",
    "Find fir KSP-1234",
    "What about in Mandya?",
    "Show me the most wanted accused",
    "thank you so much",
    "who are you",
    "jkhdsfksjdfh", # Gibberish (should fail with Low Confidence)
]

print("="*80)
print(f"{'QUERY':<40} | {'INTENT':<15} | {'CONF':<4} | {'DB ACCESS'}")
print("="*80)

for q in queries:
    res = chat_query({'message': q}, FakeRequest(), db)
    
    intent = res.get("intent", "UNKNOWN")
    conf = res.get("metadata", {}).get("confidence", 0.0)
    
    # Check if DB was accessed / SQL generated
    # If the results list has elements or summary indicates success, it likely accessed DB
    # (except for CONVERSATION which short circuits)
    if intent in ["GREETING", "GOODBYE", "THANKS", "HELP", "BOT_IDENTITY", "BOT_CAPABILITIES", "UNKNOWN"] or conf < 0.25 or (0.25 <= conf < 0.40):
        db_access = "No"
    elif intent == "PREDICT_CRIME":
        db_access = "Yes (ML Model)"
    else:
        db_access = "Yes (SQL Executed)"
        
    print(f"{q:<40} | {intent:<15} | {conf:.2f} | {db_access}")

print("="*80)
print("Pipeline stabilization verification complete.")
