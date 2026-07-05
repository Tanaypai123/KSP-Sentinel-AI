"""
Production-ready response formatter for the KSP Sentinel AI.
"""

from __future__ import annotations

from typing import Any, Dict, List

__all__ = ["format_response"]

_INTENT_SUMMARIES: Dict[str, str] = {
    "SEARCH_CASES": "Found {count} matching case(s).",
    "SEARCH_ACCUSED": "Found {count} accused record(s).",
    "SEARCH_VICTIMS": "Found {count} victim record(s).",
    "CRIME_TREND": "Crime trend analysis generated.",
    "HOTSPOT": "Crime hotspot analysis generated.",
    "REPORTS": "Dashboard statistics generated.",
}


def _build_summary(intent: str, count: int) -> str:
    template = _INTENT_SUMMARIES.get(intent)

    if template is None:
        return f"Found {count} result(s)."

    return template.format(count=count)


def format_response(intent: str, results: List[Any]) -> Dict[str, Any]:
    """
    Format AI query results into a consistent API response.
    """

    count = len(results)

    return {
        "summary": _build_summary(intent, count),
        "count": count,
        "results": results,
    }