from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db

router = APIRouter()


@router.post("/query", response_model=Dict[str, Any])
def execute_query(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Query the AI investigation workspace with questions about FIRs, accused, or location patterns.
    [STUB - LLM / AI engine execution logic pending]
    """
    query = payload.get("message", "")
    return {
        "query": query,
        "response": f"Acknowledged query: '{query}'. Sent to Sentinel-AI model core.",
        "status": "processed",
        "structured_data": {
            "summary": "Core analysis response pending",
            "entities": [],
            "actions": []
        }
    }
