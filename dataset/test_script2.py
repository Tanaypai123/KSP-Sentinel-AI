from app.ai.intent_classifier import classify_intent_with_confidence

queries = [
    "Show FIR KSP-1001",
    "Crime No 120/2026",
    "Open FIR KSP-1001"
]

for q in queries:
    intent, conf = classify_intent_with_confidence(q)
    print(f"Q: {q}")
    print(f"  Intent: {intent}")
    print(f"  Confidence: {conf}")
