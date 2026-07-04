from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.ai.intent_classifier import classify_intent
from app.ai.query_parser import parse_query
from app.ai.sql_generator import generate_select
from app.ai.query_executor import execute_query

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

    # Step 1
    detected_intent = classify_intent(query)

    # Step 2
    parsed_query = parse_query(query)

    if detected_intent is not None:
        parsed_query["intent"] = detected_intent.value

    if parsed_query.get("intent") is None:
        raise HTTPException(
            status_code=400,
            detail="Unable to classify query."
        )

    # Step 3
    select_stmt = generate_select(parsed_query)

    # Step 4
    results = execute_query(db, select_stmt)

    return {
        "success": True,
        "query": query,
        "intent": parsed_query["intent"],
        "entities": parsed_query["entities"],
        "count": len(results),
        "results": results,
    }