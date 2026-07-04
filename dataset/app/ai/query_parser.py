from typing import Dict, Any


def parse_query(query: str) -> Dict[str, Any]:
    """Parse a natural‑language query using simple rule‑based extraction.

    Returns a dictionary with the detected ``intent`` (or ``None``) and a
    mapping of entities relevant to the KSP Sentinel AI domain.
    """
    # Normalise the query for case‑insensitive matching
    lowered = query.lower()

    # Very basic intent detection – mirrors intent_classifier patterns
    intent = None
    if "case" in lowered or "fir" in lowered or "search" in lowered:
        intent = "SEARCH_CASES"
    elif "accused" in lowered or "suspect" in lowered:
        intent = "SEARCH_ACCUSED"
    elif "victim" in lowered:
        intent = "SEARCH_VICTIMS"
    elif "trend" in lowered or "statistics" in lowered:
        intent = "CRIME_TREND"
    elif "hotspot" in lowered or "heat map" in lowered:
        intent = "HOTSPOT"
    elif "report" in lowered or "dashboard" in lowered:
        intent = "REPORTS"

    # Simple entity extraction – look for known keywords
    entities = {
        "crime": None,
        "district": None,
        "date_range": None,
    }

    words = lowered.split()
    for idx, word in enumerate(words):
        if word in {"robbery", "theft", "assault", "fraud"}:
            entities["crime"] = word
        if word in {"district", "area", "zone"}:
            if idx + 1 < len(words):
                entities["district"] = words[idx + 1]
        if word in {"today", "yesterday", "last", "month", "year"}:
            entities["date_range"] = word

    return {"intent": intent, "entities": entities}
