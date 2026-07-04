from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db

router = APIRouter()


@router.get("", response_model=List[Dict[str, Any]])
def read_cases(db: Session = Depends(get_db)):
    """
    Get all active First Information Reports (FIRs) from the archive.
    [STUB - Database logic pending]
    """
    return [
        {
            "id": "fir-1",
            "case_number": "FIR 402/2026",
            "title": "Syndicated Cyber Extortion & Ransomware Attack",
            "under_section": "BNS Sec 308 (Extortion) & IT Act Sec 66D",
            "status": "Investigation",
            "date_registered": "2026-06-28",
            "severity": "Critical"
        }
    ]


@router.get("/{case_id}", response_model=Dict[str, Any])
def read_case(case_id: str, db: Session = Depends(get_db)):
    """
    Retrieve full dossier for a specific FIR by case identifier.
    [STUB - Database logic pending]
    """
    return {
        "id": case_id,
        "case_number": "FIR 402/2026",
        "title": "Syndicated Cyber Extortion & Ransomware Attack",
        "status": "Investigation",
        "details": "Ransomware deployment on hospital servers resulting in operational shutdown."
    }


@router.post("", status_code=201)
def create_case(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Log and register a new FIR.
    [STUB - Database logic pending]
    """
    return {"status": "registered", "case_number": payload.get("case_number", "PENDING")}
