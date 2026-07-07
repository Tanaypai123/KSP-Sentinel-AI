"""Production‑ready query parser for the KSP Sentinel AI.

Routes through `app.ai.entity_extractor` to execute structured NLP entity
extraction, and maps entities back to legacy keys for database/SQL backward compatibility.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional
from app.ai.entity_extractor import EntityExtractor


def parse_query(query: str, db_session: Optional[Any] = None) -> Dict[str, Any]:
    """Extract entities from *query* using the structured EntityExtractor.

    Maps values into both structured custom keys and backward-compatible legacy keys.
    """
    # Run structured extraction
    ext = EntityExtractor.extract_all(query, db_session)

    # -------------------------------------------------------------------------
    # Backward compatibility mapping for SQL generator and formatter
    # -------------------------------------------------------------------------
    entities: Dict[str, Any] = {}

    # Simple mappings
    # FIR / Identifier mapping
    entities["fir_number"] = None
    if ext.get("identifiers"):
        entities["identifiers"] = ext["identifiers"]

    entities["crime_head"] = ext["crime_type"]
    entities["district"] = ext["district"]
    entities["police_station"] = ext["police_station"]
    entities["accused_name"] = ext["accused_name"]
    entities["victim_name"] = ext["victim_name"]
    entities["complainant_name"] = None # complainant is not typically parsed from base name

    # Section / Act extraction fallback
    sec_match = re.search(r"section\s*[:\-]?\s*(\w+)", query, re.IGNORECASE)
    entities["section"] = sec_match.group(1) if sec_match else None
    
    act_match = re.search(r"act\s*[:\-]?\s*([a-z]+)", query, re.IGNORECASE)
    entities["act"] = act_match.group(1) if act_match else None

    # Gender mapping: ID values for database compatibility (1=Male, 2=Female)
    gender_map = {"male": 1, "female": 2}
    entities["gender"] = gender_map.get(ext["gender"]) if ext["gender"] else None

    # Generic numeric mapping
    entities["numeric_filters"] = ext.get("numeric_filters", [])

    # Mapping status names to DB ID values (1=Investigation, 2=Under Trial, 3=Closed, 4=Under Review)
    status_map = {
        "investigation": 1,
        "pending": 1,
        "under trial": 2,
        "closed": 3,
        "disposed": 3,
        "charge sheet": 4,
        "under review": 4
    }
    entities["status"] = status_map.get(ext["status"]) if ext["status"] else None

    # Limit / Offset
    entities["limit"] = ext["limit"]
    entities["offset"] = None
    off_match = re.search(r"\b(?:skip|offset)\s+(\d+)\b", query, re.IGNORECASE)
    if off_match:
        entities["offset"] = int(off_match.group(1))

    # Sort rules
    entities["sort_order"] = ext["sort"]
    
    sort_by = None
    if re.search(r"\b(cases?|firs?)\b", query, re.IGNORECASE):
        sort_by = "cases"
    elif re.search(r"\baccused\b", query, re.IGNORECASE):
        sort_by = "accused"
    elif re.search(r"\bvictims?\b", query, re.IGNORECASE):
        sort_by = "victims"
    entities["sort_by"] = sort_by

    # Year fallback from date filters
    entities["year"] = None
    if ext["date_from"]:
        try:
            entities["year"] = int(ext["date_from"][:4])
        except ValueError:
            pass

    # Date range SQL generator format YYYY-MM-DD,YYYY-MM-DD
    entities["date_range"] = None
    if ext["date_from"] or ext["date_to"]:
        d_from = ext["date_from"] or "1970-01-01"
        d_to = ext["date_to"] or "2099-12-31"
        entities["date_range"] = f"{d_from},{d_to}"

    # Coordinates fallback
    lat_match = re.search(r"latitude\s*[:\-]?\s*([-+]?\d*\.?\d+)", query, re.IGNORECASE)
    entities["latitude"] = lat_match.group(1) if lat_match else None
    
    lon_match = re.search(r"longitude\s*[:\-]?\s*([-+]?\d*\.?\d+)", query, re.IGNORECASE)
    entities["longitude"] = lon_match.group(1) if lon_match else None

    # Include raw structured fields in output too (accessible by other modules)
    entities.update({
        "structured_crime_type": ext["crime_type"],
        "structured_date_from": ext["date_from"],
        "structured_date_to": ext["date_to"],
        "structured_comparison": ext["comparison"],
        "structured_prediction": ext["prediction"],
        "structured_raw_district": ext["raw_district"],
        "structured_is_valid_district": ext["is_valid_district"],
        "structured_district_suggestions": ext["district_suggestions"]
    })

    return {"intent": None, "entities": entities}
