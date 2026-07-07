"""
Production‑ready response formatter for the KSP Sentinel AI.
Generates intent‑specific, entity‑aware summary strings.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

__all__ = ["format_response"]

def _search_cases_summary(count: int, entities: Dict[str, Any]) -> str:
    # Build a readable phrase like "15 theft cases were found in Mysore during 2025."
    parts: List[str] = []
    crime = entities.get("crime_head")
    if crime:
        parts.append(f"{crime} cases")
    else:
        parts.append("cases")
    summary = f"{count} {' '.join(parts)}"
    district = entities.get("district")
    if district:
        summary += f" in {district}"
    year = entities.get("year")
    if year:
        summary += f" during {year}"
    summary += "."
    return summary

def _search_accused_summary(count: int, _: Optional[Dict[str, Any]] = None) -> str:
    return f"Found {count} accused matching the supplied filters."

def _search_victims_summary(count: int, _: Optional[Dict[str, Any]] = None) -> str:
    return f"Found {count} victim records."

def _hotspot_summary(_: int, __: Optional[Dict[str, Any]] = None) -> str:
    return "Top crime hotspots generated."

def _aggregate_count_summary(count: int, _: Optional[Dict[str, Any]] = None) -> str:
    return f"There are {count} matching records."

def _generic_summary(count: int, _: Optional[Dict[str, Any]] = None) -> str:
    return f"Found {count} result(s)."

# Mapping intent to its summary builder
_SUMMARY_BUILDERS: Dict[str, Any] = {
    "SEARCH_CASES": _search_cases_summary,
    "SEARCH_ACCUSED": _search_accused_summary,
    "SEARCH_VICTIMS": _search_victims_summary,
    "CRIME_TREND": lambda c, e: "Crime trend analysis generated.",
    "HOTSPOT": _hotspot_summary,
    "REPORTS": lambda c, e: "Dashboard statistics generated.",
    "AGGREGATE_COUNT": _aggregate_count_summary,
}

def _build_summary(intent: str, count: int, entities: Optional[Dict[str, Any]] = None) -> str:
    builder = _SUMMARY_BUILDERS.get(intent, _generic_summary)
    try:
        return builder(count, entities)
    except TypeError:
        return builder(count)

def format_response(intent: str, results: List[Any], entities: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Format AI query results into a consistent API response.

    Args:
        intent: Classified intent string.
        results: List of serialized rows.
        entities: Parsed entities dict (may be ``None``).

    Returns:
        Dict with ``summary``, ``count`` and ``results``.
    """
    count = len(results)
    if intent == "AGGREGATE_COUNT" and results:
        row = results[0]
        if isinstance(row, dict) and row:
            # Extract first value from the mapping (e.g. count_1 or count)
            count = int(list(row.values())[0])
        elif isinstance(row, (int, float)):
            count = int(row)
    summary = _build_summary(intent, count, entities)
    return {
        "summary": summary,
        "count": count,
        "results": results,
    }