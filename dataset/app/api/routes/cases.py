from typing import Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.case import CaseMaster

router = APIRouter()


@router.get("", response_model=List[Dict[str, Any]])
def read_cases(db: Session = Depends(get_db)):
    """
    Return all FIR cases.
    """

    cases = (
        db.query(CaseMaster)
        .order_by(CaseMaster.case_master_id.desc())
        .all()
    )

    return [
        {
            "id": case.case_master_id,
            "crime_no": case.crime_no,
            "case_no": case.case_no,
            "crime_registered_date": case.crime_registered_date,
            "status_id": case.case_status_id,
            "gravity_id": case.gravity_offence_id,
            "brief_facts": case.brief_facts,
            "latitude": case.latitude,
            "longitude": case.longitude,
        }
        for case in cases
    ]


@router.get("/{case_id}", response_model=Dict[str, Any])
def read_case(case_id: int, db: Session = Depends(get_db)):
    """
    Return a single FIR.
    """

    case = (
        db.query(CaseMaster)
        .filter(CaseMaster.case_master_id == case_id)
        .first()
    )

    if case is None:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )

    return {
        "id": case.case_master_id,
        "crime_no": case.crime_no,
        "case_no": case.case_no,
        "crime_registered_date": case.crime_registered_date,
        "status_id": case.case_status_id,
        "gravity_id": case.gravity_offence_id,
        "brief_facts": case.brief_facts,
        "latitude": case.latitude,
        "longitude": case.longitude,
    }


@router.post("", status_code=201)
def create_case(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Create a new FIR.
    """

    new_case = CaseMaster()

    if "crime_no" in payload:
        new_case.crime_no = payload["crime_no"]

    if "case_no" in payload:
        new_case.case_no = payload["case_no"]

    if "brief_facts" in payload:
        new_case.brief_facts = payload["brief_facts"]

    db.add(new_case)
    db.commit()
    db.refresh(new_case)

    return {
        "message": "Case created successfully",
        "id": new_case.case_master_id,
    }