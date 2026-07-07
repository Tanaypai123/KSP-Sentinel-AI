from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.connection import get_db

router = APIRouter()


from app.core.metrics import global_metrics
from app.core.cache import global_cache

@router.get("", status_code=200)
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint.
    Validates database connection, cache storage readiness, and exposes latency diagnostic metrics.
    """
    db_status = "unhealthy"
    try:
        # Check database connection readiness
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        pass

    # Check cache status
    cache_status = "healthy"
    try:
        global_cache.get("health_check_ping")
    except Exception:
        cache_status = "unhealthy"

    is_healthy = db_status == "healthy" and cache_status == "healthy"

    return {
        "status": "online" if is_healthy else "degraded",
        "database": db_status,
        "cache": cache_status,
        "api": "healthy",
        "uptime_seconds": round(global_metrics.uptime, 2),
        "version": "1.0.0",
        "metrics": {
            "request_count": global_metrics.request_count,
            "average_latency_ms": global_metrics.average_latency_ms,
            "cache_hits": global_metrics.cache_hits,
            "cache_misses": global_metrics.cache_misses,
            "errors_count": global_metrics.errors_count,
            "prediction_count": global_metrics.prediction_count,
            "analytics_count": global_metrics.analytics_count,
        }
    }
