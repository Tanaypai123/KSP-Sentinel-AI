"""Production-grade Entity Extraction module for natural language queries.

Handles crime aliases, fuzzy district matching, relative and flexible date parsing,
limits, sorting order, age brackets, gender mapping, and validation.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

try:
    import rapidfuzz
except ImportError:
    rapidfuzz = None

# Comprehensive list of Karnataka districts used for fuzzy matching fallback
_KARNATAKA_DISTRICTS = [
    "Bengaluru Urban",
    "Bengaluru Rural",
    "Mysuru",
    "Mangalore",
    "Hubli",
    "Belgaum",
    "Mandya",
    "Shivamogga",
    "Tumakuru",
    "Udupi",
    "Kolar",
    "Hassan",
    "Ballari",
    "Chikkamagaluru",
    "Dharwad",
    "Bagalkot",
    "Bidar",
    "Chamarajanagar",
    "Chikkaballapur",
    "Chitradurga",
    "Davangere",
    "Gadag",
    "Haveri",
    "Kodagu",
    "Koppal",
    "Raichur",
    "Ramanagara",
    "Uttara Kannada",
    "Yadgir",
    "Vijayanagara",
    "Vijayapura",
    "Kalaburagi"
]

# Crime Head Aliases
_CRIME_ALIASES = {
    "theft": ["theft", "stolen", "stealing", "robbery", "bike theft", "vehicle theft", "chain snatching", "burglary", "larceny", "dacoity"],
    "assault": ["attack", "beating", "fight", "assault", "battery"],
    "murder": ["homicide", "killed", "murder", "killing"],
    "rape": ["rape", "sexual assault"],
    "kidnapping": ["abduct", "kidnapping", "missing child", "abduction"],
    "fraud": ["fraud", "cheating"],
}


class EntityExtractor:
    """Extracts structured entities from user natural language queries."""

    @staticmethod
    def extract_all(query: str, db_session: Optional[Any] = None) -> Dict[str, Any]:
        """Process the query string and return a dictionary of all extracted entities."""
        lowered = query.lower()

        # 1. Crime Type / Head
        crime_type = EntityExtractor.parse_crime_type(lowered)

        # 2. District with fuzzy matching and invalid district verification
        district, raw_district, is_valid_district, suggestions = EntityExtractor.parse_district(lowered, db_session)

        # 3. Police Station
        police_station = EntityExtractor.parse_police_station(lowered)

        # 4. Names
        accused_name = EntityExtractor.parse_name(lowered, r"\baccused\s*(?:named)?\s*([a-z]+(?:\s+[a-z]+)*)")
        victim_name = EntityExtractor.parse_name(lowered, r"\bvictim\s*(?:named)?\s*([a-z]+(?:\s+[a-z]+)*)")

        # 5. Gender
        gender = EntityExtractor.parse_gender(lowered)

        # 6. Age filters
        age_lt, age_gt, age_eq = EntityExtractor.parse_age(lowered)

        # 7. Status
        status = EntityExtractor.parse_status(lowered)

        # 8. Limit
        limit = EntityExtractor.parse_limit(lowered)

        # 9. Sorting
        sort = EntityExtractor.parse_sort(lowered)

        # 10. Date parsing (Relative & Flexible)
        date_from, date_to = EntityExtractor.parse_dates(lowered)

        # 11. Comparison operators (for trends & forecasting)
        comparison = EntityExtractor.parse_comparison(lowered)

        # 12. Prediction target indicator
        prediction = EntityExtractor.parse_prediction_indicator(lowered)

        return {
            "crime_type": crime_type,
            "district": district,
            "raw_district": raw_district,
            "is_valid_district": is_valid_district,
            "district_suggestions": suggestions,
            "police_station": police_station,
            "accused_name": accused_name,
            "victim_name": victim_name,
            "gender": gender,
            "age_lt": age_lt,
            "age_gt": age_gt,
            "age_eq": age_eq,
            "status": status,
            "limit": limit,
            "sort": sort,
            "date_from": date_from,
            "date_to": date_to,
            "comparison": comparison,
            "prediction": prediction
        }

    @staticmethod
    def parse_crime_type(text: str) -> Optional[str]:
        """Detect crime type based on alias dictionary."""
        # 1. Flatten and sort by length descending
        all_aliases = []
        for canonical, aliases in _CRIME_ALIASES.items():
            for alias in aliases:
                all_aliases.append((alias, canonical))
        all_aliases.sort(key=lambda x: len(x[0]), reverse=True)

        # 2. Try exact regex word boundary match
        for alias, canonical in all_aliases:
            if re.search(r"\b" + re.escape(alias) + r"\b", text):
                return canonical

        # 3. Try fuzzy matching on each word in the query string
        words = re.findall(r"\b\w+\b", text)
        if rapidfuzz:
            for word in words:
                for alias, canonical in all_aliases:
                    if rapidfuzz.fuzz.ratio(word, alias) >= 80.0:
                        return canonical

        return None

    @staticmethod
    def parse_district(text: str, db_session: Optional[Any] = None) -> Tuple[Optional[str], Optional[str], bool, List[str]]:
        """Extract and fuzzy match district name.

        Returns (matched_name, raw_extracted_name, is_valid, list_of_suggestions).
        """
        # Match pattern "in/from <district>"
        pattern = r"(?:in|from|at)\s+([a-z]+(?:\s+[a-z]+)*)\b"
        matches = re.finditer(pattern, text)
        raw_dist = None
        for m in matches:
            val = m.group(1).strip()
            # Stop words filter to ensure temporal words are not matched
            if val not in ["next", "last", "this", "month", "week", "year", "police", "accused", "victim", "cases", "theft", "murder", "assault"]:
                raw_dist = val
                break

        if not raw_dist:
            return None, None, True, []

        # Get candidates (query database if session provided, else fallback to Karnataka list)
        candidates = []
        if db_session:
            try:
                from app.models.masters import District
                rows = db_session.query(District.district_name).all()
                candidates = [r[0] for r in rows if r[0]]
            except Exception:
                pass
        if not candidates:
            candidates = _KARNATAKA_DISTRICTS

        # Map to friendly names
        candidate_map = {c.lower(): c for c in candidates}
        # Include custom maps
        candidate_map.update({
            "bangalore": "Bengaluru Urban",
            "bangaluru": "Bengaluru Urban",
            "mysore": "Mysuru",
            "mangalore": "Mangalore",
            "mangaluru": "Mangalore",
            "belgaum": "Belgaum",
            "belagavi": "Belgaum",
            "hubli": "Hubli",
            "hubballi": "Hubli",
            "coorg": "Kodagu"
        })

        query_term = raw_dist.lower().strip()

        # Direct map check
        if query_term in candidate_map:
            return candidate_map[query_term], raw_dist, True, []

        # Fuzzy Matching with RapidFuzz
        if rapidfuzz:
            keys = list(candidate_map.keys())
            res = rapidfuzz.process.extractOne(query_term, keys, score_cutoff=80.0)
            if res:
                matched_key = res[0]
                return candidate_map[matched_key], raw_dist, True, []

            # If confidence < 80%, construct suggestions
            scores = rapidfuzz.process.extract(query_term, list(candidate_map.values()), limit=3)
            suggestions = [s[0] for s in scores]
            return None, raw_dist, False, suggestions

        # Fallback without rapidfuzz
        for c_key, c_val in candidate_map.items():
            if query_term in c_key or c_key in query_term:
                return c_val, raw_dist, True, []

        # Return invalid with default suggestions
        default_suggestions = ["Mysuru", "Bengaluru Urban", "Mangalore"]
        return None, raw_dist, False, default_suggestions

    @staticmethod
    def parse_police_station(text: str) -> Optional[str]:
        """Extract police station name patterns."""
        match = re.search(r"(?:in|from|at)\s+([a-z]+(?:\s+[a-z]+)*)\s+police\s+station", text)
        return match.group(1).strip() if match else None

    @staticmethod
    def parse_name(text: str, regex_pattern: str) -> Optional[str]:
        """Extract a name using regex pattern."""
        match = re.search(regex_pattern, text)
        if match:
            name = match.group(1).strip()
            # Exclude grammar terms
            if name not in ["named", "under", "above"]:
                return name
        return None

    @staticmethod
    def parse_gender(text: str) -> Optional[str]:
        """Extract gender from text."""
        if re.search(r"\b(female|women|girls?)\b", text):
            return "female"
        if re.search(r"\b(male|men|boys?)\b", text):
            return "male"
        return None

    @staticmethod
    def parse_age(text: str) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        """Extract age comparison filters (lt, gt, eq) and validate constraints within [1, 120]."""
        # under 18 / below 18 / minor
        if re.search(r"\bminors?\b", text):
            return 18, None, None
        match_lt = re.search(r"(?:under|below|less\s+than)\s+(\d+)", text)
        if match_lt:
            val = int(match_lt.group(1))
            return max(1, min(val, 120)), None, None

        # above 50 / older than 40 / adult
        match_gt = re.search(r"(?:above|older\s+than|greater\s+than|over)\s+(\d+)", text)
        if match_gt:
            val = int(match_gt.group(1))
            return None, max(1, min(val, 120)), None
        if re.search(r"\badults?\b", text):
            return None, 18, None

        # exact age
        match_eq = re.search(r"(?:age|aged)\s+(\d+)", text)
        if match_eq:
            val = int(match_eq.group(1))
            return None, None, max(1, min(val, 120))

        return None, None, None

    @staticmethod
    def parse_status(text: str) -> Optional[str]:
        """Extract case status flags."""
        statuses = ["closed", "under trial", "investigation", "disposed", "charge sheet", "pending"]
        for st in statuses:
            if re.search(r"\b" + re.escape(st) + r"\b", text):
                return st
        return None

    @staticmethod
    def parse_limit(text: str) -> Optional[int]:
        """Extract numeric limits (top 5, latest 10, etc.) clamped to [1, 100]."""
        match = re.search(r"\b(?:top|latest|first|last|limit)\s+(\d+)\b", text)
        if match:
            val = int(match.group(1))
            return max(1, min(val, 100))
        return None

    @staticmethod
    def parse_sort(text: str) -> Optional[str]:
        """Extract sorting order."""
        if re.search(r"\b(latest|newest|recent|descending|desc)\b", text):
            return "desc"
        if re.search(r"\b(oldest|ascending|asc)\b", text):
            return "asc"
        return None

    @staticmethod
    def parse_dates(text: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse relative and flexible date boundaries.

        Returns (date_from, date_to) as ISO strings.
        """
        today = date.today()

        # --- A. Relative Dates ---
        if re.search(r"\btoday\b", text):
            return today.isoformat(), today.isoformat()
        if re.search(r"\byesterday\b", text):
            yest = today - timedelta(days=1)
            return yest.isoformat(), yest.isoformat()
        if re.search(r"\blast\s+week\b", text):
            return (today - timedelta(days=7)).isoformat(), today.isoformat()
        if re.search(r"\blast\s+month\b", text):
            return (today - timedelta(days=30)).isoformat(), today.isoformat()
        if re.search(r"\bthis\s+month\b", text):
            start = date(today.year, today.month, 1)
            return start.isoformat(), today.isoformat()
        if re.search(r"\blast\s+year\b", text):
            return date(today.year - 1, 1, 1).isoformat(), date(today.year - 1, 12, 31).isoformat()
        if re.search(r"\blast\s+30\s+days\b", text):
            return (today - timedelta(days=30)).isoformat(), today.isoformat()

        # --- B. Flexible Dates ---
        # 1. between Jan and March (current or previous year context)
        months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
        months_full = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
        
        between_match = re.search(r"between\s+(\w+)\s+and\s+(\w+)(?:\s+(\d{4}))?", text)
        if between_match:
            m1, m2 = between_match.group(1)[:3].lower(), between_match.group(2)[:3].lower()
            yr = int(between_match.group(3)) if between_match.group(3) else today.year
            if m1 in months and m2 in months:
                idx1 = months.index(m1) + 1
                idx2 = months.index(m2) + 1
                return date(yr, idx1, 1).isoformat(), date(yr, idx2, 28).isoformat()

        # 2. after Jan 2026 / after 2025
        after_match = re.search(r"after\s+(\w+)?\s*(\d{4})", text)
        if after_match:
            m_str = after_match.group(1)
            yr = int(after_match.group(2))
            if m_str and m_str[:3].lower() in months:
                idx = months.index(m_str[:3].lower()) + 1
                return date(yr, idx, 1).isoformat(), None
            return date(yr, 12, 31).isoformat(), None

        # 3. before June 2024 / before 2024
        before_match = re.search(r"before\s+(\w+)?\s*(\d{4})", text)
        if before_match:
            m_str = before_match.group(1)
            yr = int(before_match.group(2))
            if m_str and m_str[:3].lower() in months:
                idx = months.index(m_str[:3].lower()) + 1
                return None, date(yr, idx, 1).isoformat()
            return None, date(yr, 1, 1).isoformat()

        # 4. before June (implicit current year)
        before_month_only = re.search(r"before\s+([a-z]+)\b", text)
        if before_month_only:
            m_str = before_month_only.group(1)[:3].lower()
            if m_str in months:
                idx = months.index(m_str) + 1
                return None, date(today.year, idx, 1).isoformat()

        return None, None

    @staticmethod
    def parse_comparison(text: str) -> Optional[str]:
        """Detect comparison verbs for trends."""
        if re.search(r"\b(increase|growth|upward|more)\b", text):
            return "increase"
        if re.search(r"\b(decrease|decline|downward|less|fewer)\b", text):
            return "decrease"
        return None

    @staticmethod
    def parse_prediction_indicator(text: str) -> Optional[str]:
        """Detect prediction indicators."""
        if re.search(r"\b(predict|prediction|forecast|future|next\s+month|next\s+year)\b", text):
            return "prediction"
        return None
