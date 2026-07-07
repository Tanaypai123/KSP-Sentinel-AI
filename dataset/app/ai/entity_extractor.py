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
    "Bagalkote",
    "Ballari",
    "Belagavi",
    "Bengaluru Rural",
    "Bengaluru Urban",
    "Bidar",
    "Chamarajanagar",
    "Chikkaballapur",
    "Chikkamagaluru",
    "Chitradurga",
    "Dakshina Kannada",
    "Davanagere",
    "Dharwad",
    "Gadag",
    "Hassan",
    "Haveri",
    "Kalaburagi",
    "Kodagu",
    "Kolar",
    "Koppal",
    "Mandya",
    "Mysuru",
    "Raichur",
    "Ramanagara",
    "Shivamogga",
    "Tumakuru",
    "Udupi",
    "Uttara Kannada",
    "Vijayapura",
    "Yadgir",
    "Vijayanagara"
]

# Crime Head Aliases
_CRIME_ALIASES = {
    "theft": ["theft", "stolen", "stealing", "pickpocket"],
    "robbery": ["robbery", "armed robbery", "loot", "looting"],
    "burglary": ["burglary", "housebreaking", "breaking and entering"],
    "snatching": ["snatching", "chain snatching", "bag snatching"],
    "dacoity": ["dacoity", "armed dacoity", "gang robbery"],
    "assault": ["attack", "beating", "fight", "assault", "battery"],
    "murder": ["homicide", "killed", "murder", "killing"],
    "rape": ["rape", "sexual assault"],
    "kidnapping": ["abduct", "kidnapping", "missing child", "abduction", "kidnap"],
    "fraud": ["fraud", "cheating", "scam", "online fraud", "cyber fraud"],
    "cyber_crime": ["cyber crime", "online scam", "cyber fraud", "internet crime", "hacking", "phishing"],
    "narcotics": ["drugs", "narcotics", "weed", "cocaine", "smuggling", "drug offence"],
    "domestic_violence": ["domestic violence", "dowry", "wife beating", "cruelty by husband"],
    "traffic": ["traffic", "accident", "hit and run", "rash driving"],
    "missing_person": ["missing person", "lost person"],
    "vehicle_theft": ["vehicle theft", "bike theft", "car theft"],
    "rioting": ["rioting", "mob", "protest violence"],
    "extortion": ["extortion", "blackmail"],
    "arson": ["arson", "burning", "fire"]
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
        accused_name = EntityExtractor.parse_name(lowered, r"\baccused\s*(?:named)?\s+([a-z0-9]+(?:\s+[a-z0-9]+)*)")
        victim_name = EntityExtractor.parse_name(lowered, r"\bvictim\s*(?:named)?\s+([a-z0-9]+(?:\s+[a-z0-9]+)*)")

        # 5. Gender
        gender = EntityExtractor.parse_gender(lowered)

        # 6. Generic Numeric Filters
        numeric_filters = EntityExtractor.parse_numeric_filters(lowered)

        # 7. Status
        status = EntityExtractor.parse_status(lowered)

        # 8. Limit
        limit = EntityExtractor.parse_limit(lowered)

        # 9. Sorting
        sort = EntityExtractor.parse_sort(lowered)

        # 10. Date parsing
        date_from, date_to = EntityExtractor.parse_dates(lowered)

        # 11. Comparison operators
        comparison = EntityExtractor.parse_comparison(lowered)

        # 12. Prediction target
        prediction = EntityExtractor.parse_prediction_indicator(lowered)
        
        # 13. Generic Identifier (FIR/Case)
        identifiers = EntityExtractor.parse_identifier(lowered)

        # 14. Acts and Sections
        act = EntityExtractor.parse_act(lowered)
        section = EntityExtractor.parse_section(lowered)

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
            "numeric_filters": numeric_filters,
            "status": status,
            "limit": limit,
            "sort": sort,
            "date_from": date_from,
            "date_to": date_to,
            "comparison": comparison,
            "prediction": prediction,
            "identifiers": identifiers,
            "act": act,
            "section": section
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
        else:
            # Combine DB candidates with canonical districts to ensure valid districts are always recognized
            candidates = list(set(candidates + _KARNATAKA_DISTRICTS))

        # Map to friendly names
        candidate_map = {c.lower(): c for c in candidates}
        # Include custom maps
        candidate_map.update({
            "bangalore": "Bengaluru Urban",
            "banglore": "Bengaluru Urban",
            "bengaluru": "Bengaluru Urban",
            "mysore": "Mysuru",
            "mangalore": "Dakshina Kannada",
            "mangaluru": "Dakshina Kannada",
            "belgaum": "Belagavi",
            "gulbarga": "Kalaburagi",
            "shimoga": "Shivamogga",
            "tumkur": "Tumakuru",
            "bijapur": "Vijayapura",
            "hubli": "Dharwad",
            "hubballi": "Dharwad",
            "coorg": "Kodagu"
        })

        # Match pattern "in/from/at/location/near/of <district>" or exact match anywhere
        stop_words = ["next", "last", "this", "month", "week", "year", "police", "accused", "victim", "cases", "theft", "murder", "assault", "offender", "offenders", "criminal", "criminals", "most", "wanted"]
        
        raw_dist = None
        all_known = list(candidate_map.keys())
        all_known.sort(key=len, reverse=True)
        
        for k in all_known:
            if re.search(r"\b" + re.escape(k) + r"\b", text):
                raw_dist = k
                break
                
        if not raw_dist:
            pattern = r"(?:in|from|at|near|of|district)\s+([a-z]+(?:\s+[a-z]+)*)\b"
            matches = re.finditer(pattern, text)
            for m in matches:
                val = m.group(1).strip()
                if val not in stop_words:
                    raw_dist = val
                    break

        if not raw_dist:
            return None, None, True, []

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
            # Stop name at common grammatical boundaries
            name = re.split(r"\b(in|at|from|with|who|under|above|for|and|or|having)\b", name)[0].strip()
            # Exclude grammar terms
            if name and name not in ["named", "under", "above", "with"]:
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
    def parse_numeric_filters(text: str) -> List[Dict[str, Any]]:
        """Extract generic numeric filters mapping attributes to operators and values."""
        filters = []
        op_patterns = {
            "gte": r"(?:>=)",
            "lte": r"(?:<=)",
            "gt":  r"(?:>|above|older\s+than|greater\s+than|over|more\s+than)",
            "lt":  r"(?:<|under|below|less\s+than|younger\s+than)",
            "eq":  r"(?:==|=|exact|exactly|aged?)"
        }
        
        attr_patterns = {
            "age": r"\b(?:age|years?\s+old)\b",
            "cases": r"\b(?:cases?|firs?|crimes?)\b"
        }
        
        for attr, attr_pat in attr_patterns.items():
            for op, op_pat in op_patterns.items():
                # Formats: attr > val OR op val attr
                p1 = attr_pat + r"\s*" + op_pat + r"\s*(\d+)"
                p2 = op_pat + r"\s*(\d+)\s*" + attr_pat
                
                for p in [p1, p2]:
                    for m in re.finditer(p, text):
                        filters.append({"attribute": attr, "operator": op, "value": int(m.group(1))})
                        
        # Implicit attribute fallback
        for op, op_pat in op_patterns.items():
            for m in re.finditer(op_pat + r"\s*(\d+)", text):
                val = int(m.group(1))
                if not any(f["value"] == val for f in filters):
                    match_str = m.group(0)
                    if "older" in match_str or "younger" in match_str or val < 100:
                        # Assuming age for small numbers without explicit context if operator makes sense
                        if "older" in match_str or "younger" in match_str or re.search(r"\baged?\s+\d+", text):
                            filters.append({"attribute": "age", "operator": op, "value": val})
                        elif "more" in match_str or "less" in match_str:
                            filters.append({"attribute": "cases", "operator": op, "value": val})

        # Explicit minor/adult checks
        if re.search(r"\bminors?\b", text) and not any(f["attribute"] == "age" for f in filters):
            filters.append({"attribute": "age", "operator": "lt", "value": 18})
        if re.search(r"\badults?\b", text) and not any(f["attribute"] == "age" for f in filters):
            filters.append({"attribute": "age", "operator": "gte", "value": 18})
            
        return filters

    @staticmethod
    def parse_identifier(text: str) -> Optional[List[str]]:
        """Normalize generic FIR/Crime identifiers into an array of search candidates."""
        # Match explicit prefixes (FIR No, Case Number, etc.) followed by an identifier
        match = re.search(r"\b(?:fir|case|crime)\s+(?:no\.?|number|id)?\s*[-#:]?\s*([A-Z0-9]+[-\s/][A-Z0-9]+|\d+)\b", text, re.IGNORECASE)
        if match:
            raw = match.group(1)
        else:
            # Fallback to matching standalone common patterns:
            # 1. KSP-123, KSP 123, or KSP123
            # 2. 123/2026
            # 3. 000123 (pure numeric but could be ID, we will grab the first standalone 4+ digit number or slashed string)
            match = re.search(r"\b([A-Z]{2,5}[-\s]?\d+|\d+/\d+|\d{4,})\b", text, re.IGNORECASE)
            if match:
                raw = match.group(1)
            else:
                return None
                
        # Normalize raw string: remove spaces
        raw = re.sub(r"\s+", "", raw)
                
        # Parse into a canonical list of variants
        variants = []
        raw_upper = raw.upper()
        variants.append(raw_upper)
        
        # Check for strict formats like KSP-0001 or KSP0001
        m_prefix = re.match(r"([A-Z]+)[-]?(0*)(\d+)", raw_upper)
        if m_prefix:
            prefix, zeros, num = m_prefix.groups()
            variants.extend([
                f"{prefix}-{zeros}{num}",
                f"{prefix}{zeros}{num}",
                f"{prefix}-{num}",
                f"{prefix}{num}",
                f"{prefix}-{num.zfill(4)}",
                f"{prefix}-{num.zfill(6)}"
            ])
            
        # Check for slashes (e.g. 120/2026)
        if "/" in raw_upper:
            variants.append(raw_upper.replace("/", "-"))
        elif "-" in raw_upper and re.match(r"\d+-\d+", raw_upper):
            variants.append(raw_upper.replace("-", "/"))
            
        # Ensure we always include the pure numeric part if applicable
        num_match = re.search(r"\b(\d+)\b", raw_upper)
        if num_match:
            pure_num = num_match.group(1)
            variants.append(pure_num)
            variants.append(f"KSP-{pure_num.zfill(4)}")
            variants.append(f"KSP-{pure_num.zfill(6)}")

        # Return unique list
        return list(set(variants))

    @staticmethod
    def parse_act(text: str) -> Optional[str]:
        """Extract act name (e.g., IPC, NDPS)."""
        match = re.search(r"act\s*[:\-]?\s*([a-z]+)", text, re.IGNORECASE)
        return match.group(1) if match else None

    @staticmethod
    def parse_section(text: str) -> Optional[str]:
        """Extract section number (e.g., 302, 379)."""
        match = re.search(r"section\s*[:\-]?\s*([a-z0-9]+)", text, re.IGNORECASE)
        return match.group(1) if match else None

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
