"""
Standalone verification script — runs predict_crime() directly
against the real database for all three test queries and prints full debug info.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.database.connection import SessionLocal
from app.ai.predictor import (
    predict_crime,
    _resolve_district_id,
    _resolve_crime_head_id,
    _resolve_police_station_id,
    _fetch_monthly_counts,
)

QUERIES = [
    {
        "label": "Query 1 – Predict crime next month",
        "entities": {},
    },
    {
        "label": "Query 2 – Will theft increase in Mysore",
        "entities": {"district": "mysore"},
    },
    {
        "label": "Query 3 – Predict burglary in Bangalore next month",
        "entities": {"district": "bangalore", "crime_head": "burglary"},
    },
]

SEP = "=" * 70

db = SessionLocal()

try:
    for q in QUERIES:
        print(f"\n{SEP}")
        print(f"  {q['label']}")
        print(SEP)

        entities = q["entities"]
        district_name       = entities.get("district")
        crime_head_name     = entities.get("crime_head") or entities.get("crime_major_head")
        police_station_name = entities.get("police_station")

        # ---- Resolve IDs ----
        district_id       = _resolve_district_id(db, district_name)             if district_name       else None
        crime_head_id     = _resolve_crime_head_id(db, crime_head_name)         if crime_head_name     else None
        police_station_id = _resolve_police_station_id(db, police_station_name) if police_station_name else None

        print(f"  district_name       = {district_name!r:30s}  -> district_id       = {district_id}")
        print(f"  crime_head_name     = {crime_head_name!r:30s}  -> crime_head_id     = {crime_head_id}")
        print(f"  police_station_name = {police_station_name!r:30s}  -> police_station_id = {police_station_id}")

        # ---- Compile and print SQL ----
        from sqlalchemy import extract, func, select
        from app.models.case import CaseMaster
        from app.models.masters import Unit

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

        try:
            from sqlalchemy.dialects import postgresql
            compiled_sql = stmt.compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": True}
            )
            print(f"\n  Generated SQL:\n{compiled_sql}\n")
        except Exception as e:
            print(f"  (Could not render literal SQL: {e})")

        # ---- Execute and fetch counts ----
        rows = db.execute(stmt).all()
        counts = [(int(r.yr), int(r.mo), int(r.cnt)) for r in rows]

        print(f"  Rows returned from DB: {len(counts)}")
        if counts:
            print(f"  Monthly counts (year, month, count):")
            for yr, mo, cnt in counts:
                print(f"    {yr}-{mo:02d} : {cnt}")
        else:
            print("  No data rows returned — fallback will be applied.")

        # ---- Run full prediction ----
        result = predict_crime(db, {"intent": "PREDICT_CRIME", "entities": entities})
        print(f"\n  Prediction result:")
        for k, v in result.items():
            if k != "historical_counts":
                print(f"    {k}: {v}")

finally:
    db.close()
