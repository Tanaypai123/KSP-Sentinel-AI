"""
QA Fixtures — Shared mock DB, seeded FIR records, and ExecutionContext builder
for Phase 7.0 Manual QA.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

# ── Seeded FIR Records ────────────────────────────────────────────────────────

SEED_FIR_RECORDS = [
    {
        "fir_number": "FIR-2023-001",
        "case_number": "CASE-001",
        "accused_name": "Ravi Kumar",
        "victim_name": "Sita Devi",
        "crime_head": "Theft",
        "district": "Bengaluru Urban",
        "station_name": "MG Road",
        "date_of_occurrence": "2023-01-15",
        "date_of_registration": "2023-01-16",
        "weapon_type": "Knife",
        "vehicle_number": "KA-01-AB-1234",
        "status": "Under Investigation",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "year": 2023,
        "month": 1,
    },
    {
        "fir_number": "FIR-2023-002",
        "case_number": "CASE-002",
        "accused_name": "Mohan Das",
        "victim_name": "Priya Sharma",
        "crime_head": "Robbery",
        "district": "Mysuru",
        "station_name": "Saraswathipuram",
        "date_of_occurrence": "2023-02-10",
        "date_of_registration": "2023-02-11",
        "weapon_type": None,
        "vehicle_number": "KA-09-CD-5678",
        "status": "Charge Sheet Filed",
        "latitude": 12.2958,
        "longitude": 76.6394,
        "year": 2023,
        "month": 2,
    },
    {
        "fir_number": "FIR-2023-003",
        "case_number": "CASE-003",
        "accused_name": "Ravi Kumar",
        "victim_name": "Rajesh Nair",
        "crime_head": "Assault",
        "district": "Bengaluru Urban",
        "station_name": "Indiranagar",
        "date_of_occurrence": "2023-03-05",
        "date_of_registration": "2023-03-06",
        "weapon_type": "Iron Rod",
        "vehicle_number": None,
        "status": "Arrested",
        "latitude": 12.9784,
        "longitude": 77.6408,
        "year": 2023,
        "month": 3,
    },
    {
        "fir_number": "FIR-2023-004",
        "case_number": "CASE-004",
        "accused_name": "Suresh Babu",
        "victim_name": "Lakshmi Bai",
        "crime_head": "Murder",
        "district": "Shivamogga",
        "station_name": "Shimoga Town",
        "date_of_occurrence": "2023-04-20",
        "date_of_registration": "2023-04-21",
        "weapon_type": "Firearm",
        "vehicle_number": "KA-14-EF-9012",
        "status": "Under Investigation",
        "latitude": 13.9299,
        "longitude": 75.5681,
        "year": 2023,
        "month": 4,
    },
    {
        "fir_number": "FIR-2023-005",
        "case_number": "CASE-005",
        "accused_name": "Anita Singh",
        "victim_name": "Geeta Reddy",
        "crime_head": "Kidnapping",
        "district": "Kalaburagi",
        "station_name": "Kalaburagi Town",
        "date_of_occurrence": "2023-05-12",
        "date_of_registration": "2023-05-13",
        "weapon_type": None,
        "vehicle_number": "KA-32-GH-3456",
        "status": "Charge Sheet Filed",
        "latitude": 17.3297,
        "longitude": 76.8343,
        "year": 2023,
        "month": 5,
    },
]

EMPTY_FIR_RECORDS: List[Dict[str, Any]] = []

LARGE_FIR_RECORDS = [
    {
        "fir_number": f"FIR-2023-{100 + i:03d}",
        "case_number": f"CASE-{100 + i:03d}",
        "accused_name": f"Accused {i}",
        "victim_name": f"Victim {i}",
        "crime_head": ["Theft", "Robbery", "Assault", "Murder", "Kidnapping"][i % 5],
        "district": ["Bengaluru Urban", "Mysuru", "Mangaluru", "Shivamogga", "Kalaburagi"][i % 5],
        "station_name": f"Station {i}",
        "date_of_occurrence": f"2023-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}",
        "date_of_registration": f"2023-{(i % 12) + 1:02d}-{(i % 28) + 2:02d}",
        "weapon_type": ["Knife", "Firearm", None, "Iron Rod", None][i % 5],
        "vehicle_number": f"KA-{(i % 30) + 1:02d}-XX-{1000 + i}",
        "status": ["Under Investigation", "Arrested", "Charge Sheet Filed"][i % 3],
        "latitude": 12.5 + (i * 0.01),
        "longitude": 76.5 + (i * 0.01),
        "year": 2023,
        "month": (i % 12) + 1,
    }
    for i in range(50)
]


# ── Mock DB Builder ───────────────────────────────────────────────────────────

def make_mock_db(records: Optional[List[Dict]] = None) -> MagicMock:
    """Create a mock SQLAlchemy Session that returns seeded records."""
    if records is None:
        records = SEED_FIR_RECORDS
    db = MagicMock()

    mock_result = MagicMock()
    mock_result.mappings.return_value.all.return_value = [dict(r) for r in records]
    db.execute.return_value = mock_result
    return db


# ── ExecutionContext Builder ──────────────────────────────────────────────────

def make_context(
    raw_query: str = "Show FIRs in Bengaluru",
    intent: Optional[str] = "SEARCH",
    resolved_entities: Optional[Dict] = None,
    search_results: Optional[List] = None,
    conversation_id: str = "qa-test",
    records: Optional[List] = None,
) -> Any:
    """Build a minimal ExecutionContext for unit-level QA testing."""
    import sys
    sys.path.insert(0, "/Users/tanaysharma/Desktop/KSP-Sentinel-AI/dataset")
    from app.ai.pipeline_runner import ExecutionContext

    db = make_mock_db(records if records is not None else SEED_FIR_RECORDS)
    ctx = ExecutionContext(raw_query=raw_query, db=db, conversation_id=conversation_id)
    ctx.intent = intent
    ctx.resolved_entities = resolved_entities or {
        "district": "Bengaluru Urban",
        "crime_head": "Theft",
        "accused_name": None,
        "year": 2023,
    }
    ctx.search_result = search_results if search_results is not None else list(SEED_FIR_RECORDS)
    return ctx
