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
    assert set(EntityExtractor.parse_identifier("Crime No 120/2026")) == {"120/2026", "120-2026"}
    assert set(EntityExtractor.parse_identifier("Crime Number 120/2026")) == {"120/2026", "120-2026"}
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
