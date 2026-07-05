from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.ai.intent_classifier import classify_intent
from app.ai.query_parser import parse_query
from app.ai.sql_generator import generate_select
from app.ai.query_executor import execute_query
from app.ai.response_formatter import format_response
# Conversation memory utilities
from app.ai.conversation_memory import get_last_state, merge_with_last, update_state
router = APIRouter()


@router.post("/query", response_model=Dict[str, Any])
def chat_query(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Execute an AI investigation query.

    Flow:
    Intent Classifier
        ↓
    Query Parser
        ↓
    SQL Generator
        ↓
    Query Executor
    """

    query = payload.get("message", "").strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="message field is required"
        )

    # Step 1: detect intent
    detected_intent = classify_intent(query)

    # Step 2: parse current query
    parsed_query = parse_query(query)

    # Merge with previous conversation context
    merged_query = merge_with_last(parsed_query)

    # Apply detected intent, overriding if present
    if detected_intent is not None:
        merged_query["intent"] = detected_intent.value
    elif merged_query.get("intent") is None:
        raise HTTPException(
            status_code=400,
            detail="Unable to classify query."
        )

    # Step 3: generate SQL using merged query
    select_stmt = generate_select(merged_query)

    # Step 4: execute query
    results = execute_query(db, select_stmt)

    # Persist the merged state for next turn
    update_state(merged_query)

    try:
        formatted = format_response(merged_query["intent"], results, merged_query.get("entities"))
    except Exception:
        formatted = {
            "summary": None,
            "count": len(results),
            "results": results,
        }

    return {
        "success": True,
        "query": query,
        "intent": merged_query["intent"],
        "entities": merged_query["entities"],
        "summary": formatted["summary"],
        "count": formatted["count"],
        "results": formatted["results"],
    }