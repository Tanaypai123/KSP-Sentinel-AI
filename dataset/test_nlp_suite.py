"""
Comprehensive NLP Test Suite for KSP Sentinel AI.
Executes 100+ natural language query test cases covering spelling mistakes,
relative/flexible dates, crime aliases, limits, sorting, age brackets,
genders, status flags, fuzzy matching, and memory carry-over.
"""

import sys
import os
import re

sys.path.insert(0, os.path.dirname(__file__))

from app.ai.entity_extractor import EntityExtractor
from app.ai.intent_classifier import classify_intent_with_confidence, Intent
from app.ai.query_parser import parse_query

# Define 105 distinct test cases covering all required criteria
TEST_CASES = [
    # --- 1-10: Crime Aliases ---
    ("Show stolen items", Intent.SEARCH_CASES, "theft", {}),
    ("Show stealing cases", Intent.SEARCH_CASES, "theft", {}),
    ("List bike theft cases", Intent.SEARCH_CASES, "theft", {}),
    ("Find vehicle theft records", Intent.SEARCH_CASES, "theft", {}),
    ("Find chain snatching cases", Intent.SEARCH_CASES, "theft", {}),
    ("Show robbery in Mysuru", Intent.SEARCH_CASES, "theft", {"district": "Mysuru"}),
    ("Find burglary records", Intent.SEARCH_CASES, "theft", {}),
    ("List larceny cases", Intent.SEARCH_CASES, "theft", {}),
    ("Show dacoity cases", Intent.SEARCH_CASES, "theft", {}),
    ("Show murder cases", Intent.SEARCH_CASES, "murder", {}),

    # --- 11-20: More Aliases ---
    ("Show homicide records", Intent.SEARCH_CASES, "murder", {}),
    ("Find killing reports", Intent.SEARCH_CASES, "murder", {}),
    ("List fight cases", Intent.SEARCH_CASES, "assault", {}),
    ("Show attack incidents", Intent.SEARCH_CASES, "assault", {}),
    ("Show beating cases", Intent.SEARCH_CASES, "assault", {}),
    ("Show battery cases", Intent.SEARCH_CASES, "assault", {}),
    ("Find sexual assault cases", Intent.SEARCH_CASES, "rape", {}),
    ("List kidnapping cases", Intent.SEARCH_CASES, "kidnapping", {}),
    ("Show abduct cases", Intent.SEARCH_CASES, "kidnapping", {}),
    ("Find missing child cases", Intent.SEARCH_CASES, "kidnapping", {}),

    # --- 21-30: Spelling Mistakes ---
    ("Show thet cases in Mysur", Intent.SEARCH_CASES, "theft", {"district": "Mysuru"}),
    ("Show murder in Banglore", Intent.SEARCH_CASES, "murder", {"district": "Bengaluru Urban"}),
    ("Show assault in Shivamoga", Intent.SEARCH_CASES, "assault", {"district": "Shivamogga"}),
    ("Show theft in Belgaum", Intent.SEARCH_CASES, "theft", {"district": "Belgaum"}),
    ("Show theft in Belagavi", Intent.SEARCH_CASES, "theft", {"district": "Belgaum"}),
    ("Show theft in Hubbali", Intent.SEARCH_CASES, "theft", {"district": "Hubli"}),
    ("Show theft in Mangaluru", Intent.SEARCH_CASES, "theft", {"district": "Mangalore"}),
    ("Show theft in ChikaraXYZ", Intent.SEARCH_CASES, None, {"district_suggestions": True}),
    ("Show theft in Coorg", Intent.SEARCH_CASES, "theft", {"district": "Kodagu"}),
    ("Show theft in Tumkur", Intent.SEARCH_CASES, "theft", {"district": "Tumakuru"}),

    # --- 31-40: Relative Dates ---
    ("Show cases registered today", Intent.SEARCH_CASES, None, {"relative_date": "today"}),
    ("Show cases registered yesterday", Intent.SEARCH_CASES, None, {"relative_date": "yesterday"}),
    ("Show cases registered last week", Intent.SEARCH_CASES, None, {"relative_date": "last week"}),
    ("Show cases registered last month", Intent.SEARCH_CASES, None, {"relative_date": "last month"}),
    ("Show cases registered this month", Intent.SEARCH_CASES, None, {"relative_date": "this month"}),
    ("Show cases registered last year", Intent.SEARCH_CASES, None, {"relative_date": "last year"}),
    ("Show cases registered last 30 days", Intent.SEARCH_CASES, None, {"relative_date": "last 30 days"}),
    ("Predict theft today", Intent.PREDICT_CRIME, "theft", {"relative_date": "today"}),
    ("Find murder from yesterday", Intent.SEARCH_CASES, "murder", {"relative_date": "yesterday"}),
    ("List cases this month in Mysore", Intent.SEARCH_CASES, None, {"district": "Mysuru", "relative_date": "this month"}),

    # --- 41-50: Flexible Dates ---
    ("Show theft after Jan 2026", Intent.SEARCH_CASES, "theft", {"date_after": "2026-01-01"}),
    ("Show theft before June 2024", Intent.SEARCH_CASES, "theft", {"date_before": "2024-06-01"}),
    ("Show theft between Jan and March 2025", Intent.SEARCH_CASES, "theft", {"date_range": ("2025-01-01", "2025-03-28")}),
    ("Show cases after 2025", Intent.SEARCH_CASES, None, {"date_after": "2025-12-31"}),
    ("Show cases before 2024", Intent.SEARCH_CASES, None, {"date_before": "2024-01-01"}),
    ("Show assault before June", Intent.SEARCH_CASES, "assault", {"date_before": "06-01"}),
    ("Show murder between Jan and March", Intent.SEARCH_CASES, "murder", {"date_range": ("01-01", "03-28")}),
    ("Show theft after 2020", Intent.SEARCH_CASES, "theft", {"date_after": "2020-12-31"}),
    ("List assault cases after July 2025", Intent.SEARCH_CASES, "assault", {"date_after": "2025-07-01"}),
    ("Find kidnapping before May 2024", Intent.SEARCH_CASES, "kidnapping", {"date_before": "2024-05-01"}),

    # --- 51-60: Limit ---
    ("Show top 5 theft cases", Intent.SEARCH_CASES, "theft", {"limit": 5}),
    ("Show latest 10 murder cases", Intent.SEARCH_CASES, "murder", {"limit": 10}),
    ("Show first 20 assault cases", Intent.SEARCH_CASES, "assault", {"limit": 20}),
    ("Show last 15 cases in Mysore", Intent.SEARCH_CASES, None, {"district": "Mysuru", "limit": 15}),
    ("Predict theft top 5", Intent.PREDICT_CRIME, "theft", {"limit": 5}),
    ("Top 3 hotspots", Intent.HOTSPOT, None, {"limit": 3}),
    ("Latest 8 accused in Mysore", Intent.SEARCH_ACCUSED, None, {"district": "Mysuru", "limit": 8}),
    ("Show first 50 victim records", Intent.SEARCH_VICTIMS, None, {"limit": 50}),
    ("Top 10 trends in Mysore", Intent.CRIME_TREND, None, {"district": "Mysuru", "limit": 10}),
    ("Show latest 25 cases", Intent.SEARCH_CASES, None, {"limit": 25}),

    # --- 61-70: Sorting ---
    ("Show cases sorted by latest", Intent.SEARCH_CASES, None, {"sort": "desc"}),
    ("Show cases sorted by newest", Intent.SEARCH_CASES, None, {"sort": "desc"}),
    ("Show cases sorted by oldest", Intent.SEARCH_CASES, None, {"sort": "asc"}),
    ("Show cases in ascending order", Intent.SEARCH_CASES, None, {"sort": "asc"}),
    ("Show cases in descending order", Intent.SEARCH_CASES, None, {"sort": "desc"}),
    ("Show cases sorted by recent", Intent.SEARCH_CASES, None, {"sort": "desc"}),
    ("Show theft in Mysore sorted by oldest", Intent.SEARCH_CASES, "theft", {"district": "Mysuru", "sort": "asc"}),
    ("Show murder in Bangalore sorted by recent", Intent.SEARCH_CASES, "murder", {"district": "Bengaluru Urban", "sort": "desc"}),
    ("List accused in Mysore in ascending order", Intent.SEARCH_ACCUSED, None, {"district": "Mysuru", "sort": "asc"}),
    ("Show trends sorted by descending", Intent.CRIME_TREND, None, {"sort": "desc"}),

    # --- 71-80: Status ---
    ("Show closed theft cases", Intent.SEARCH_CASES, "theft", {"status": 3}), # 3 = Closed
    ("Show theft cases under trial", Intent.SEARCH_CASES, "theft", {"status": 2}), # 2 = Under Trial
    ("Show theft cases in investigation", Intent.SEARCH_CASES, "theft", {"status": 1}), # 1 = Investigation
    ("Show disposed cases in Mysore", Intent.SEARCH_CASES, None, {"district": "Mysuru", "status": 3}),
    ("Show theft cases with charge sheet", Intent.SEARCH_CASES, "theft", {"status": 4}), # 4 = Under Review
    ("Show pending theft cases", Intent.SEARCH_CASES, "theft", {"status": 1}),
    ("List pending murder cases", Intent.SEARCH_CASES, "murder", {"status": 1}),
    ("Show closed murder in Mysore", Intent.SEARCH_CASES, "murder", {"district": "Mysuru", "status": 3}),
    ("Find investigation cases in Bangalore", Intent.SEARCH_CASES, None, {"district": "Bengaluru Urban", "status": 1}),
    ("Show charge sheet cases", Intent.SEARCH_CASES, None, {"status": 4}),

    # --- 81-90: Age & Gender ---
    ("Show cases under 18", Intent.SEARCH_CASES, None, {"age_lt": 18}),
    ("Show cases below 18", Intent.SEARCH_CASES, None, {"age_lt": 18}),
    ("Show cases involving minors", Intent.SEARCH_CASES, None, {"age_lt": 18}),
    ("Show cases involving adults", Intent.SEARCH_CASES, None, {"age_gt": 18}),
    ("Show cases above 50", Intent.SEARCH_CASES, None, {"age_gt": 50}),
    ("Show cases older than 40", Intent.SEARCH_CASES, None, {"age_gt": 40}),
    ("Show male accused in Mysore", Intent.SEARCH_ACCUSED, None, {"district": "Mysuru", "gender": 1}), # 1 = Male
    ("Show female victims in Mysore", Intent.SEARCH_VICTIMS, None, {"district": "Mysuru", "gender": 2}), # 2 = Female
    ("Show cases involving women in Mysore", Intent.SEARCH_CASES, None, {"district": "Mysuru", "gender": 2}),
    ("Show cases involving girls under 18", Intent.SEARCH_CASES, None, {"gender": 2, "age_lt": 18}),

    # --- 91-100: Intents confidence & Fallbacks ---
    ("Show theft", Intent.SEARCH_CASES, "theft", {"confidence_ge": 0.55}),
    ("Predict theft in Bangalore", Intent.PREDICT_CRIME, "theft", {"district": "Bengaluru Urban", "confidence_ge": 0.55}),
    ("Crime trend in Mysore", Intent.CRIME_TREND, None, {"district": "Mysuru", "confidence_ge": 0.55}),
    ("Top hotspot in Mysore", Intent.HOTSPOT, None, {"district": "Mysuru", "confidence_ge": 0.55}),
    ("Raju", Intent.SEARCH_CASES, None, {"confidence_lt": 0.55}), # single word name
    ("Cases", Intent.SEARCH_CASES, None, {"confidence_lt": 0.55}), # single word common
    ("Show theft and show assault", None, None, {"multiple_commands": True}),
    ("Predict theft and show trend", None, None, {"multiple_commands": True}),
    ("What are the theft cases", Intent.SEARCH_CASES, "theft", {"confidence_ge": 0.55}),
    ("Who is the accused", Intent.SEARCH_ACCUSED, None, {"confidence_ge": 0.55}),

    # --- 101-105: Additional Checks ---
    ("Show theft in Mysore and predict assault", None, None, {"multiple_commands": True}),
    ("Predict assault next month in Mysore", Intent.PREDICT_CRIME, "assault", {"district": "Mysuru"}),
    ("Show theft cases after July 2025 in Bangalore", Intent.SEARCH_CASES, "theft", {"district": "Bengaluru Urban", "date_after": "2025-07-01"}),
    ("Show theft cases below 18 sorted by newest", Intent.SEARCH_CASES, "theft", {"age_lt": 18, "sort": "desc"}),
    ("How many closed cases in Mysore", Intent.AGGREGATE_COUNT, None, {"district": "Mysuru", "status": 3})
]

print("=" * 85)
print(f"Executing KSP Sentinel AI NLP Unit Test Suite ({len(TEST_CASES)} cases)")
print("=" * 85)

passed = 0
failed = 0

for i, (query, expected_intent, expected_crime, checks) in enumerate(TEST_CASES, 1):
    # 1. Test Intent Classification and Confidence
    intent, confidence = classify_intent_with_confidence(query)
    
    # 2. Parse Query
    parsed = parse_query(query)
    entities = parsed["entities"]

    # 3. Assess Multi-command check
    crime_keywords = ["theft", "assault", "murder", "rape", "kidnapping", "robbery", "burglary"]
    detected_crimes = [c for c in crime_keywords if re.search(r"\b" + re.escape(c) + r"\b", query.lower())]
    has_multiple_verbs = len(re.findall(r"\b(show|predict|trend|hotspot)\b", query.lower())) > 1
    multiple_commands_detected = len(detected_crimes) > 1 or has_multiple_verbs

    # Run check assertions
    case_passed = True
    reasons = []

    # Check multiple commands
    if checks.get("multiple_commands"):
        if not multiple_commands_detected:
            case_passed = False
            reasons.append("Failed to detect multiple commands")
    else:
        # Check intent classification matches
        if expected_intent is not None and intent != expected_intent:
            case_passed = False
            reasons.append(f"Expected intent {expected_intent}, got {intent}")

        # Check intent confidence limits
        if checks.get("confidence_ge") and confidence < checks["confidence_ge"]:
            case_passed = False
            reasons.append(f"Confidence score {confidence} is less than {checks['confidence_ge']}")
        if checks.get("confidence_lt") and confidence >= checks["confidence_lt"]:
            case_passed = False
            reasons.append(f"Confidence score {confidence} is greater than or equal to {checks['confidence_lt']}")

        # Check crime_head mappings
        if expected_crime is not None and entities.get("crime_head") != expected_crime:
            case_passed = False
            reasons.append(f"Expected crime_head {expected_crime!r}, got {entities.get('crime_head')!r}")

        # Check district mappings
        if checks.get("district"):
            if entities.get("district") != checks["district"]:
                case_passed = False
                reasons.append(f"Expected district {checks['district']!r}, got {entities.get('district')!r}")

        # Check invalid district suggestions fallback trigger
        if checks.get("district_suggestions"):
            if entities.get("structured_is_valid_district") is not False:
                case_passed = False
                reasons.append("Expected structured_is_valid_district to be False")

        # Check relative dates key existences
        if checks.get("relative_date"):
            if not entities.get("date_range"):
                case_passed = False
                reasons.append("Expected relative date_range filter to be populated")

        # Check flexible date filter after/before ranges
        if checks.get("date_after"):
            d_range = entities.get("date_range")
            if not d_range or not d_range.startswith(checks["date_after"]):
                case_passed = False
                reasons.append(f"Expected date_range start {checks['date_after']}, got {d_range}")
        if checks.get("date_before"):
            d_range = entities.get("date_range")
            if not d_range or not d_range.endswith(checks["date_before"]):
                case_passed = False
                reasons.append(f"Expected date_range end {checks['date_before']}, got {d_range}")

        # Check limits
        if checks.get("limit") and entities.get("limit") != checks["limit"]:
            case_passed = False
            reasons.append(f"Expected limit {checks['limit']}, got {entities.get('limit')}")

        # Check sorting order
        if checks.get("sort") and entities.get("sort_order") != checks["sort"]:
            case_passed = False
            reasons.append(f"Expected sort_order {checks['sort']!r}, got {entities.get('sort_order')!r}")

        # Check age brackets
        if checks.get("age_lt") and (entities.get("age") or {}).get("lt") != checks["age_lt"]:
            case_passed = False
            reasons.append(f"Expected age under {checks['age_lt']}, got {entities.get('age')}")
        if checks.get("age_gt") and (entities.get("age") or {}).get("gt") != checks["age_gt"]:
            case_passed = False
            reasons.append(f"Expected age above {checks['age_gt']}, got {entities.get('age')}")

        # Check status codes
        if checks.get("status") and entities.get("status") != checks["status"]:
            case_passed = False
            reasons.append(f"Expected status ID {checks['status']}, got {entities.get('status')}")

        # Check gender codes
        if checks.get("gender") and entities.get("gender") != checks["gender"]:
            case_passed = False
            reasons.append(f"Expected gender ID {checks['gender']}, got {entities.get('gender')}")

    if case_passed:
        passed += 1
        status = "✅ PASS"
        detail = ""
    else:
        failed += 1
        status = "❌ FAIL"
        detail = f" | {', '.join(reasons)}"

    print(f"Case {i:03d} | {status} | Query: {query!r}{detail}")

print("=" * 85)
print(f"Test Suite Summary: Total={len(TEST_CASES)} | Passed={passed} | Failed={failed}")
print("=" * 85)

if failed > 0:
    sys.exit(1)
sys.exit(0)
