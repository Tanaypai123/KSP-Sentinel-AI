import sys
import os

# Ensure the parent directory is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.ai.entity_extractor import EntityExtractor
from app.ai.intent_classifier import Intent, classify_intent_with_confidence

def test_generic_identifier_normalization():
    # FIR numbers with "KSP" prefix
    assert "1" in EntityExtractor.parse_identifier("KSP-1")
    assert "KSP-1" in EntityExtractor.parse_identifier("KSP-1")
    assert "1" in EntityExtractor.parse_identifier("FIR KSP-1")
    assert "KSP0001" in EntityExtractor.parse_identifier("FIR KSP0001")
    assert "KSP-0001" in EntityExtractor.parse_identifier("FIR KSP-0001")
    assert "12" in EntityExtractor.parse_identifier("Open FIR KSP-12")

    # Pure numeric / slash identifiers
    assert "145" in EntityExtractor.parse_identifier("Case 145")
    
    # Slashes and hyphens
    assert "120/2026" in EntityExtractor.parse_identifier("Crime No 120/2026")
    assert "120/2026" in EntityExtractor.parse_identifier("Crime Number 120/2026")
    assert "1" in EntityExtractor.parse_identifier("FIR 1")

def test_generic_numeric_filters():
    # Age > 40
    res = EntityExtractor.parse_numeric_filters("Age > 40".lower())
    assert any(f["attribute"] == "age" and f["operator"] == "gt" and f["value"] == 40 for f in res)

    # Age < 25
    res = EntityExtractor.parse_numeric_filters("Age < 25".lower())
    assert any(f["attribute"] == "age" and f["operator"] == "lt" and f["value"] == 25 for f in res)

    # Older than 40
    res = EntityExtractor.parse_numeric_filters("Older than 40".lower())
    assert any(f["attribute"] == "age" and f["operator"] == "gt" and f["value"] == 40 for f in res)

    # Younger than 25
    res = EntityExtractor.parse_numeric_filters("Younger than 25".lower())
    assert any(f["attribute"] == "age" and f["operator"] == "lt" and f["value"] == 25 for f in res)

    # More than 10 cases
    res = EntityExtractor.parse_numeric_filters("More than 10 cases".lower())
    assert any(f["attribute"] == "cases" and f["operator"] == "gt" and f["value"] == 10 for f in res)

    # Less than 5 FIRs
    res = EntityExtractor.parse_numeric_filters("Less than 5 FIRs".lower())
    assert any(f["attribute"] == "cases" and f["operator"] == "lt" and f["value"] == 5 for f in res)

def test_generic_analytics_intent():
    # Verify these map to CRIME_TREND
    trends = [
        "Top crimes",
        "Top crime categories",
        "Crime category ranking",
        "Most common crimes",
        "Crime distribution",
        "Crime breakdown",
        "Crime analysis",
        "Highest crime categories",
        "Crime frequency"
    ]
    for q in trends:
        intent, conf = classify_intent_with_confidence(q)
        assert intent == Intent.CRIME_TREND, f"Failed on '{q}', got {intent}"
        assert conf > 0.5

def test_conversational_intents():
    from app.ai.pipeline.classifier import classify_pipeline_intent
    from app.ai.pipeline.normalizer import normalize_text
    
    cases = {
        "hello there": "GREETING",
        "good morning": "GREETING",
        "goodbye": "GOODBYE",
        "thanks a lot": "THANKS",
        "help me": "HELP",
        "who are you": "BOT_IDENTITY",
        "what can you do": "BOT_CAPABILITIES",
        "djfhkdshfsdf": "UNKNOWN",
        "asdfgh": "UNKNOWN",
        "123456": "UNKNOWN"
    }
    
    for q, expected in cases.items():
        intent, _ = classify_pipeline_intent(normalize_text(q))
        intent_val = intent.value if hasattr(intent, 'value') else str(intent)
        assert intent_val == expected, f"Failed on '{q}', got {intent_val}"

def test_canonical_crimes():
    assert EntityExtractor.parse_crime_type("armed robbery") == "robbery"
    assert EntityExtractor.parse_crime_type("chain snatching") == "snatching"
    assert EntityExtractor.parse_crime_type("cyber fraud") == "cyber_crime"
    assert EntityExtractor.parse_crime_type("wife beating") == "domestic_violence"
    assert EntityExtractor.parse_crime_type("stolen property") == "theft"
    assert EntityExtractor.parse_crime_type("hit and run") == "traffic"
    assert EntityExtractor.parse_crime_type("missing child") == "kidnapping"
    assert EntityExtractor.parse_crime_type("drug offence") == "narcotics"
    assert EntityExtractor.parse_crime_type("protest violence") == "rioting"
    assert EntityExtractor.parse_crime_type("blackmail") == "extortion"
    assert EntityExtractor.parse_crime_type("burning") == "arson"
    assert EntityExtractor.parse_crime_type("car theft") == "vehicle_theft"
