from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.connection import get_db

router = APIRouter()


@router.get("", status_code=200)
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint.
    Validates database connection readiness and reports health status.
    """
    db_status = "unhealthy"
    try:
        # Check connection validity by executing simple query
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        # DB connection could fail or be offline
        pass

    return {
        "status": "online" if db_status == "healthy" else "degraded",
        "database": db_status,
        "service": "KSP Sentinel AI Operations Engine",
    }
