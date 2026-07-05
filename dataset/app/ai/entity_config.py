from typing import Dict

# Entity configuration for the AI query parser.
# Each entry maps an entity name to its extraction pattern and optional metadata used by ``app.ai.query_parser``.
# The configuration is deliberately minimal – only the regular‑expression pattern and a ``type`` field that tells the parser how to interpret the matched value.
# Adding a new entity requires editing *only* this file.
# The parser extracts values based on these patterns.

ENTITY_CONFIG: Dict[str, Dict[str, str]] = {
    "fir_number": {"pattern": r"\b(ksp-\d{4,})\b", "type": "simple"},
    "crime_head": {"pattern": r"(?:crime head\s*[:\-]?\s*)?(\w+)\s+cases?", "type": "simple"},
    "district": {"pattern": r"(?:in|from)\s+([a-z]+(?:\s+[a-z]+)*)\s*(?:district)?", "type": "simple"},
    "police_station": {"pattern": r"(?:in|from)\s+([a-z]+(?:\s+[a-z]+)*)\s+police station", "type": "simple"},
    "accused_name": {"pattern": r"accused\s*(?:named)?\s*([a-z]+(?:\s+[a-z]+)*)", "type": "simple"},
    "victim_name": {"pattern": r"victim\s*(?:named)?\s*([a-z]+(?:\s+[a-z]+)*)", "type": "simple"},
    "complainant_name": {"pattern": r"complainant\s*(?:named)?\s*([a-z]+(?:\s+[a-z]+)*)", "type": "simple"},
    "section": {"pattern": r"section\s*[:\-]?\s*(\w+)", "type": "simple"},
    "act": {"pattern": r"act\s*[:\-]?\s*([a-z]+)", "type": "simple"},
    "date_range_after": {"pattern": r"after\s+(\w+)\s+(\d{4})", "type": "date_range"},
    "date_range_before": {"pattern": r"before\s+(\w+)\s+(\d{4})", "type": "date_range"},
    "year": {"pattern": r"\b(20\d{2})\b", "type": "simple"},
    "gender": {"pattern": r"\b(male|female)\b", "type": "simple"},
    "age_under": {"pattern": r"under\s+(\d+)", "type": "age"},
    "age_exact": {"pattern": r"(?:age|aged)\s+(\d+)", "type": "age"},
    "status": {"pattern": r"status\s*[:\-]?\s*(\w+)", "type": "simple"},
    "latitude": {"pattern": r"latitude\s*[:\-]?\s*([-+]?\d*\.?\d+)", "type": "simple"},
    "longitude": {"pattern": r"longitude\s*[:\-]?\s*([-+]?\d*\.?\d+)", "type": "simple"},
    # Pagination and sorting entities
    "limit": {"pattern": r"\b(?:latest|newest|first|top)\s+(\d+)\b", "type": "simple"},
    "offset": {"pattern": r"\b(?:skip|offset)\s+(\d+)\b", "type": "simple"},
    "sort_by": {"pattern": r"\b(cases?|firs?|accused|victims?)\b", "type": "simple"},
    "sort_order": {"pattern": r"\b(asc|desc|oldest|newest|latest)\b", "type": "simple"},
}
