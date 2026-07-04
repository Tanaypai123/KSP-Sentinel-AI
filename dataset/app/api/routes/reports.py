from typing import Dict, Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.connection import get_db
from app.models.case import CaseMaster, Accused, Victim

router = APIRouter()


@router.post("/generate", response_model=Dict[str, Any])
def generate_intelligence_report(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
):
    """
    Generate dashboard intelligence statistics.
    """

    total_cases = db.query(func.count(CaseMaster.case_master_id)).scalar() or 0
    total_accused = db.query(func.count(Accused.accused_master_id)).scalar() or 0
    total_victims = db.query(func.count(Victim.victim_master_id)).scalar() or 0

    recent_cases = (
        db.query(CaseMaster)
        .order_by(CaseMaster.case_master_id.desc())
        .limit(5)
        .all()
    )

    return {
        "status": "generated",
        "title": payload.get("title", "KSP Sentinel Intelligence Report"),
        "summary": {
            "total_cases": total_cases,
            "total_accused": total_accused,
            "total_victims": total_victims,
        },
        "recent_cases": [
            {
                "id": case.case_master_id,
                "crime_no": case.crime_no,
                "case_no": case.case_no,
                "registered_date": case.crime_registered_date,
            }
            for case in recent_cases
        ],
    }


@router.get("/{report_id}/export")
def export_report(
    report_id: str,
    db: Session = Depends(get_db),
):
    """
    Placeholder export endpoint.
    Actual PDF generation can be added later.
    """

    return {
        "report_id": report_id,
        "exported": True,
        "format": "PDF",
        "download_url": f"/downloads/reports/{report_id}.pdf",
    }