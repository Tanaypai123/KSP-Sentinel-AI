"""Intent classification for natural‑language police queries.

This module implements a lightweight rule‑based classifier that maps a user
utterance to one of the supported intents. Regular expressions are used to
match keywords associated with each intent – no LLM required.

Public API:
- :class:`Intent` – enum of supported intents.
- :func:`classify_intent` – returns the matching ``Intent`` or ``None``.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Optional, List, Dict

class Intent(str, Enum):
    """Supported query intents."""

    SEARCH_CASES = "SEARCH_CASES"
    SEARCH_ACCUSED = "SEARCH_ACCUSED"
    SEARCH_VICTIMS = "SEARCH_VICTIMS"
    CRIME_TREND = "CRIME_TREND"
    HOTSPOT = "HOTSPOT"
    REPORTS = "REPORTS"

# Mapping intent -> list of regex patterns (case‑insensitive)
_PATTERN_MAP: Dict[Intent, List[str]] = {
    Intent.SEARCH_CASES: [r"\\bcase\\b", r"\\bfir\\b", r"\\bsearch\\b", r"\\breport\\b"],
    Intent.SEARCH_ACCUSED: [r"\\baccused\\b", r"\\bsuspect\\b", r"\\bcriminal\\b"],
    Intent.SEARCH_VICTIMS: [r"\\bvictim\\b", r"\\binjured\\b"],
    Intent.CRIME_TREND: [r"\\btrend\\b", r"\\bstatistics?\\b", r"\\bcrime.*rate\\b"],
    Intent.HOTSPOT: [r"\\bhotspot\\b", r"\\bheat map\\b", r"\\barea.*high.*crime\\b"],
    Intent.REPORTS: [r"\\breport\\b", r"\\bdashboard\\b"],
}

# Pre‑compile patterns for performance
_COMPILED: Dict[Intent, re.Pattern] = {
    intent: re.compile(r"|".join(pats), re.IGNORECASE)
    for intent, pats in _PATTERN_MAP.items()
}

def classify_intent(text: str) -> Optional[Intent]:
    """Return the first matching :class:`Intent` for *text*.

    If none of the patterns match, ``None`` is returned.
    """
    for intent, regex in _COMPILED.items():
        if regex.search(text):
            return intent
    return None
