"""Shared normalization layer for district and crime head inputs.

Ensures colloquial names and alternate spellings (e.g. Bangalore, Mysore,
burglary) match canonical database records.
"""

from __future__ import annotations

# Mappings of common spelling variations/aliases to canonical DB substrings.
_DISTRICT_MAP = {
    "bangalore": "bengaluru",
    "bangaluru": "bengaluru",
    "bengaluru": "bengaluru",
    "mysore": "mysuru",
    "mysuru": "mysuru",
    "mangalore": "mangalore",
    "mangaluru": "mangalore",
    "hubli": "hubli",
    "hubballi": "hubli",
    "belgaum": "belgaum",
    "belagavi": "belgaum",
    "gulbarga": "kalaburagi",
    "kalaburagi": "kalaburagi",
    "bijapur": "vijayapura",
    "vijayapura": "vijayapura",
    "shimoga": "shivamogga",
    "shivamogga": "shivamogga",
    "chikmagalur": "chikkamagaluru",
    "chikkamagaluru": "chikkamagaluru",
    "bellary": "ballari",
    "ballari": "ballari",
    "tumkur": "tumakuru",
    "tumakuru": "tumakuru",
    "dharwad": "dharwad",
    "gadag": "gadag",
    "haveri": "haveri",
    "bidar": "bidar",
    "raichur": "raichur",
    "koppal": "koppal",
    "bagalkot": "bagalkot",
    "kolar": "kolar",
    "chikkaballapur": "chikkaballapur",
    "ramanagara": "ramanagara",
    "mandya": "mandya",
    "hassan": "hassan",
    "kodagu": "kodagu",
    "coorg": "kodagu",
    "chamarajanagar": "chamarajanagar",
    "udupi": "udupi",
    "dakshina kannada": "mangalore",
    "uttara kannada": "uttara kannada",
    "karwar": "uttara kannada",
    "davangere": "davangere",
    "chitradurga": "chitradurga",
    "yadgir": "yadgir",
    "vijayanagara": "vijayanagara",
}

_CRIME_HEAD_MAP = {
    "burglary": "theft",
    "larceny": "theft",
    "robbery": "robbery",
    "theft": "theft",
    "murder": "murder",
    "homicide": "murder",
    "killing": "murder",
    "assault": "assault",
    "battery": "assault",
    "rape": "rape",
    "sexual assault": "rape",
    "kidnapping": "kidnapping",
    "abduction": "kidnapping",
    "fraud": "fraud",
    "cheating": "fraud",
    "dacoity": "robbery",
}

# Stopwords that are commonly extracted as crime heads by generic regex patterns
# but are actually part of the query grammar.
_CRIME_HEAD_STOPWORDS = {
    "many", "all", "any", "some", "the", "these", "those",
    "other", "show", "list", "find", "get", "view", "rate"
}


def normalize_district(name: str | None) -> str | None:
    """Normalize a district name/alias into the canonical DB search term."""
    if not name:
        return None
    val = name.lower().strip()
    return _DISTRICT_MAP.get(val, val)


def normalize_crime_head(name: str | None) -> str | None:
    """Normalize a crime type into the canonical DB group name search term.

    Discards common query stopwords to prevent false-positive filters.
    """
    if not name:
        return None
    val = name.lower().strip()
    if val in _CRIME_HEAD_STOPWORDS:
        return None
    return _CRIME_HEAD_MAP.get(val, val)
