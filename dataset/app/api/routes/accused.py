from typing import Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.case import Accused

router = APIRouter()


@router.get("", response_model=List[Dict[str, Any]])
def read_accused_list(db: Session = Depends(get_db)):
    """
    Get all accused records.
    """

    accused_list = db.query(Accused).all()

    return [
        {
            "id": accused.accused_master_id,
            "case_master_id": accused.case_master_id,
            "name": accused.accused_name,
            "age": accused.age_year,
            "gender_id": accused.gender_id,
            "person_id": accused.person_id,
        }
        for accused in accused_list
    ]


@router.get("/{accused_id}", response_model=Dict[str, Any])
def read_accused(accused_id: int, db: Session = Depends(get_db)):
    """
    Get a single accused record.
    """

    accused = (
        db.query(Accused)
        .filter(Accused.accused_master_id == accused_id)
        .first()
    )

    if accused is None:
        raise HTTPException(
            status_code=404,
            detail="Accused not found"
        )

    return {
        "id": accused.accused_master_id,
        "case_master_id": accused.case_master_id,
        "name": accused.accused_name,
        "age": accused.age_year,
        "gender_id": accused.gender_id,
        "person_id": accused.person_id,
    }


@router.put("/{accused_id}", response_model=Dict[str, Any])
def update_accused(
    accused_id: int,
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
):
    """
    Update an accused record.
    """

    accused = (
        db.query(Accused)
        .filter(Accused.accused_master_id == accused_id)
        .first()
    )

    if accused is None:
        raise HTTPException(
            status_code=404,
            detail="Accused not found"
        )

    allowed_fields = [
        "accused_name",
        "age_year",
        "gender_id",
        "person_id",
    ]

    for field in allowed_fields:
        if field in payload:
            setattr(accused, field, payload[field])

    db.commit()
    db.refresh(accused)

    return {
        "message": "Accused updated successfully",
        "id": accused.accused_master_id,
    }