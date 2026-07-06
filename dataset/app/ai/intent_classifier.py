"""Intent classification for natural‑language police queries.

This module implements a lightweight rule‑based classifier that maps a user
utterance to one of the supported intents. Regular expressions are used to
match keywords associated with each intent – no LLM required.

Priority order (first match wins):
    1. PREDICT_CRIME    – prediction / forecasting language
    2. AGGREGATE_COUNT  – "how many", "total", "count"
    3. CRIME_TREND      – "trend", "statistics", "crime rate"
    4. HOTSPOT          – hotspot / heat-map language
    5. SEARCH_ACCUSED   – suspect / accused lookup
    6. SEARCH_VICTIMS   – victim lookup
    7. REPORTS          – report / dashboard
    8. SEARCH_CASES     – generic case search (catch-all)
"""

from __future__ import annotations

import re
from collections import OrderedDict
from enum import Enum
from typing import Dict, List, Optional


class Intent(str, Enum):
    """Supported query intents."""

    PREDICT_CRIME   = "PREDICT_CRIME"
    SEARCH_CASES    = "SEARCH_CASES"
    SEARCH_ACCUSED  = "SEARCH_ACCUSED"
    SEARCH_VICTIMS  = "SEARCH_VICTIMS"
    CRIME_TREND     = "CRIME_TREND"
    HOTSPOT         = "HOTSPOT"
    REPORTS         = "REPORTS"
    AGGREGATE_COUNT = "AGGREGATE_COUNT"


# ---------------------------------------------------------------------------
# Pattern lists — listed in priority order inside _PATTERN_MAP below.
# ---------------------------------------------------------------------------

_PATTERNS_PREDICT: List[str] = [
    r"\bpredict\b",
    r"\bprediction\b",
    r"\bforecast\b",
    r"\bfuture crime\b",
    r"\bfuture cases\b",
    r"\bexpected crime\b",
    r"\bcrime prediction\b",
    r"\bnext month\b",
    r"\bnext week\b",
    r"\bnext year\b",
    r"\bwill crime increase\b",
    r"\bwill theft increase\b",
    r"\bwill .+ increase\b",
    r"\blikely\b",
    r"\bprobability\b",
]

_PATTERNS_AGGREGATE: List[str] = [
    r"\bhow many\b",
    r"\btotal\b",
    r"\bcount\b",
    r"\bnumber of\b",
    r"\bnumbers? of\b",
    r"\bnum\b",
    r"\baggregate\b",
    r"\bstats?\b",
]

_PATTERNS_TREND: List[str] = [
    r"\btrend\b",
    r"\bstatistics\b",
    r"\bcrime\s+rate\b",
    r"\bcrime.*rate\b",
    r"top\s+crimes",
    r"\bcrime\s+trend\b",
]

_PATTERNS_HOTSPOT: List[str] = [
    r"\bhotspots?\b",
    r"\bheat\s+map\b",
    r"\barea.*high.*crime\b",
    r"crime\s+hotspots?",
    r"show\s+hotspots?",
    r"list\s+hotspots?",
]

_PATTERNS_ACCUSED: List[str] = [
    r"\baccused\b",
    r"\bsuspect\b",
    r"\bcriminal\b",
    r"named\s+\w+",
]

_PATTERNS_VICTIMS: List[str] = [
    r"\bvictims?\b",
    r"\binjured\b",
    r"victims?\s+under\s+\d+",
    r"victims?\s+aged?\s+\d+",
    r"show\s+victims?",
    r"list\s+victims?",
]

_PATTERNS_REPORTS: List[str] = [
    r"\breport\b",
    r"\bdashboard\b",
    r"statistics\s+dashboard",
]

# SEARCH_CASES is the catch-all: explicit search verbs OR bare crime keywords.
# It is evaluated LAST so higher-priority intents win on ambiguous queries.
_PATTERNS_SEARCH_CASES: List[str] = [
    r"show\s+.*cases?",
    r"list\s+.*cases?",
    r"find\s+.*cases?",
    r"get\s+.*cases?",
    r"\bsearch\b",
    r"\bfirs?\b",
    r"\bcases?\b",
    r"\btheft\b",
    r"\brobbery\b",
    r"\bmurder\b",
    r"\bassault\b",
    r"\bfraud\b",
    r"\bkidnapping\b",
    r"\bburglary\b",
    r"\bcrime\b",
]

# ---------------------------------------------------------------------------
# Ordered map — OrderedDict guarantees iteration order on all Python versions.
# Priority: first entry = highest priority.
# ---------------------------------------------------------------------------
_PATTERN_MAP: Dict[Intent, List[str]] = OrderedDict([
    (Intent.PREDICT_CRIME,   _PATTERNS_PREDICT),
    (Intent.AGGREGATE_COUNT, _PATTERNS_AGGREGATE),
    (Intent.CRIME_TREND,     _PATTERNS_TREND),
    (Intent.HOTSPOT,         _PATTERNS_HOTSPOT),
    (Intent.SEARCH_ACCUSED,  _PATTERNS_ACCUSED),
    (Intent.SEARCH_VICTIMS,  _PATTERNS_VICTIMS),
    (Intent.REPORTS,         _PATTERNS_REPORTS),
    (Intent.SEARCH_CASES,    _PATTERNS_SEARCH_CASES),
])

# Pre‑compile patterns for performance.
_COMPILED: Dict[Intent, re.Pattern] = {
    intent: re.compile("|".join(pats), re.IGNORECASE)
    for intent, pats in _PATTERN_MAP.items()
}


def classify_intent(text: str) -> Optional[Intent]:
    """Return the first matching :class:`Intent` for *text*.

    Intents are evaluated in priority order (PREDICT_CRIME first,
    SEARCH_CASES last).  Returns ``None`` if nothing matches.
    """
    for intent, regex in _COMPILED.items():
        if regex.search(text):
            return intent
    return None
