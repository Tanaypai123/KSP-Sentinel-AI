"""Global Analytics Service.

Provides dialect-agnostic aggregate statistical queries for dashboard displays.
"""

from __future__ import annotations

from typing import Any, Dict, List
from sqlalchemy import func, select, extract
from sqlalchemy.orm import Session

from app.models.case import CaseMaster, Victim
from app.models.crime import CrimeHead, CaseStatusMaster
from app.models.masters import District, Unit


class AnalyticsService:
    """Database aggregation layer returning crime distributions without SQL duplication."""

    @staticmethod
    def get_top_crimes(db: Session, limit: int = 5) -> List[Dict[str, Any]]:
        """Return top crimes sorted by case occurrences."""
        stmt = (
            select(
                CrimeHead.crime_group_name.label("crime_group"),
                func.count(CaseMaster.case_master_id).label("count")
            )
            .join(CrimeHead, CaseMaster.crime_major_head_id == CrimeHead.crime_head_id)
            .group_by(CrimeHead.crime_group_name)
            .order_by(func.count(CaseMaster.case_master_id).desc())
            .limit(limit)
        )
        rows = db.execute(stmt).all()
        return [{"crime_group": r[0], "count": r[1]} for r in rows]

    @staticmethod
    def get_top_districts(db: Session, limit: int = 5) -> List[Dict[str, Any]]:
        """Return top Karnataka districts by case occurrences."""
        stmt = (
            select(
                District.district_name.label("district"),
                func.count(CaseMaster.case_master_id).label("count")
            )
            .join(Unit, CaseMaster.police_station_id == Unit.unit_id)
            .join(District, Unit.district_id == District.district_id)
            .group_by(District.district_name)
            .order_by(func.count(CaseMaster.case_master_id).desc())
            .limit(limit)
        )
        rows = db.execute(stmt).all()
        return [{"district": r[0], "count": r[1]} for r in rows]

    @staticmethod
    def get_top_stations(db: Session, limit: int = 5) -> List[Dict[str, Any]]:
        """Return top police stations by case occurrences."""
        stmt = (
            select(
                Unit.unit_name.label("station"),
                func.count(CaseMaster.case_master_id).label("count")
            )
            .join(Unit, CaseMaster.police_station_id == Unit.unit_id)
            .group_by(Unit.unit_name)
            .order_by(func.count(CaseMaster.case_master_id).desc())
            .limit(limit)
        )
        rows = db.execute(stmt).all()
        return [{"station": r[0], "count": r[1]} for r in rows]

    @staticmethod
    def get_monthly_counts(db: Session) -> List[Dict[str, Any]]:
        """Return chronological monthly counts of cases."""
        yr_col = extract("year", CaseMaster.crime_registered_date)
        mo_col = extract("month", CaseMaster.crime_registered_date)
        
        stmt = (
            select(
                yr_col.label("yr"),
                mo_col.label("mo"),
                func.count(CaseMaster.case_master_id).label("cnt")
            )
            .where(CaseMaster.crime_registered_date.isnot(None))
            .group_by(yr_col, mo_col)
            .order_by(yr_col, mo_col)
        )
        rows = db.execute(stmt).all()
        return [{"month": f"{int(r[0])}-{int(r[1]):02d}", "count": int(r[2])} for r in rows]

    @staticmethod
    def get_status_distribution(db: Session) -> List[Dict[str, Any]]:
        """Return case distribution grouped by status name."""
        stmt = (
            select(
                CaseStatusMaster.case_status_name.label("status"),
                func.count(CaseMaster.case_master_id).label("count")
            )
            .join(CaseStatusMaster, CaseMaster.case_status_id == CaseStatusMaster.case_status_id)
            .group_by(CaseStatusMaster.case_status_name)
            .order_by(func.count(CaseMaster.case_master_id).desc())
        )
        rows = db.execute(stmt).all()
        return [{"status": r[0], "count": r[1]} for r in rows]

    @staticmethod
    def get_gender_distribution(db: Session) -> List[Dict[str, Any]]:
        """Return case victim distribution by gender."""
        stmt = (
            select(
                Victim.gender_id,
                func.count(Victim.victim_master_id).label("count")
            )
            .group_by(Victim.gender_id)
        )
        rows = db.execute(stmt).all()
        gender_names = {1: "Male", 2: "Female"}
        return [{"gender": gender_names.get(r[0], "Other/Unknown"), "count": r[1]} for r in rows]

    @staticmethod
    def get_age_distribution(db: Session) -> List[Dict[str, Any]]:
        """Return case victim age group distribution."""
        stmt = select(Victim.age_year).where(Victim.age_year.isnot(None))
        ages = db.scalars(stmt).all()

        brackets = {"Under 18": 0, "18-30": 0, "30-50": 0, "Above 50": 0}
        for age in ages:
            if age < 18:
                brackets["Under 18"] += 1
            elif age <= 30:
                brackets["18-30"] += 1
            elif age <= 50:
                brackets["30-50"] += 1
            else:
                brackets["Above 50"] += 1

        return [{"bracket": k, "count": v} for k, v in brackets.items()]

    @staticmethod
    def get_unit_map(db: Session) -> Dict[int, str]:
        """Fetch lookup dict mapping unit_id to unit_name."""
        stmt = select(Unit.unit_id, Unit.unit_name)
        rows = db.execute(stmt).all()
        return {r[0]: r[1] for r in rows if r[0]}
