"""
Production‑ready response formatter for the KSP Sentinel AI.
Generates intent‑specific, entity‑aware summary strings.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

__all__ = ["format_response"]

def _search_cases_summary(count: int, actual_length: int, entities: Dict[str, Any]) -> str:
    if count == 0:
        return (
            "No cases matched your search.\n\n"
            "**Possible reasons:**\n"
            "- The filters might be too restrictive.\n"
            "- Check for typos in the location or crime name.\n\n"
            "**Suggested actions:**\n"
            "- Remove filters\n"
            "- Search broadly (e.g. 'Show theft cases')"
        )
    parts: List[str] = []
    crime = entities.get("crime_head")
    if crime:
        parts.append(f"{crime} cases")
    else:
        parts.append("cases")
        
    summary = f"Displaying first {actual_length} of {count} {' '.join(parts)}" if count > actual_length else f"Found {count} {' '.join(parts)}"
    
    district = entities.get("district")
    if district:
        summary += f" in {district}"
    year = entities.get("year")
    if year:
        summary += f" during {year}"
    summary += "."
    return summary

def _fir_lookup_summary(count: int, actual_length: int, entities: Optional[Dict[str, Any]] = None) -> str:
    if count == 0:
        # Build dynamic suggestions from DB if available
        dynamic = entities.get("_dynamic_suggestions", []) if entities else []
        suggestion_lines = ""
        if dynamic:
            suggestion_lines = "\n".join(f"- {s}" for s in dynamic[:5])
        else:
            suggestion_lines = "- KSP-0001\n- KSP-0050\n- KSP-000100"

        return (
            "FIR not found.\n\n"
            "**Possible reasons:**\n"
            "- The FIR number might not exist in the database.\n"
            "- Check the format — database uses KSP-0001 style numbering.\n"
            "- The case might be registered under a different jurisdiction.\n\n"
            "**Try these valid FIR numbers:**\n"
            f"{suggestion_lines}"
        )
    fir_num = entities.get("fir_number") if entities else None
    if fir_num:
        return f"Displaying first {actual_length} of {count} result(s) for FIR {fir_num}." if count > actual_length else f"Found {count} result(s) for FIR {fir_num}."
    return f"Displaying first {actual_length} of {count} FIR result(s)." if count > actual_length else f"Found {count} FIR result(s)."

def _search_accused_summary(count: int, actual_length: int, _: Optional[Dict[str, Any]] = None) -> str:
    if count == 0:
        return (
            "No accused matched your search.\n\n"
            "**Possible reasons:**\n"
            "- Name spelling might be incorrect.\n"
            "- The individual may not have a recorded case.\n\n"
            "**Suggested actions:**\n"
            "- Use partial names (e.g. 'Search accused Vik')\n"
            "- Remove filters"
        )
    return f"Displaying first {actual_length} of {count} accused matching the supplied filters." if count > actual_length else f"Found {count} accused matching the supplied filters."

def _search_victims_summary(count: int, actual_length: int, _: Optional[Dict[str, Any]] = None) -> str:
    if count == 0:
        return (
            "No victims matched your search.\n\n"
            "**Suggested actions:**\n"
            "- Remove filters\n"
            "- Search broadly"
        )
    return f"Displaying first {actual_length} of {count} victims matching filters." if count > actual_length else f"Found {count} victims matching filters."

def _hotspot_summary(_: int, __: int, ___: Optional[Dict[str, Any]] = None) -> str:
    return "Top crime hotspots generated."

def _aggregate_count_summary(count: int, _: int, __: Optional[Dict[str, Any]] = None) -> str:
    return f"There are {count} matching records."

def _generic_summary(count: int, actual_length: int, _: Optional[Dict[str, Any]] = None) -> str:
    return f"Displaying first {actual_length} of {count} records returned." if count > actual_length else f"Found {count} matching records."

# Mapping intent to its summary builder
_SUMMARY_BUILDERS: Dict[str, Any] = {
    "FIR_LOOKUP": _fir_lookup_summary,
    "SEARCH_CASES": _search_cases_summary,
    "SEARCH_ACCUSED": _search_accused_summary,
    "SEARCH_VICTIMS": _search_victims_summary,
    "CRIME_TREND": lambda c, a, e: "Crime trend analysis generated.",
    "HOTSPOT": _hotspot_summary,
    "REPORTS": lambda c, a, e: "Dashboard statistics generated.",
    "AGGREGATE_COUNT": _aggregate_count_summary,
    "REPEAT_OFFENDERS": lambda c, a, e: f"Displaying {c} repeat offender(s)." if c > 0 else "No repeat offenders found.",
    "MOST_WANTED": lambda c, a, e: f"Displaying {a} of {c} most wanted accused profiles." if c > a else f"Found {c} most wanted accused profiles.",
}

def _build_summary(intent: str, count: int, actual_length: int, entities: Optional[Dict[str, Any]] = None) -> str:
    builder = _SUMMARY_BUILDERS.get(intent)
    if builder:
        try:
            return builder(count, actual_length, entities)
        except TypeError:
            return builder(count, entities)
    return _generic_summary(count, actual_length, entities)

def format_response(intent: str, results: List[Dict[str, Any]], entities: Optional[Dict[str, Any]] = None, total_count: int = -1) -> Dict[str, Any]:
    """Format AI query results into a consistent API response.

    Args:
        intent: Classified intent string.
        results: List of serialized rows.
        entities: Parsed entities dict (may be ``None``).
        total_count: Total records available if paginated.

    Returns:
        Dict with ``summary``, ``count`` and ``results``.
    """
    actual_length = len(results)
    count = total_count if total_count >= 0 else actual_length

    if intent == "AGGREGATE_COUNT" and results:
        row = results[0]
        if isinstance(row, dict) and row:
            # Extract first value from the mapping (e.g. count_1 or count)
            count = int(list(row.values())[0])
        elif isinstance(row, (int, float)):
            count = int(row)

    summary = _build_summary(intent, count, actual_length, entities)
    return {
        "summary": summary,
        "count": count,
        "results": results,
    }