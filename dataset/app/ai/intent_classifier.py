"""Intent classification for natural‑language police queries.

This module implements a lightweight rule‑based classifier that maps a user
utterance to one of the supported intents. Regular expressions are used to
match keywords associated with each intent – no LLM required.
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

# Mapping intent → list of regex patterns (case‑insensitive)
_PATTERN_MAP: Dict[Intent, List[str]] = {
    Intent.SEARCH_CASES: [
    r"\bcases?\b",
    r"\bfirs?\b",
    r"\bsearch\b",
    r"\breport\b",

    r"show\s+.*cases?",
    r"list\s+.*cases?",
    r"find\s+.*cases?",

    r"\btheft\b",
    r"\brobbery\b",
    r"\bmurder\b",
    r"\bassault\b",
    r"\bfraud\b",
    r"\bkidnapping\b",
    r"\bburglary\b",
    r"\bcrime\b",
    ], 
    Intent.SEARCH_ACCUSED: [
        r"\baccused\b",
        r"\bsuspect\b",
        r"\bcriminal\b",
        r"named\s+\w+",
    ],
    Intent.SEARCH_VICTIMS: [
        r"\bvictims?\b",
        r"\binjured\b",
        r"victims?\s+under\s+\d+",
        r"victims?\s+aged?\s+\d+",
        r"show\s+victims?",
        r"list\s+victims?",
    ],
    Intent.CRIME_TREND: [
        r"\btrend\b",
        r"\bstatistics?\b",
        r"\bcrime.*rate\b",
        r"top\s+crimes",
    ],
    Intent.HOTSPOT: [
    r"\bhotspot\b",
    r"\bhotspots\b",
    r"\bheat\s+map\b",
    r"\barea.*high.*crime\b",
    r"crime\s+hotspots?",
    r"show\s+hotspots?",
    r"list\s+hotspots?",
    ],
    Intent.REPORTS: [
        r"\breport\b",
        r"\bdashboard\b",
        r"statistics\s+dashboard",
    ],
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
