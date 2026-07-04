from typing import Dict, Any

from sqlalchemy import select, func

from app.models.case import CaseMaster, Accused, Victim


def generate_select(parsed_query: Dict[str, Any]):
    """Generate a SQLAlchemy ``Select`` object based on the parsed query.

    The *parsed_query* is the dictionary returned by ``parse_query`` and is
    expected to contain an ``intent`` key with one of the supported intent
    strings and an ``entities`` mapping.
    """
    intent = parsed_query.get("intent")

    if intent == "SEARCH_CASES":
        # Return all columns of the CaseMaster table (limit can be applied later)
        return select(CaseMaster)
    elif intent == "SEARCH_ACCUSED":
        return select(Accused)
    elif intent == "SEARCH_VICTIMS":
        return select(Victim)
    elif intent == "CRIME_TREND":
        # Group by major crime head and count occurrences
        return (
            select(CaseMaster.crime_major_head_id, func.count().label("count"))
            .group_by(CaseMaster.crime_major_head_id)
            .order_by(func.count().desc())
            .limit(5)
        )
    elif intent == "HOTSPOT":
        # Aggregate by latitude/longitude to find hotspot areas
        return (
            select(CaseMaster.latitude, CaseMaster.longitude, func.count().label("count"))
            .where(CaseMaster.latitude != None)
            .group_by(CaseMaster.latitude, CaseMaster.longitude)
            .order_by(func.count().desc())
            .limit(10)
        )
    elif intent == "REPORTS":
        # Simple example: total number of cases
        return select(func.count(CaseMaster.case_master_id).label("total_cases"))
    else:
        # Fallback: empty select (no rows)
        return select()
