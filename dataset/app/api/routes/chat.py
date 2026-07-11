import logging
import time
from typing import Dict, Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database.connection import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/query", response_model=Dict[str, Any])
async def chat_query(payload: Dict[str, Any], request: Request, db: Session = Depends(get_db)):
    """
    Handle natural language queries by parsing, executing, and formatting results.
    Delegates entirely to SearchService.
    """
    start_time = time.time()
    query = payload.get("message", "").strip()

    if not query:
        return {
            "success": False,
            "intent": "UNKNOWN",
            "summary": "Please enter a valid query.",
            "count": 0,
            "entities": {},
            "results": [],
            "metadata": {"query_time_ms": 0.0, "cache_hit": False, "confidence": 0.0},
            "error": "Query message cannot be empty."
        }

    try:
        from app.services.search_service import SearchService
        conversation_id = payload.get("conversation_id")
        res = await SearchService.search_async(query, db, conversation_id=conversation_id)
        res["metadata"]["query"] = query
        
        # Determine actual rows retrieved vs scanned for backwards compatibility if needed
        if res.get("intent") != "PREDICT_CRIME" and "rows_scanned" not in res["metadata"]:
            res["metadata"]["rows_scanned"] = res.get("count", 0)
            res["metadata"]["rows_returned"] = len(res.get("results", []))
            
        # Store intent in request state for middleware
        request.state.intent = res.get("intent", "UNKNOWN")
        
        return res
    except Exception as e:
        logger.exception(f"Unexpected error in chat_query: {e}")
        duration = (time.time() - start_time) * 1000
        return {
            "success": False,
            "intent": "UNKNOWN",
            "summary": "An unexpected error occurred while processing your request.",
            "count": 0,
            "entities": {},
            "results": [],
            "metadata": {
                "query": query,
                "suggestions": ["Show theft cases", "Open FIR KSP-0001"],
                "confidence": 0.0,
                "query_time_ms": round(duration, 2),
                "cache_hit": False
            },
            "error": "Internal server error"
        }
