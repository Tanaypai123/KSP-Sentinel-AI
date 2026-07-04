from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db

router = APIRouter()


@router.get("", response_model=List[Dict[str, Any]])
def read_accused_list(db: Session = Depends(get_db)):
    """
    Get all accused profiles from biometrics tracking.
    [STUB - Database logic pending]
    """
    return [
        {
            "id": "acc-1",
            "name": "Rajesh \"Gowda\" Gowda",
            "age": 34,
            "status": "At Large",
            "risk_score": 92,
            "biometrics_match": 87.5
        }
    ]


@router.get("/{accused_id}", response_model=Dict[str, Any])
def read_accused(accused_id: str, db: Session = Depends(get_db)):
    """
    Get detailed biometric dossier for a specific suspect.
    [STUB - Database logic pending]
    """
    return {
        "id": accused_id,
        "name": "Rajesh \"Gowda\" Gowda",
        "age": 34,
        "status": "At Large",
        "notes": "Operates dark web syndicate 'Gowda_Net'."
    }


@router.put("/{accused_id}", response_model=Dict[str, Any])
def update_accused(accused_id: str, payload: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Update details/biometrics for a suspect.
    [STUB - Database logic pending]
    """
    return {"id": accused_id, "status": "updated", "data": payload}
