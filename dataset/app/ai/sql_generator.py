"""Production‑ready dynamic SQLAlchemy query generator.

The generator builds SELECT statements using **only** the columns and
relationships that actually exist in the project's ORM models (see
``app/ai/compatibility_report.md`` for the verified list).

It accepts the parsed output from ``app.ai.query_parser`` – a dictionary with
``intent`` and ``entities`` – and creates an appropriate ORM query, adding
``WHERE`` clauses for any non‑null entity values and joining related tables when
necessary.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List

from sqlalchemy import and_, func, or_, select

# Import the verified ORM models.
from app.models.case import (
    Accused,
    CaseMaster,
    ComplainantDetails,
    Victim,
    ActSectionAssociation,
)
from app.models.crime import CrimeHead, CrimeSubHead
from app.models.masters import District, Unit

# ---------------------------------------------------------------------------
# Helper filter functions – each receives a ``Select`` statement and the entity
# value, returning the (potentially) modified statement.  They use only the
# attributes/relationships listed in the compatibility report.
# ---------------------------------------------------------------------------
# Helper filter functions – each receives a ``Select`` statement and the entity
# value, returning the (potentially) modified statement. They use only the
# attributes/relationships listed in the compatibility report.
# ---------------------------------------------------------------------------

def _filter_fir_number(stmt, value):
    """Filter by FIR number (crime_no)."""
    if not value:
        return stmt
    return stmt.where(CaseMaster.crime_no.ilike(f"%{value}%"))

def _filter_crime_head(stmt, value):
    """Filter by major crime head name."""
    if not value:
        return stmt
    return stmt.where(CaseMaster.crime_major_head.has(CrimeHead.crime_group_name.ilike(f"%{value}%")))

def _filter_crime_sub_head(stmt, value):
    """Filter by sub‑head name."""
    if not value:
        return stmt
    return stmt.where(CaseMaster.crime_minor_head.has(CrimeSubHead.crime_head_name.ilike(f"%{value}%")))

def _filter_district(stmt, value):
    """Filter by district name via police station relationship."""
    if not value:
        return stmt
    return stmt.where(
        CaseMaster.police_station.has(
            Unit.district.has(District.district_name.ilike(f"%{value}%"))
        )
    )

def _filter_police_station(stmt, value):
    """Filter by police station (unit) name."""
    if not value:
        return stmt
    return stmt.where(CaseMaster.police_station.has(Unit.unit_name.ilike(f"%{value}%")))

def _filter_accused_name(stmt, value):
    """Filter accused by name."""
    if not value:
        return stmt
    return stmt.where(Accused.accused_name.ilike(f"%{value}%"))

def _filter_victim_name(stmt, value):
    """Filter victim by name."""
    if not value:
        return stmt
    return stmt.where(Victim.victim_name.ilike(f"%{value}%"))

def _filter_complainant_name(stmt, value):
    """Filter complainant by name."""
    if not value:
        return stmt
    return stmt.where(ComplainantDetails.complainant_name.ilike(f"%{value}%"))

def _filter_section(stmt, value):
    """Filter by legal section name."""
    if not value:
        return stmt
    return stmt.where(ActSectionAssociation.section_code.ilike(f"%{value}%"))

def _filter_act(stmt, value):
    """Filter by act name."""
    if not value:
        return stmt
    return stmt.where(ActSectionAssociation.act_code.ilike(f"%{value}%"))

def _filter_date_range(stmt, value):
    """Filter by a start,end date range string "YYYY-MM-DD,YYYY-MM-DD"."""
    if not value:
        return stmt
    try:
        start, end = [d.strip() for d in value.split(',')]
        return stmt.where(CaseMaster.crime_registered_date.between(start, end))
    except Exception:
        return stmt

def _filter_year(stmt, value):
    """Filter by registration year."""
    if not value:
        return stmt
    try:
        yr = int(value)
    except Exception:
        return stmt
    return stmt.where(func.extract('year', CaseMaster.crime_registered_date) == yr)

def _filter_gender(stmt, value):
    """Filter by gender ID (applies to victims)."""
    if not value:
        return stmt
    try:
        gid = int(value)
    except Exception:
        return stmt
    return stmt.where(Victim.gender_id == gid)

def _filter_age(stmt, value):
    """Filter by victim age."""
    if not value:
        return stmt

    if isinstance(value, dict):
        if "lt" in value:
            return stmt.where(Victim.age_year < int(value["lt"]))
        if "gt" in value:
            return stmt.where(Victim.age_year > int(value["gt"]))
        if "eq" in value:
            return stmt.where(Victim.age_year == int(value["eq"]))
        return stmt

    return stmt.where(Victim.age_year == int(value))

def _filter_status(stmt, value):
    """Filter by case status ID."""
    if not value:
        return stmt
    try:
        sid = int(value)
    except Exception:
        return stmt
    return stmt.where(CaseMaster.case_status_id == sid)

def _filter_latitude(stmt, value):
    """Filter by latitude coordinate."""
    if not value:
        return stmt
    try:
        lat = float(value)
    except Exception:
        return stmt
    return stmt.where(CaseMaster.latitude == lat)

def _filter_longitude(stmt, value):
    """Filter by longitude coordinate."""
    if not value:
        return stmt
    try:
        lon = float(value)
    except Exception:
        return stmt
    return stmt.where(CaseMaster.longitude == lon)




# Mapping of entity keys to their filter helpers.
ENTITY_FILTERS: Dict[str, Callable[[Any, Any], Any]] = {
    "fir_number": _filter_fir_number,
    "crime_head": _filter_crime_head,
    "crime_sub_head": _filter_crime_sub_head,
    "district": _filter_district,
    "police_station": _filter_police_station,
    "accused_name": _filter_accused_name,
    "victim_name": _filter_victim_name,
    "complainant_name": _filter_complainant_name,
    "section": _filter_section,
    "act": _filter_act,
    "date_range": _filter_date_range,
    "year": _filter_year,
    "gender": _filter_gender,
    "age": _filter_age,
    "status": _filter_status,
    "latitude": _filter_latitude,
    "longitude": _filter_longitude,
}


def _apply_entity_filters(base_stmt, entities: Dict[str, Any]):
    """Apply each non‑null entity filter to the statement.

    ``base_stmt`` is the initial ``Select`` (usually ``select(CaseMaster)``).
    The function iterates over ``entities`` and, when a matching helper exists,
    calls it to augment the query.
    """
    stmt = base_stmt
    for entity, value in entities.items():
        filter_fn = ENTITY_FILTERS.get(entity)
        if filter_fn:
            stmt = filter_fn(stmt, value)
    return stmt


def generate_select(parsed_query: Dict[str, Any]):
    """Generate a SQLAlchemy ``Select`` based on the parsed query.

    The function respects the ``intent`` and then applies dynamic filters for
    any entities that were extracted.  All joins and column references are
    derived from the verified ORM model definitions.
    """
    intent = parsed_query.get("intent")
    entities = parsed_query.get("entities", {})

    # -------------------------------------------------------------------
    # Intent‑specific base statements
    # -------------------------------------------------------------------
    if intent == "SEARCH_CASES":
        stmt = select(CaseMaster)
        return _apply_entity_filters(stmt, entities)

    if intent == "SEARCH_ACCUSED":
        stmt = select(Accused)
        # Apply accused‑specific filter directly.
        if entities.get("accused_name"):
            stmt = stmt.where(Accused.accused_name.ilike(entities["accused_name"]))
        # For any case‑level filters, join back to CaseMaster.
        case_entities = {k: v for k, v in entities.items() if k not in {"accused_name", "victim_name", "complainant_name"}}
        if any(case_entities.values()):
            stmt = stmt.join(Accused.case_master)
            stmt = _apply_entity_filters(stmt, case_entities)
        return stmt

    if intent == "SEARCH_VICTIMS":
        stmt = select(Victim)
        # Victim‑specific filters
        if entities.get("victim_name"):
            stmt = stmt.where(Victim.victim_name.ilike(f"%{entities['victim_name']}%"))
        if entities.get("gender"):
            stmt = stmt.where(Victim.gender_id == entities["gender"])
        if entities.get("age"):
            stmt = _filter_age(stmt, entities["age"])
        # Case‑level filters (exclude victim‑specific keys)
        case_entities = {k: v for k, v in entities.items() if k not in {"victim_name", "gender", "age", "accused_name", "complainant_name"}}
        if any(case_entities.values()):
            stmt = stmt.join(Victim.case_master)
            stmt = _apply_entity_filters(stmt, case_entities)
        return stmt

    if intent == "CRIME_TREND":
        stmt = (
            select(CaseMaster.crime_major_head_id, func.count().label("count"))
            .group_by(CaseMaster.crime_major_head_id)
        )
        stmt = _apply_entity_filters(stmt, entities)
        return stmt.order_by(func.count().desc()).limit(5)

    if intent == "HOTSPOT":
        stmt = (
            select(CaseMaster.latitude, CaseMaster.longitude, func.count().label("count"))
            .where(CaseMaster.latitude != None)
            .group_by(CaseMaster.latitude, CaseMaster.longitude)
        )
        stmt = _apply_entity_filters(stmt, entities)
        return stmt.order_by(func.count().desc()).limit(10)

    if intent == "REPORTS":
        stmt = select(
            func.count(CaseMaster.case_master_id).label("total_cases"),
            func.count(Accused.accused_master_id).label("total_accused"),
            func.count(Victim.victim_master_id).label("total_victims"),
        )
        return stmt

    # Fallback – empty select.
    return select()
