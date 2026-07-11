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


@router.post("/{report_id}/export")
def export_report(
    report_id: str,
    payload: Dict[str, Any] = None,
    db: Session = Depends(get_db),
):
    """
    Export PDF endpoint.
    """
    import os
    import logging
    from app.services.pdf_generator import generate_pdf_report
    
    logger = logging.getLogger(__name__)
    logger.info(f"Export request received for report_id: {report_id}")
    if payload:
        logger.info(f"Received payload with keys: {list(payload.keys())}")
    logger.info("PDF generation started")

    import os
    from app.services.pdf_generator import generate_pdf_report
    
    # Save the PDF in dataset/app/temp_reports
    pdf_dir = os.path.join(os.path.dirname(__file__), "..", "..", "temp_reports")
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_path = os.path.join(pdf_dir, f"{report_id}.pdf")
    abs_pdf_path = os.path.abspath(pdf_path)
    
    generate_pdf_report(report_id, pdf_path, payload)
    
    import os
    file_exists = os.path.exists(abs_pdf_path)
    file_size = os.path.getsize(abs_pdf_path) if file_exists else 0
    dir_listing = os.listdir(os.path.abspath(pdf_dir))
    
    logger.info(f"Absolute output path: {abs_pdf_path}")
    logger.info(f"Filename: {report_id}.pdf")
    logger.info(f"os.path.exists(path): {file_exists}")
    logger.info(f"os.path.getsize(path): {file_size}")
    logger.info(f"Directory listing of temp_reports: {dir_listing}")

    return {
        "report_id": report_id,
        "exported": True,
        "format": "PDF",
        "download_url": f"/downloads/reports/{report_id}.pdf",
    }