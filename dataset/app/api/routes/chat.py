import logging
import time
import re
from typing import Dict, Any, List

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.ai.intent_classifier import classify_intent_with_confidence
from app.ai.query_parser import parse_query
from app.ai.sql_generator import generate_select
from app.ai.query_executor import execute_query
from app.ai.response_formatter import format_response
from app.ai.conversation_memory import merge_with_last, update_state
from app.ai.insights import IntelligenceEngine
from app.services.analytics import AnalyticsService
from app.core.cache import global_cache

logger = logging.getLogger("ksp-sentinel-backend.chat")
router = APIRouter()

# Default suggested queries for clarifications
_DEFAULT_SUGGESTIONS = [
    "Show theft in Mysuru",
    "Crime trend in Bengaluru Urban",
    "Top hotspots",
    "Predict theft next month in Mysuru"
]


@router.post("/query", response_model=Dict[str, Any])
def chat_query(payload: Dict[str, Any], request: Request, db: Session = Depends(get_db)):
    """
    Execute an AI investigation query, routing by intent.

    Supports caching, explainability, insights, case summary details, and metadata.
    """
    query = payload.get("message", "").strip()
    start_time = time.time()

    if not query:
        return {
            "success": False,
            "intent": "UNKNOWN",
            "summary": "Query message cannot be empty.",
            "count": 0,
            "entities": {},
            "results": [],
            "metadata": {"query_time_ms": 0.0, "cache_hit": False},
            "error": "Query message cannot be empty."
        }

    # Step 1: Detect intent and confidence score
    intent, confidence = classify_intent_with_confidence(query)
    intent_val = intent.value if intent else "UNKNOWN"
    request.state.intent = intent_val

    # Step 2: In-memory Cache Lookup (Skip for PREDICT_CRIME)
    if intent_val != "PREDICT_CRIME":
        cache_key = f"chat_{query.lower().strip()}"
        cached = global_cache.get(cache_key)
        if cached:
            duration = (time.time() - start_time) * 1000
            cached["metadata"]["cache_hit"] = True
            cached["metadata"]["query_time_ms"] = round(duration, 2)
            logger.info(f"CACHE HIT | Query: {query!r} | Time: {duration:.2f}ms")
            request.state.cache_hit = True
            return cached

    request.state.cache_hit = False

    try:
        # Step 3: Detect multiple commands
        crime_keywords = ["theft", "assault", "murder", "rape", "kidnapping", "robbery", "burglary"]
        detected_crimes = [c for c in crime_keywords if re.search(r"\b" + re.escape(c) + r"\b", query.lower())]
        has_multiple_verbs = len(re.findall(r"\b(show|predict|trend|hotspot)\b", query.lower())) > 1
        
        if len(detected_crimes) > 1 or has_multiple_verbs:
            duration = (time.time() - start_time) * 1000
            logger.warning(f"NLP LOG | Multiple commands detected: {detected_crimes} | Query: {query!r} | Time: {duration:.2f}ms")
            return {
                "success": False,
                "intent": "UNKNOWN",
                "summary": "I detected multiple commands. Which one should I execute?",
                "count": 0,
                "entities": {},
                "results": [],
                "metadata": {
                    "query": query,
                    "suggestions": [f"Show {c} cases" for c in detected_crimes] if detected_crimes else _DEFAULT_SUGGESTIONS,
                    "query_time_ms": round(duration, 2),
                    "cache_hit": False
                },
                "error": "Multiple commands detected"
            }

        # Step 4: Low confidence handling
        if confidence < 0.55:
            duration = (time.time() - start_time) * 1000
            logger.warning(f"NLP LOG | Low confidence intent classification: {confidence} | Query: {query!r}")
            return {
                "success": False,
                "intent": "UNKNOWN",
                "summary": "I'm not sure what you mean. Did you mean to look up cases, view trends, or run a prediction?",
                "count": 0,
                "entities": {},
                "results": [],
                "metadata": {
                    "query": query,
                    "suggestions": _DEFAULT_SUGGESTIONS,
                    "confidence": confidence,
                    "query_time_ms": round(duration, 2),
                    "cache_hit": False
                },
                "error": "Low intent confidence"
            }

        # Step 5: Parse current query and merge with memory context
        parsed_query = parse_query(query, db)
        merged_query = merge_with_last(parsed_query)

        # Apply detected intent
        if intent is not None:
            merged_query["intent"] = intent_val

        entities = merged_query.get("entities", {})

        # Step 6: Check for invalid district lookup (Fuzzy match threshold check)
        is_valid_district = entities.get("structured_is_valid_district", True)
        if not is_valid_district:
            raw_d = entities.get("structured_raw_district")
            suggestions = entities.get("structured_district_suggestions") or ["Mysuru", "Mandya", "Bengaluru Urban"]
            suggest_str = ", ".join(suggestions)
            duration = (time.time() - start_time) * 1000
            
            logger.warning(f"NLP LOG | Invalid district check failed: {raw_d!r} | Suggestions: {suggestions}")
            return {
                "success": False,
                "intent": intent_val,
                "summary": f"District \"{raw_d}\" not found. Did you mean: {suggest_str}?",
                "count": 0,
                "entities": entities,
                "results": [],
                "metadata": {
                    "query": query,
                    "suggestions": [f"Show cases in {s}" for s in suggestions],
                    "query_time_ms": round(duration, 2),
                    "cache_hit": False
                },
                "error": f"District \"{raw_d}\" not found"
            }

        # ------------------------------------------------------------------
        # PREDICT_CRIME: bypass SQL generator and query executor entirely.
        # ------------------------------------------------------------------
        if intent_val == "PREDICT_CRIME":
            from app.ai.predictor import predict_crime
            prediction = predict_crime(db, merged_query)
            update_state(merged_query)

            duration = (time.time() - start_time) * 1000
            
            # Formulate prediction explanation
            explanation = {
                "intent": "PREDICT_CRIME",
                "entities": {k: v for k, v in entities.items() if v is not None and not k.startswith("structured_")},
                "reasoning": prediction.get("reasoning"),
                "filters": [f"{k}={v}" for k, v in entities.items() if v and not k.startswith("structured_")],
                "sql_summary": "None (Predictive OLS Model)",
                "algorithm": prediction.get("model_used"),
                "confidence": prediction.get("confidence"),
                "trend_direction": prediction.get("trend"),
                "risk_level": prediction.get("risk_level"),
                "historical_data_used": f"{prediction.get('data_points_used')} monthly records"
            }

            insights = IntelligenceEngine.generate_insights(db, intent_val, entities)
            recs = IntelligenceEngine.generate_recommendations(intent_val, entities)

            return {
                "success": True,
                "intent": "PREDICT_CRIME",
                "summary": prediction.get("reasoning"),
                "count": prediction.get("predicted_cases", 0),
                "entities": entities,
                "results": prediction.get("historical_counts", []),
                "metadata": {
                    "prediction": prediction,
                    "query": query,
                    "confidence": confidence,
                    "query_time_ms": round(duration, 2),
                    "cache_hit": False,
                    "rows_scanned": prediction.get("data_points_used"),
                    "rows_returned": 1
                },
                "insights": insights,
                "recommended_queries": recs,
                "explanation": explanation,
                "prediction": prediction  # Frontend compatibility
            }

        # Step 7: Generate SQL using merged query
        select_stmt = generate_select(merged_query)

        # Step 8: Execute query
        results = execute_query(db, select_stmt)

        # Persist state for next turn
        update_state(merged_query)

        # Format human-friendly summary
        try:
            formatted = format_response(intent_val, results, entities)
        except Exception as fe:
            logger.error(f"Error formatting response: {fe}")
            formatted = {
                "summary": f"Found {len(results)} matching records.",
                "count": len(results),
                "results": results,
            }

        # Step 9: Post-process results with intelligence
        # A. Case summaries for FIR rows
        if intent_val in ["SEARCH_CASES", "SEARCH_VICTIMS"]:
            unit_map = AnalyticsService.get_unit_map(db)
            status_names = {
                1: "under investigation",
                2: "under trial",
                3: "closed",
                4: "under review"
            }
            for row in formatted["results"]:
                if isinstance(row, dict) and "crime_no" in row:
                    status_id = row.get("status")
                    status_str = status_names.get(status_id, "investigation")
                    reg_date = row.get("crime_registered_date")
                    station_id = row.get("police_station_id")
                    station_name = unit_map.get(station_id, "Unknown Police Station")
                    date_str = str(reg_date) if reg_date else "Unknown Date"
                    # Add FIR summary
                    row["fir_summary"] = f"The case is {status_str} and was registered on {date_str} at {station_name}."

        # B. Hotspots Intelligence
        elif intent_val == "HOTSPOT":
            formatted["results"] = IntelligenceEngine.calculate_hotspot_intelligence(formatted["results"])

        # C. Trend Analytics
        trend_analytics = {}
        if intent_val == "CRIME_TREND":
            monthly_counts = AnalyticsService.get_monthly_counts(db)
            trend_analytics = IntelligenceEngine.calculate_trend_analytics(monthly_counts)

        # Step 10: Generate insights and recommendations
        insights = IntelligenceEngine.generate_insights(db, intent_val, entities)
        recs = IntelligenceEngine.generate_recommendations(intent_val, entities)
        explanation = IntelligenceEngine.generate_explanation(intent_val, entities, select_stmt)

        duration = (time.time() - start_time) * 1000
        
        response = {
            "success": True,
            "intent": intent_val,
            "summary": formatted["summary"],
            "count": formatted["count"],
            "entities": entities,
            "results": formatted["results"],
            "metadata": {
                "query": query,
                "confidence": confidence,
                "raw_results_count": len(results),
                "query_time_ms": round(duration, 2),
                "cache_hit": False,
                "rows_scanned": len(results),
                "rows_returned": len(formatted["results"]),
                "trend_analytics": trend_analytics
            },
            "insights": insights,
            "recommended_queries": recs,
            "explanation": explanation
        }

        # Step 11: Set in cache (only for successful non-prediction requests)
        cache_key = f"chat_{query.lower().strip()}"
        global_cache.set(cache_key, response)

        return response

    except Exception as e:
        logger.error(f"Unexpected error in chat_query: {e}", exc_info=True)
        duration = (time.time() - start_time) * 1000
        return {
            "success": False,
            "intent": "UNKNOWN",
            "summary": f"An unhandled error occurred: {str(e)}",
            "count": 0,
            "entities": {},
            "results": [],
            "metadata": {
                "query": query,
                "query_time_ms": round(duration, 2),
                "cache_hit": False
            },
            "error": str(e)
        }
