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

from typing import Any, Callable, Dict, List, Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import joinedload, selectinload

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

def _resolve_sort_column(intent: str, sort_by: str):
    """Map a ``sort_by`` string to an ORM column based on intent.

    Extend this mapping when new sortable fields are added.
    """
    mapping = {
        "cases": CaseMaster.crime_registered_date,
        "case": CaseMaster.crime_registered_date,
        "firs": CaseMaster.crime_no,
        "fir": CaseMaster.crime_no,
        "accused": Accused.accused_name,
        "victims": Victim.victim_name,
        "victim": Victim.victim_name,
    }
    return mapping.get(sort_by.lower())

def _normalize_sort_order(order: Optional[str]) -> str:
    """Return ``asc`` or ``desc`` based on user input.

    Accepts synonyms ``oldest`` (asc) and ``newest``/``latest`` (desc).
    """
    if not order:
        return "desc"
    order = order.lower()
    if order in {"asc", "oldest"}:
        return "asc"
    return "desc"

def _apply_sort_and_pagination(stmt, entities: Dict[str, Any], intent: str):
    """Apply ORDER BY, LIMIT and OFFSET based on extracted entities.

    * ``sort_by`` – optional column name to sort on.
    * ``sort_order`` – ``asc`` or ``desc`` (default ``desc``).
    * ``limit`` – maximum number of rows.
    * ``offset`` – number of rows to skip.

    For intents that provide their own ordering (HOTSPOT, CRIME_TREND, REPORTS),
    generic sorting is omitted.
    """
    sort_by = entities.get("sort_by")
    sort_order = _normalize_sort_order(entities.get("sort_order"))
    # Intents with custom ordering that should skip generic sort logic
    skip_generic_intents = {"HOTSPOT", "CRIME_TREND", "REPORTS"}
    if intent not in skip_generic_intents:
        if sort_by:
            column = _resolve_sort_column(intent, sort_by)
            if column is not None:
                stmt = stmt.order_by(column.asc() if sort_order == "asc" else column.desc())
        else:
            if intent in {"SEARCH_CASES", "SEARCH_ACCUSED", "SEARCH_VICTIMS"}:
                stmt = stmt.order_by(CaseMaster.crime_registered_date.desc())
    # Pagination handling
    limit = entities.get("limit")
    offset = entities.get("offset")
    if limit:
        try:
            stmt = stmt.limit(int(limit))
        except Exception:
            pass
    if offset:
        try:
            stmt = stmt.offset(int(offset))
        except Exception:
            pass
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
        stmt = _apply_entity_filters(stmt, entities)
        stmt = stmt.options(
            selectinload(CaseMaster.police_station),
            selectinload(CaseMaster.crime_major_head),
            selectinload(CaseMaster.crime_minor_head),
        )
        stmt = _apply_sort_and_pagination(stmt, entities, intent)
        return stmt

    if intent == "SEARCH_ACCUSED":
        stmt = select(Accused)
        # Apply accused‑specific filter directly.
        if entities.get("accused_name"):
            stmt = stmt.where(Accused.accused_name.ilike(entities["accused_name"]))
        # For any case‑level filters, join back to CaseMaster only once.
        case_entities = {k: v for k, v in entities.items() if k not in {"accused_name", "victim_name", "complainant_name"}}
        if any(case_entities.values()):
            stmt = stmt.join(Accused.case_master)
            stmt = _apply_entity_filters(stmt, case_entities)
        # Eager load related case master to avoid N+1 queries.
        stmt = stmt.options(selectinload(Accused.case_master))
        stmt = _apply_sort_and_pagination(stmt, entities, intent)
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
        # Eager load related case master to avoid N+1 queries.
        stmt = stmt.options(selectinload(Victim.case_master))
        stmt = _apply_sort_and_pagination(stmt, entities, intent)
        return stmt

    if intent == "CRIME_TREND":
        stmt = (
            select(CaseMaster.crime_major_head_id, func.count().label("count"))
            .group_by(CaseMaster.crime_major_head_id)
        )
        stmt = _apply_entity_filters(stmt, entities)
        # Apply optional pagination (limit/offset) after ordering by count descending.
        stmt = stmt.order_by(func.count().desc())
        stmt = _apply_sort_and_pagination(stmt, entities, intent)
        return stmt

    if intent == "HOTSPOT":
        stmt = (
            select(CaseMaster.latitude, CaseMaster.longitude, func.count().label("count"))
            .where(CaseMaster.latitude != None)
            .group_by(CaseMaster.latitude, CaseMaster.longitude)
        )
        stmt = _apply_entity_filters(stmt, entities)
        # Order by hotspot count descending and apply pagination.
        stmt = stmt.order_by(func.count().desc())
        stmt = _apply_sort_and_pagination(stmt, entities, intent)
        return stmt

    if intent == "AGGREGATE_COUNT":
        # Accused count when accused-specific filter is present
        if entities.get("accused_name"):
            stmt = select(func.count(Accused.accused_master_id))
            stmt = stmt.where(Accused.accused_name.ilike(entities["accused_name"]))
            # Apply any case-level filters via join
            case_entities = {k: v for k, v in entities.items() if k not in {"accused_name", "victim_name", "complainant_name"}}
            if any(case_entities.values()):
                stmt = stmt.join(Accused.case_master)
                stmt = _apply_entity_filters(stmt, case_entities)
            return stmt
        # Victim count when victim-related filters are present
        if entities.get("victim_name") or entities.get("gender") or entities.get("age"):
            stmt = select(func.count(Victim.victim_master_id))
            if entities.get("victim_name"):
                stmt = stmt.where(Victim.victim_name.ilike(f"%{entities['victim_name']}%"))
            if entities.get("gender"):
                stmt = stmt.where(Victim.gender_id == entities["gender"])
            if entities.get("age"):
                stmt = _filter_age(stmt, entities["age"])
            case_entities = {k: v for k, v in entities.items() if k not in {"victim_name", "gender", "age", "accused_name", "complainant_name"}}
            if any(case_entities.values()):
                stmt = stmt.join(Victim.case_master)
                stmt = _apply_entity_filters(stmt, case_entities)
            return stmt
        # Default case count (no specific entity filters)
        stmt = select(func.count(CaseMaster.case_master_id))
        stmt = _apply_entity_filters(stmt, entities)
        return stmt
