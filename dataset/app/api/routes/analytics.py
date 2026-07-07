"""FastAPI router for global analytical distributions and metrics dashboard.
"""

from __future__ import annotations

import time
from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.analytics import AnalyticsService
from app.core.cache import global_cache

router = APIRouter()


@router.get("/dashboard", response_model=Dict[str, Any])
def get_dashboard_analytics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Retrieve unified analytical counts across crimes, districts, stations, and months.

    Utilizes 5-minute intelligent cache to accelerate responses.
    """
    cache_key = "global_dashboard_analytics"
    cached = global_cache.get(cache_key)
    if cached:
        # Update hit metadata
        cached["metadata"]["cache_hit"] = True
        return cached

    start_time = time.time()
    
    top_crimes = AnalyticsService.get_top_crimes(db)
    top_districts = AnalyticsService.get_top_districts(db)
    top_stations = AnalyticsService.get_top_stations(db)
    monthly_counts = AnalyticsService.get_monthly_counts(db)
    status_dist = AnalyticsService.get_status_distribution(db)
    gender_dist = AnalyticsService.get_gender_distribution(db)
    age_dist = AnalyticsService.get_age_distribution(db)

    execution_time = (time.time() - start_time) * 1000

    response = {
        "success": True,
        "top_crimes": top_crimes,
        "top_districts": top_districts,
        "top_stations": top_stations,
        "monthly_crime_counts": monthly_counts,
        "status_distribution": status_dist,
        "gender_distribution": gender_dist,
        "age_distribution": age_dist,
        "metadata": {
            "execution_time_ms": round(execution_time, 2),
            "cache_hit": False
        }
    }

    # Store in cache
    global_cache.set(cache_key, response)
    return response
