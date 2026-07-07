"""
Comprehensive validation script for KSP Sentinel AI API.
Verifies all goals:
1. District normalization (Mysore -> Mysuru, Bangalore -> Bengaluru)
2. Aggregate counts (extracts scalar count instead of list length)
3. Hotspots (joins and returns unit/location name)
4. Trends (joins and returns crime_group_name)
5. Response standardization (success, intent, summary, count, entities, results, metadata)
6. Non-sticky memory for location entities (district, police_station, etc.)
7. SQL validation (no errors for blank or valid entities)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.database.connection import SessionLocal
from app.ai.query_parser import parse_query
from app.ai.conversation_memory import merge_with_last, update_state, _last_state
from app.ai.sql_generator import generate_select
from app.ai.query_executor import execute_query
from app.ai.response_formatter import format_response
from app.api.routes.chat import chat_query

# Re-init memory
_last_state["intent"] = None
_last_state["entities"] = {}

db = SessionLocal()

QUERIES_TO_TEST = [
    # 1. Search Cases with theft
    ("Search theft", "SEARCH_CASES"),
    # 2. Search by district (validates normalization Mysore -> mysuru)
    ("Show theft cases in Mysore", "SEARCH_CASES"),
    # 3. Non-sticky memory check (Should have district = None, even after Mysore query)
    ("Show theft cases", "SEARCH_CASES"),
    # 4. Aggregate count (checks scalar count extraction)
    ("How many cases in Mysuru", "AGGREGATE_COUNT"),
    # 5. Crime trend (checks crime_group_name in trend result)
    ("Crime trend in Mysuru", "CRIME_TREND"),
    # 6. Prediction
    ("Predict crime next month in Mysuru", "PREDICT_CRIME"),
    # 7. Hotspot (checks location name in hotspot result)
    ("Show hotspot in Mysuru", "HOTSPOT"),
    # 8. Accused search
    ("Find accused named Rajesh", "SEARCH_ACCUSED"),
]

SEP = "=" * 80

try:
    for query, expected_intent in QUERIES_TO_TEST:
        print(f"\n{SEP}")
        print(f"TEST QUERY: {query!r}")
        print(f"EXPECTED INTENT: {expected_intent}")
        print(SEP)

        # Call chat_query route directly
        res = chat_query({"message": query}, db)

        # Assert format keys
        keys = ["success", "intent", "summary", "count", "entities", "results", "metadata"]
        all_keys_exist = all(k in res for k in keys)
        print(f"  Standardized Keys Exist: {all_keys_exist}")
        if not all_keys_exist:
            print(f"  Missing keys: {[k for k in keys if k not in res]}")

        # Check normalization & values
        print(f"  Result Intent: {res.get('intent')}")
        print(f"  Result Count: {res.get('count')}")
        print(f"  District Entity: {res.get('entities', {}).get('district')}")
        print(f"  Summary: {res.get('summary')}")
        
        # Check specific intent payloads
        if expected_intent == "PREDICT_CRIME":
            prediction = res.get("prediction")
            print(f"  Prediction Key Exists (compat check): {prediction is not None}")
            if prediction:
                print(f"    Predicted cases: {prediction.get('predicted_cases')}")
                print(f"    Confidence: {prediction.get('confidence')}%")
                print(f"    Risk level: {prediction.get('risk_level')}")
                print(f"    Reasoning: {prediction.get('reasoning')}")
        elif expected_intent == "HOTSPOT":
            results = res.get("results", [])
            print(f"  Hotspot rows returned: {len(results)}")
            if results:
                print(f"    First row sample: {results[0]}")
                print(f"    Location field name check: {'location' in results[0] and results[0]['location'] is not None}")
        elif expected_intent == "CRIME_TREND":
            results = res.get("results", [])
            print(f"  Trend rows returned: {len(results)}")
            if results:
                print(f"    First row sample: {results[0]}")
                print(f"    Crime group name check: {'crime_group_name' in results[0] and results[0]['crime_group_name'] is not None}")
        elif expected_intent == "SEARCH_ACCUSED":
            results = res.get("results", [])
            print(f"  Accused rows returned: {len(results)}")
            if results:
                print(f"    First row sample: {results[0]}")

finally:
    db.close()
