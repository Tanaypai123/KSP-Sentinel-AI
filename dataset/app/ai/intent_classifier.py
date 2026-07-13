"""Intent classification for natural‑language police queries.

This module implements a lightweight rule‑based classifier that maps a user
utterance to one of the supported intents. Regular expressions are used to
match keywords associated with each intent. Supports confidence scoring.
"""

from __future__ import annotations

import re
from collections import OrderedDict
from enum import Enum
from typing import Dict, List, Optional, Tuple


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
    FIR_LOOKUP      = "FIR_LOOKUP"
    REPEAT_OFFENDERS = "REPEAT_OFFENDERS"
    MOST_WANTED     = "MOST_WANTED"
    SEARCH_LOCATION = "SEARCH_LOCATION"
    SEARCH_COURT = "SEARCH_COURT"
    SEARCH_COMPLAINANT = "SEARCH_COMPLAINANT"
    SEARCH_POLICE_STATION = "SEARCH_POLICE_STATION"
    SEARCH_OFFICER = "SEARCH_OFFICER"
    SEARCH_CRIME_TYPE = "SEARCH_CRIME_TYPE"
    SEARCH_ACT_SECTION = "SEARCH_ACT_SECTION"
    STATISTICS = "STATISTICS"
    
    # Conversational Intents
    GREETING        = "GREETING"
    GOODBYE         = "GOODBYE"
    THANKS          = "THANKS"
    HELP            = "HELP"
    BOT_IDENTITY    = "BOT_IDENTITY"
    BOT_CAPABILITIES = "BOT_CAPABILITIES"
    GENERAL_CHAT    = "GENERAL_CHAT"
    UNKNOWN         = "UNKNOWN"


# Triggers indicating strong intent
_STRONG_TRIGGERS = {
    Intent.PREDICT_CRIME: [r"\bpredict\b", r"\bprediction\b", r"\bforecast\b", r"\bfuture\b", r"\bnext month\b", r"\bwill crime increase\b", r"\bwill theft increase\b"],
    Intent.AGGREGATE_COUNT: [r"\bhow many\b", r"\btotal\b", r"\bcount\b", r"\bnumber of\b", r"\bnum\b", r"\baggregate\b"],
    Intent.CRIME_TREND: [r"\btrend\b", r"\bstatistics\b", r"\bcrime\s+rate\b", r"\bcrime.*rate\b", r"\b(?:top|highest|most\s+common|frequent)\s+(?:crime\s+categories|crimes?|categories)\b", r"crime\s+(?:distribution|breakdown|analysis|frequency)\b", r"\bcrime\s+categor(?:y|ies)\s+ranking\b"],
    Intent.HOTSPOT: [r"\bhotspots?\b", r"\bheat\s+map\b", r"\barea.*high.*crime\b"],
    Intent.SEARCH_ACCUSED: [r"\baccused\b", r"\bsuspect\b", r"\bcriminal\b", r"named\s+\w+"],
    Intent.SEARCH_VICTIMS: [r"\bvictims?\b", r"\binjured\b"],
    # BUG 2 FIX: REPORTS must score much higher than FIR_LOOKUP/SEARCH_CASES for
    # "generate report" / "investigation report" queries. Previously it only had one
    # general pattern \breport\b which tied with SEARCH_CASES crime patterns.
    Intent.REPORTS: [
        r"\bgenerate\s+report\b", r"\bgenerate\s+investigation\s+report\b",
        r"\bcreate\s+report\b", r"\bprepare\s+report\b", r"\bbuild\s+report\b",
        r"\bexport\s+report\b", r"\bdownload\s+report\b",
        r"\binvestigation\s+report\b", r"\bofficer\s+report\b",
        r"\breport\s+for\s+this\s+fir\b", r"\breport\s+for\s+this\s+case\b",
        r"\bcase\s+report\b", r"\bfir\s+report\b"
    ],
    Intent.FIR_LOOKUP: [r"\bfir\b", r"\bcase\b", r"\bcrime\s+(?:no\.?|number)\b", r"\bksp-\d{4,}\b"],
    Intent.REPEAT_OFFENDERS: [r"\brepeat\s+offender", r"\bhabitual\s+offender", r"\bserial\s+offender"],
    Intent.MOST_WANTED: [r"\bmost\s+wanted\b", r"\bhigh\s+risk\s+accused\b"],
}

# General patterns list
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
    r"\btrends?\b",
    r"\bstatistics\b",
    r"\bcrime\s+rate\b",
    r"\bcrime.*rate\b",
    r"\b(?:top|highest|most\s+common|frequent)\s+(?:crime\s+categories|crimes?|categories)\b",
    r"\bcrime\s+(?:distribution|breakdown|analysis|frequency)\b",
    r"\bhighest\s+crime\b",
    r"\bcrime\s+trend\b",
    r"\bcrime\s+categor(?:y|ies)\s+ranking\b",
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
    # BUG 2 FIX: Additional patterns for report generation queries
    r"\bgenerate\s+report\b",
    r"\bcreate\s+report\b",
    r"\bprepare\s+report\b",
    r"\binvestigation\s+report\b",
    r"\bofficer\s+report\b",
    r"\bcase\s+report\b",
    r"\bfir\s+report\b",
    r"\bexport\s+report\b",
]

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
    r"\bstolen\b",
    r"\bstealing\b",
    r"\bhomicide\b",
    r"\bkilled\b",
    r"\bkilling\b",
    r"\battack\b",
    r"\bbeating\b",
    r"\bfight\b",
    r"\bbattery\b",
    r"\brape\b",
    r"\babduct\b",
    r"\bkidnap\b",
    r"\babduction\b",
]

_VERBS = r"(show|open|display|search|find|get|fetch|retrieve|lookup|details\s+of)"
_PATTERNS_FIR_LOOKUP: List[str] = [
    r"\b" + _VERBS + r"\s+(?:fir|case|crime)\b",
    r"\bfir\b\s*(?:no\.?|number|id)?\s*[-#:]?\s*[a-z0-9][a-z0-9/-]*\b",
    r"\bcase\b\s*(?:no\.?|number|id)?\s*[-#:]?\s*[a-z0-9][a-z0-9/-]*\b",
    r"\bcrime\b\s+(?:no\.?|number)\s*[-#:]?\s*[a-z0-9][a-z0-9/-]*\b",
    r"\b(?:ksp|cr|fir)-\d{2,}\b",
]

_PATTERNS_REPEAT_OFFENDERS: List[str] = [
    r"\brepeat\s+offenders?\b",
    r"\bhabitual\s+offenders?\b",
    r"\bserial\s+offenders?\b",
    r"\brecidivist\b"
]

_PATTERNS_MOST_WANTED: List[str] = [
    r"\bmost\s+wanted\b",
    r"\bhigh\s+risk\s+accused\b",
    r"\btop\s+criminals?\b",
    r"\bmost\s+dangerous\b"
]

_PATTERN_MAP: Dict[Intent, List[str]] = OrderedDict([
    (Intent.FIR_LOOKUP,      _PATTERNS_FIR_LOOKUP),
    (Intent.PREDICT_CRIME,   _PATTERNS_PREDICT),
    (Intent.REPEAT_OFFENDERS, _PATTERNS_REPEAT_OFFENDERS),
    (Intent.MOST_WANTED,      _PATTERNS_MOST_WANTED),
    (Intent.AGGREGATE_COUNT, _PATTERNS_AGGREGATE),
    (Intent.CRIME_TREND,     _PATTERNS_TREND),
    (Intent.HOTSPOT,         _PATTERNS_HOTSPOT),
    (Intent.SEARCH_ACCUSED,  _PATTERNS_ACCUSED),
    (Intent.SEARCH_VICTIMS,  _PATTERNS_VICTIMS),
    (Intent.REPORTS,         _PATTERNS_REPORTS),
    (Intent.SEARCH_CASES,    _PATTERNS_SEARCH_CASES),
])

_COMPILED: Dict[Intent, re.Pattern] = {
    intent: re.compile("|".join(pats), re.IGNORECASE)
    for intent, pats in _PATTERN_MAP.items()
}


def predict_intent(text: str) -> Intent:
    """Predict the intent using semantic scoring based on regex triggers."""
    text_lower = text.lower()
    scores: Dict[Intent, float] = {intent: 0.0 for intent in Intent}

    # Apply strong trigger weights
    for intent, patterns in _STRONG_TRIGGERS.items():
        for p in patterns:
            if re.search(p, text_lower):
                scores[intent] += 10.0

    # Apply general pattern weights
    for intent, pattern_list in _PATTERN_MAP.items():
        for p in pattern_list:
            if re.search(p, text_lower):
                scores[intent] += 1.0
                
    # Select highest scoring intent
    best_intent = max(scores, key=scores.get)
    if scores[best_intent] > 0:
        return best_intent

    return Intent.SEARCH_CASES


def classify_intent_with_confidence(text: str) -> Tuple[Optional[Intent], float]:
    """Classify user query intent and estimate confidence score (0.0 to 1.0)."""
    lowered = text.lower().strip()
    if not lowered:
        return None, 0.0

    scores: Dict[Intent, float] = {intent: 0.0 for intent in Intent}

    # 1. Apply strong trigger weights
    for intent, patterns in _STRONG_TRIGGERS.items():
        for p in patterns:
            if re.search(p, lowered):
                scores[intent] += 0.8

    # 2. Apply general pattern weights
    for intent, pattern_list in _PATTERN_MAP.items():
        for p in pattern_list:
            if re.search(p, lowered):
                scores[intent] += 0.4
                
    # Extra points for action verbs if generic
    if re.search(r"\b(show|list|find|get|search)\b", lowered):
        scores[Intent.SEARCH_CASES] += 0.2

    best_intent = max(scores, key=scores.get)
    best_score = scores[best_intent]

    if best_score == 0:
        return Intent.SEARCH_CASES, 0.40
        
    confidence = min(0.95, best_score)
    
    words = lowered.split()
    if len(words) <= 1:
        confidence = max(0.40, confidence - 0.20)
    elif len(words) >= 4:
        confidence = min(1.0, confidence + 0.10)
        
    return best_intent, round(confidence, 2)


def classify_intent(text: str) -> Optional[Intent]:
    """Backward compatible classify_intent returns the Intent or None."""
    intent, _ = classify_intent_with_confidence(text)
    return intent
