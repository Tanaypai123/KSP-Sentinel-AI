"""
Production‑ready response formatter for the KSP Sentinel AI.
Generates intent‑specific, entity‑aware summary strings.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

__all__ = ["format_response"]

from app.ai.response_templates import get_no_records_found, get_fir_not_found

def _search_cases_summary(count: int, actual_length: int, entities: Dict[str, Any]) -> str:
    district = entities.get("district")
    crime = entities.get("crime_head") or "crime"
    
    if count == 0:
        if entities.get("structured_is_valid_district") and district:
            return f"I identified the district as {district}. However, no matching FIRs were found for your current search filters."
        return get_no_records_found(entities.get("crime_head", "cases"))

    summary = f"I found {count} {crime} cases"
    if district:
        summary += f" registered in {district}"
    
    year = entities.get("year")
    if year:
        summary += f" during {year}"
    summary += "."
    
    if count > 0:
        summary += "\n\nThe latest matching FIRs are displayed below."
        
    return summary

def _fir_lookup_summary(count: int, actual_length: int, entities: Optional[Dict[str, Any]] = None) -> str:
    if count == 0:
        # Build dynamic suggestions from DB if available
        dynamic = entities.get("_dynamic_suggestions", []) if entities else []
        suggestions = dynamic[:3] if dynamic else ["KSP-0001", "KSP-0050", "KSP-0100"]
        return get_fir_not_found(suggestions)
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

def format_response(intent: str, results: List[Dict[str, Any]], entities: Optional[Dict[str, Any]] = None, total_count: int = -1, db: Any = None) -> Dict[str, Any]:
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
            count = int(list(row.values())[0])
        elif isinstance(row, (int, float)):
            count = int(row)

    if count == 0:
        return {
            "summary": get_no_records_found(entities.get("crime_head", "records")),
            "count": 0,
            "results": []
        }

    # 1. Executive Summary
    entities = entities or {}
    crime = entities.get("crime_head") or "case"
    district = entities.get("district") or "the jurisdiction"
    
    # Capitalize appropriately
    crime_str = crime.replace('_', ' ').lower()
    if intent == "SEARCH_ACCUSED":
        exec_summary = f"I identified {count} accused profiles matching your criteria."
    elif intent == "SEARCH_VICTIMS":
        exec_summary = f"I identified {count} victim records matching your criteria."
    elif intent == "FIR_LOOKUP":
        fir_num = entities.get("identifiers", [""])[0] if entities.get("identifiers") else "the requested FIR"
        exec_summary = f"I retrieved the details for FIR {fir_num}."
    else:
        exec_summary = f"I identified {count} {crime_str} records in {district} matching your request."

    # 2. Investigation Findings (extracted inline natively if single record)
    findings = ""
    if actual_length == 1:
        r = results[0]
        if intent == "FIR_LOOKUP":
            findings = f"**Crime Type:** {r.get('crime_category', 'Unknown')}\n" \
                       f"**District:** {r.get('district_name', 'Unknown')}\n" \
                       f"**Police Station:** {r.get('police_station_name', 'Unknown')}\n" \
                       f"**Current Status:** {r.get('status_name', 'Pending')}"
        elif intent == "SEARCH_ACCUSED":
            findings = f"**Accused Name:** {r.get('accused_name', 'Unknown')}\n" \
                       f"**Age:** {r.get('age_year', 'Unknown')}"
    elif actual_length > 1:
        findings = f"The complete list of {actual_length} records is available in the data grid below for detailed review."

    # 3. Investigation Insights & 4. AI Observations & 5. Recommended Actions
    from app.ai.insights import IntelligenceEngine
    dynamic_intel = IntelligenceEngine.generate_dynamic_insights(results, intent, db)
    
    observations = dynamic_intel.get("observations", [])
    recommendations = dynamic_intel.get("recommendations", [])
    similar_cases = dynamic_intel.get("similar_cases", [])
    
    if len(results) < 2 and intent != "FIR_LOOKUP":
        obs_str = "Insufficient evidence to generate meaningful investigation insights."
    else:
        obs_str = "\n".join(f"• {obs}" for obs in observations) if observations else "No significant investigative pattern was detected."
        
    rec_str = "\n".join(f"• {rec}" for rec in recommendations) if recommendations else "• Review the attached records."

    # Build the 5-Part Markdown Structure
    markdown = f"### 1. Executive Summary\n{exec_summary}\n\n"
    markdown += f"### 2. Key Findings\n{findings}\n\n"
    markdown += f"### 3. Investigation Insights & AI Observations\n{obs_str}\n\n"
    markdown += f"### 4. Recommended Next Actions\n{rec_str}"
    
    if similar_cases:
        markdown += f"\n\n### 5. Related Cases\n{similar_cases}"

    return {
        "summary": markdown,
        "count": count,
        "results": results,
    }