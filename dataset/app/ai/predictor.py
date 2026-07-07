"""Real prediction engine for PREDICT_CRIME intent.

Queries historical CaseMaster records, aggregates by month, then applies:
  - Moving average    (primary estimator, window = 3)
  - Linear regression (trend line via least-squares, no external libs)

Returns a structured prediction dict that chat.py returns directly to the
caller.  This module uses SQLAlchemy directly and is completely independent
of sql_generator / query_executor.
"""

from __future__ import annotations

import statistics
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session

from app.models.case import CaseMaster
from app.models.crime import CrimeHead
from app.models.masters import District, Unit


# ---------------------------------------------------------------------------
# Pure-Python statistical helpers
# ---------------------------------------------------------------------------

def _moving_average(values: List[float], window: int = 3) -> float:
    """Return the moving average of the last *window* values."""
    tail = values[-window:] if len(values) >= window else values
    return sum(tail) / len(tail) if tail else 0.0


def _linear_regression(values: List[float]) -> Tuple[float, float]:
    """Return (slope, intercept) via OLS.  x = index 0..n-1, y = count."""
    n = len(values)
    if n < 2:
        return 0.0, float(values[0]) if values else 0.0
    x_mean = (n - 1) / 2.0
    y_mean = statistics.mean(values)
    num = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
    den = sum((i - x_mean) ** 2 for i in range(n))
    slope = num / den if den else 0.0
    intercept = y_mean - slope * x_mean
    return slope, intercept


def _predict_next(monthly_values: List[float]) -> int:
    """60 % moving-average + 40 % linear-regression blend, floored at 0."""
    n = len(monthly_values)
    if n == 0:
        return 0
    if n == 1:
        return max(0, int(round(monthly_values[0])))
    ma = _moving_average(monthly_values, window=3)
    slope, intercept = _linear_regression(monthly_values)
    lr_next = intercept + slope * n          # next index = n
    predicted = 0.6 * ma + 0.4 * lr_next
    return max(0, int(round(predicted)))


def _growth_rate(values: List[float]) -> float:
    """(recent-half mean − old-half mean) / old-half mean."""
    n = len(values)
    if n < 2:
        return 0.0
    half = max(1, n // 2)
    old_avg = statistics.mean(values[:half]) or 1.0
    new_avg = statistics.mean(values[half:]) or 0.0
    return (new_avg - old_avg) / old_avg


def _risk_level(growth: float) -> str:
    if growth >= 0.20:
        return "HIGH"
    if growth >= 0.05:
        return "MEDIUM"
    return "LOW"


def _trend_label(growth: float) -> str:
    if growth >= 0.05:
        return "Increasing"
    if growth <= -0.05:
        return "Decreasing"
    return "Stable"


def _confidence(n_months: int) -> int:
    """Confidence % based on depth of historical data."""
    if n_months >= 24:
        return 90
    if n_months >= 12:
        return 75
    if n_months >= 6:
        return 55
    if n_months >= 3:
        return 35
    return 15


def _forecast_month_label() -> str:
    """Return next calendar month as 'YYYY-MM' string."""
    today = date.today()
    if today.month == 12:
        return f"{today.year + 1}-01"
    return f"{today.year}-{today.month + 1:02d}"


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

# Common alternate-name → canonical DB substring map.
# Keeps resolver decoupled from hard-coded IDs; only normalises the search term.
from app.ai.normalizer import normalize_district, normalize_crime_head

def _resolve_district_id(db: Session, name: str) -> Optional[int]:
    canonical = normalize_district(name) or name
    row = db.execute(
        select(District.district_id)
        .where(District.district_name.ilike(f"%{canonical}%"))
        .limit(1)
    ).first()
    return row[0] if row else None


def _resolve_crime_head_id(db: Session, name: str) -> Optional[int]:
    canonical = normalize_crime_head(name) or name
    row = db.execute(
        select(CrimeHead.crime_head_id)
        .where(CrimeHead.crime_group_name.ilike(f"%{canonical}%"))
        .limit(1)
    ).first()
    return row[0] if row else None


def _resolve_police_station_id(db: Session, name: str) -> Optional[int]:
    row = db.execute(
        select(Unit.unit_id)
        .where(Unit.unit_name.ilike(f"%{name}%"))
        .limit(1)
    ).first()
    return row[0] if row else None


def _fetch_monthly_counts(
    db: Session,
    district_id: Optional[int],
    crime_head_id: Optional[int],
    police_station_id: Optional[int],
) -> List[Tuple[int, int, int]]:
    """Return [(year, month, count)] sorted chronologically.

    Uses explicit column expressions for GROUP BY / ORDER BY so that the query
    works correctly on PostgreSQL, MySQL, and SQLite alike.
    """
    yr_col  = extract("year",  CaseMaster.crime_registered_date)
    mo_col  = extract("month", CaseMaster.crime_registered_date)
    cnt_col = func.count(CaseMaster.case_master_id)

    stmt = (
        select(yr_col.label("yr"), mo_col.label("mo"), cnt_col.label("cnt"))
        .where(CaseMaster.crime_registered_date.isnot(None))
        .group_by(yr_col, mo_col)
        .order_by(yr_col, mo_col)
    )

    if district_id is not None:
        stmt = stmt.join(
            Unit, CaseMaster.police_station_id == Unit.unit_id, isouter=True
        ).where(Unit.district_id == district_id)

    if crime_head_id is not None:
        stmt = stmt.where(CaseMaster.crime_major_head_id == crime_head_id)

    if police_station_id is not None:
        stmt = stmt.where(CaseMaster.police_station_id == police_station_id)

    # ---- DEBUG: print compiled SQL and active filters ----
    try:
        from sqlalchemy.dialects import postgresql
        compiled = stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
        print("\n[PREDICTOR DEBUG] Generated SQL:\n", str(compiled))
    except Exception as e:
        print("[PREDICTOR DEBUG] Could not compile SQL for display:", e)

    rows = db.execute(stmt).all()

    print(f"[PREDICTOR DEBUG] Rows returned from DB: {len(rows)}")
    print("[PREDICTOR DEBUG] Monthly counts:", [(int(r.yr), int(r.mo), int(r.cnt)) for r in rows])

    return [(int(r.yr), int(r.mo), int(r.cnt)) for r in rows]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def predict_crime(db: Session, parsed_query: Dict[str, Any]) -> Dict[str, Any]:
    """Predict next-month crime count from historical CaseMaster data.

    Args:
        db:           Active SQLAlchemy Session.
        parsed_query: Merged query dict produced by query_parser +
                      conversation_memory (contains 'entities').

    Returns:
        Prediction dict compatible with the PREDICT_CRIME API response.
    """
    entities: Dict[str, Any] = parsed_query.get("entities") or {}

    district_name       = entities.get("district")
    crime_head_name     = entities.get("crime_head") or entities.get("crime_major_head")
    police_station_name = entities.get("police_station")

    # ---- Resolve entity strings → primary-key IDs ----
    district_id       = _resolve_district_id(db, district_name)             if district_name       else None
    crime_head_id     = _resolve_crime_head_id(db, crime_head_name)         if crime_head_name     else None
    police_station_id = _resolve_police_station_id(db, police_station_name) if police_station_name else None

    print("\n[PREDICTOR DEBUG] ---- Filter Resolution ----")
    print(f"[PREDICTOR DEBUG]  district_name       = {district_name!r}  -> district_id       = {district_id}")
    print(f"[PREDICTOR DEBUG]  crime_head_name     = {crime_head_name!r}  -> crime_head_id     = {crime_head_id}")
    print(f"[PREDICTOR DEBUG]  police_station_name = {police_station_name!r}  -> police_station_id = {police_station_id}")

    # ---- Pull historical monthly counts ----
    rows = _fetch_monthly_counts(db, district_id, crime_head_id, police_station_id)

    historical_counts = [
        {"year": yr, "month": mo, "count": cnt} for yr, mo, cnt in rows
    ]

    forecast_month = _forecast_month_label()

    # ---- No data fallback ----
    if not rows:
        fallback_reason = (
            "No historical records found for the given filters "
            "(district, crime type, or police station may not match any data). "
            "Prediction defaulted to 0 with UNKNOWN risk."
        )
        return {
            "predicted_cases":   0,
            "risk_level":        "UNKNOWN",
            "confidence":        0,
            "trend":             "Unknown",
            "reasoning":         fallback_reason,
            "historical_counts": [],
            "forecast_month":    forecast_month,
            "model_used":        "No model applied — insufficient data",
            "data_points_used":  0,
        }

    # ---- Compute prediction ----
    values: List[float] = [float(r[2]) for r in rows]
    n_months  = len(values)
    predicted = _predict_next(values)
    growth    = _growth_rate(values)
    risk      = _risk_level(growth)
    trend     = _trend_label(growth)
    conf      = _confidence(n_months)

    # ---- Build reasoning string ----
    filter_parts: List[str] = []
    if district_name:
        filter_parts.append(f"district '{district_name}'")
    if crime_head_name:
        filter_parts.append(f"crime type '{crime_head_name}'")
    if police_station_name:
        filter_parts.append(f"police station '{police_station_name}'")
    filter_desc = " and ".join(filter_parts) if filter_parts else "all available records"

    recent_avg = round(_moving_average(values, window=3), 1)

    # Explain fallback if data is sparse
    method_note = ""
    if n_months < 3:
        method_note = (
            " Only 1–2 data points available; prediction is based on the "
            "observed average (no regression applied)."
        )

    reasoning = (
        f"Based on {n_months} month(s) of historical data for {filter_desc}. "
        f"Recent 3-month average: {recent_avg} cases/month. "
        f"Growth rate vs earlier period: {round(growth * 100, 1)}%. "
        f"Prediction blends 60% moving average + 40% linear regression."
        f"{method_note}"
    )

    return {
        "predicted_cases":   predicted,
        "risk_level":        risk,
        "confidence":        conf,
        "trend":             trend,
        "reasoning":         reasoning,
        "historical_counts": historical_counts,
        "forecast_month":    forecast_month,
        "model_used":        "Moving Average + Linear Regression",
        "data_points_used":  n_months,
    }
