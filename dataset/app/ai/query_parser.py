"""Production‑ready query parser for the KSP Sentinel AI.

The parser is *entity‑only* – intent detection is performed separately by
`app.ai.intent_classifier`.  It extracts values from a natural‑language query
using a configurable set of regular‑expression patterns.  The design is
schema‑aware (entity names correspond to real attributes in the SQLAlchemy
models) but does **not** hard‑code any specific values such as crime types,
district names, or police stations.  Adding a new entity only requires a new
entry in the ``ENTITY_PATTERNS`` mapping – the core extraction logic remains
unchanged.

The function returns a dictionary compatible with the existing pipeline:

```python
{
    "intent": None,               # intent is filled later by the classifier
    "entities": { ... }           # extracted values, ``None`` when missing
}
```
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, Optional
from app.ai.entity_config import ENTITY_CONFIG

# ---------------------------------------------------------------------------
# Configurable regex patterns for each entity.  Patterns capture a single
# group – the value to be stored.  All patterns are case‑insensitive.
# ---------------------------------------------------------------------------
# Entity patterns moved to entity_config.py


def _apply_pattern(pattern: str, text: str) -> Optional[str]:
    """Return the first captured group for *pattern* in *text*.

    The regex is compiled with ``re.IGNORECASE``; if no match is found ``None``
    is returned.
    """
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else None


def _parse_date_range(text: str) -> Optional[Dict[str, str]]:
    """Parse ``after <Month> <Year>`` / ``before <Month> <Year>`` expressions.

    Returns ``{"gt": "YYYY‑MM‑DD"}`` for an "after" clause or ``{"lt": ...}``
    for a "before" clause.  The ISO‑formatted date string is used to keep the
    downstream SQL generator simple.
    """
    after_match = re.search(ENTITY_CONFIG["date_range_after"]["pattern"], text, re.IGNORECASE)
    before_match = re.search(ENTITY_CONFIG["date_range_before"]["pattern"], text, re.IGNORECASE)
    if after_match:
        try:
            dt = datetime.strptime(f"{after_match.group(1)} {after_match.group(2)}", "%B %Y")
            return {"gt": dt.date().isoformat()}
        except ValueError:
            return None
    if before_match:
        try:
            dt = datetime.strptime(f"{before_match.group(1)} {before_match.group(2)}", "%B %Y")
            return {"lt": dt.date().isoformat()}
        except ValueError:
            return None
    return None


def _parse_age(text: str) -> Optional[Dict[str, int]]:
    """Extract age filters.

    ``{"lt": 18}`` for "under 18" or ``{"eq": 30}`` for "age 30".
    """
    under = re.search(ENTITY_CONFIG["age_under"]["pattern"], text, re.IGNORECASE)
    exact = re.search(ENTITY_CONFIG["age_exact"]["pattern"], text, re.IGNORECASE)
    if under:
        return {"lt": int(under.group(1))}
    if exact:
        return {"eq": int(exact.group(1))}
    return None


def parse_query(query: str) -> Dict[str, Any]:
    """Extract entities from *query*.

    The function does **not** perform intent classification – that is handled
    elsewhere.  It returns a dictionary with ``intent`` set to ``None`` (the
    caller may replace it with the classified intent) and an ``entities`` map
    whose keys correspond to real column names used throughout the ORM models.
    Missing values are represented as ``None``.
    """
    lowered = query.lower()

    # ---------------------------------------------------------------------
    # Entity extraction using the configurable patterns.
    # ---------------------------------------------------------------------
    entities: Dict[str, Any] = {}
    for name, config in ENTITY_CONFIG.items():
        entity_type = config.get("type", "simple")
        pattern = config.get("pattern")
        if not pattern:
            continue
        if entity_type == "simple":
            entities[name] = _apply_pattern(pattern, lowered)
        elif entity_type == "date_range":
            entities[name] = _parse_date_range(lowered)
        elif entity_type == "age":
            entities[name] = _parse_age(lowered)
        else:
            entities[name] = None


    # Normalise numeric fields where appropriate
    for numeric_key in ["year", "limit", "offset"]:
        if numeric_key in entities and entities[numeric_key] is not None:
            try:
                entities[numeric_key] = int(entities[numeric_key])
            except ValueError:
                entities[numeric_key] = None

    # Normalise sort_order synonyms
    if entities.get("sort_order"):
        order = entities["sort_order"].lower()
        if order in {"oldest", "asc"}:
            entities["sort_order"] = "asc"
        elif order in {"newest", "latest", "desc"}:
            entities["sort_order"] = "desc"
        else:
            entities["sort_order"] = None

    # Latitude/longitude remain strings; the downstream generator can cast
    # them to the required numeric type.

    return {"intent": None, "entities": entities}
