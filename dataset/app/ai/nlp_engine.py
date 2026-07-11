import re
import unicodedata
from typing import Dict, Any, Optional, Tuple

class NLPEngine:
    """
    Unified production-grade hybrid NLP engine for police query understanding.
    Handles casing, spacing, unicode variants, Hinglish/mixed language translation,
    typo correction, alias resolution, entity extraction, query rewriting, and multi-intent detection.
    """

    # Karnataka Districts for Levenshtein comparison
    KARNATAKA_DISTRICTS = [
        "Bagalkote", "Ballari", "Belagavi", "Bengaluru Rural", "Bengaluru Urban", "Bidar",
        "Chamarajanagar", "Chikkaballapur", "Chikkamagaluru", "Chitradurga", "Dakshina Kannada",
        "Davanagere", "Dharwad", "Gadag", "Hassan", "Haveri", "Kalaburagi", "Kodagu",
        "Kolar", "Koppal", "Mandya", "Mysuru", "Raichur", "Ramanagara", "Shivamogga",
        "Tumakuru", "Udupi", "Uttara Kannada", "Vijayapura", "Yadgir", "Vijayanagara"
    ]

    # Colloquial variations mapped to canonical district names
    DISTRICT_COLLOQUIAL_MAP = {
        # Bengaluru variants
        "bangalore": "Bengaluru Urban",
        "banglore": "Bengaluru Urban",
        "bengaluru": "Bengaluru Urban",
        "bengalru": "Bengaluru Urban",
        "bnglore": "Bengaluru Urban",
        "blr": "Bengaluru Urban",
        # Mysuru variants
        "mysore": "Mysuru",
        "mysur": "Mysuru",
        "mysr": "Mysuru",
        # Belagavi variants
        "belgaum": "Belagavi",
        "belgavi": "Belagavi",
        # Dakshina Kannada (Mangaluru) variants
        "mangalore": "Dakshina Kannada",
        "mangaluru": "Dakshina Kannada",
        "manglore": "Dakshina Kannada",
        "mangalru": "Dakshina Kannada",
        "mangalor": "Dakshina Kannada",
        # Dharwad (Hubli) variants
        "hubli": "Dharwad",
        "hubbali": "Dharwad",
        "hubballi": "Dharwad",
        # Kodagu (Coorg) variants
        "coorg": "Kodagu",
        # Kalaburagi (Gulbarga) variants
        "gulbarga": "Kalaburagi",
        # Tumakuru variants
        "tumkur": "Tumakuru",
        # Shivamogga variants
        "shimoga": "Shivamogga",
        "shivamoga": "Shivamogga",
        # Davanagere variants
        "davangere": "Davanagere",
        # Ramanagara variants
        "ramnagar": "Ramanagara",
        # Chamarajanagar variants
        "chamarajnagar": "Chamarajanagar",
        # Gadag variants
        "gadaga": "Gadag",
        # Haveri variants
        "haverii": "Haveri",
        # Yadgir variants
        "yadgiri": "Yadgir",
        # Koppal variants
        "koppala": "Koppal",
        # Kolar variants
        "kolara": "Kolar",
        # Bagalkote variants
        "bagalkot": "Bagalkote",
        # Udupi variants
        "udupii": "Udupi",
        # Bidar variants
        "bidara": "Bidar",
        # Raichur variants
        "raichurr": "Raichur",
        # Mandya variants
        "mandyaa": "Mandya",
        # Hassan variants
        "hasan": "Hassan",
    }

    # Hinglish to English translation map
    HINGLISH_TRANSLATION_MAP = {
        "hatya": "murder",
        "maar diya": "murder",
        "khoon": "murder",
        "chori": "theft",
        "chori ke": "theft",
        "loot": "robbery",
        "lootpaat": "robbery",
        "balatkar": "rape",
        "kidnap": "kidnapping",
        "apaharan": "kidnapping",
        "thana": "police station",
        "chowky": "police station",
        "chowki": "police station",
        "dhara": "section",
        "kanoon": "act"
    }

    # Canonical crime categories
    CRIME_CATEGORIES = ["theft", "murder", "assault", "rape", "kidnapping", "cheating", "dacoity", "robbery", "burglary", "homicide"]

    @classmethod
    def normalize_query(cls, query: str) -> str:
        """
        1. Query Normalizer: Standardization of spacing, casing, unicode and common abbreviations.
        NOTE: This must be called AFTER resolve_aliases so alias markers aren't stripped.
        """
        if not query:
            return ""

        # Normalize unicode variants (NFKD decomposition)
        cleaned = "".join(c for c in unicodedata.normalize('NFKD', query) if not unicodedata.combining(c))

        # Casing
        cleaned = cleaned.lower()

        # Handle police abbreviations BEFORE stripping punctuation
        cleaned = re.sub(r"\bps\b", "police station", cleaned)
        cleaned = re.sub(r"\bno\.?\b", "number", cleaned)

        # Hinglish Translation
        for hinglish, english in cls.HINGLISH_TRANSLATION_MAP.items():
            cleaned = re.sub(rf"\b{hinglish}\b", english, cleaned)

        # Standardize spacing & strip punctuation except for hyphens/slashes
        cleaned = re.sub(r"\s+", " ", cleaned)
        cleaned = re.sub(r"[^\w\s\-\/]", "", cleaned)
        cleaned = cleaned.strip()

        # Typo correction on matching known entities
        cleaned = cls.correct_typos(cleaned)

        return cleaned

    # Words that introduce a proper name — the NEXT word is a name and must not be typo-corrected
    NAME_INTRODUCERS = {"accused", "victim", "named", "offender", "criminal", "suspect", "person"}

    @classmethod
    def correct_typos(cls, query: str) -> str:
        """
        3. Typo Corrector: Uses edit distance to match misspelled districts and crimes.
        - Words < 4 chars are skipped to prevent false positives.
        - District colloquial map is checked first (exact key match).
        - Levenshtein against single-word canonical districts for <=2 edits.
        - Crime typos: words >= 4 chars with <=2 edits.
        - Words following name-introducing tokens ('accused', 'victim', etc.) are protected.
        """
        words = query.split()
        corrected_words = []
        skip_next = False  # True when the next word is a proper name

        for i, word in enumerate(words):
            # If previous word was a name introducer, this word is a name — skip correction
            if skip_next:
                corrected_words.append(word)
                skip_next = False
                continue

            # If this word introduces a name, flag the next word
            if word in cls.NAME_INTRODUCERS:
                corrected_words.append(word)
                skip_next = True
                continue

            # Skip very short words to prevent mis-correction
            if len(word) < 4:
                corrected_words.append(word)
                continue

            # Check district colloquial mappings first (comprehensive exact map)
            if word in cls.DISTRICT_COLLOQUIAL_MAP:
                corrected_words.append(cls.DISTRICT_COLLOQUIAL_MAP[word].lower())
                continue

            # Run Levenshtein against SINGLE-WORD canonical districts only
            # (multi-word like 'Bengaluru Urban' are handled by colloquial map above)
            single_word_districts = [
                d for d in cls.KARNATAKA_DISTRICTS if " " not in d
            ]
            best_district = word
            min_dist_dist = 999
            for dist in single_word_districts:
                dist_low = dist.lower()
                d = cls.levenshtein_distance(word, dist_low)
                if d < min_dist_dist:
                    min_dist_dist = d
                    best_district = dist_low

            if min_dist_dist <= 2 and len(word) >= 5:
                corrected_words.append(best_district)
                continue

            # Run Levenshtein against crime types (words >= 4 chars)
            best_crime = word
            min_dist_crime = 999
            for crime in cls.CRIME_CATEGORIES:
                d = cls.levenshtein_distance(word, crime)
                if d < min_dist_crime:
                    min_dist_crime = d
                    best_crime = crime

            if min_dist_crime <= 2 and len(word) >= 4:
                corrected_words.append(best_crime)
                continue

            corrected_words.append(word)

        return " ".join(corrected_words)

    @classmethod
    def levenshtein_distance(cls, s1: str, s2: str) -> int:
        """Standard Levenshtein distance computation."""
        if len(s1) < len(s2):
            return cls.levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

    @classmethod
    def resolve_aliases(cls, raw_query: str) -> Tuple[str, Optional[str], Optional[str]]:
        """
        4. Alias Resolver: Maps patterns like "Raju alias Raj", "Raju @ Raj", "Raju a.k.a Raj"
        to (modified_query, name, alias). Must be called on the ORIGINAL query before normalization.
        Never hallucinates aliases.
        """
        # Patterns to match: 'alias', '@', 'a.k.a', 'aka'
        alias_patterns = [
            r"\b([A-Za-z0-9]+)\s+alias\s+([A-Za-z0-9]+)\b",
            r"\b([A-Za-z0-9]+)\s*@\s*([A-Za-z0-9]+)\b",
            r"\b([A-Za-z0-9]+)\s+a\.k\.a\.?\s+([A-Za-z0-9]+)\b",
            r"\b([A-Za-z0-9]+)\s+aka\s+([A-Za-z0-9]+)\b",
        ]

        query = raw_query
        for pattern in alias_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                name = match.group(1).lower()
                alias = match.group(2).lower()
                # Remove the alias portion so downstream extractors see only the primary name
                rewritten = re.sub(pattern, match.group(1), query, flags=re.IGNORECASE)
                return rewritten, name, alias

        return query, None, None

    @classmethod
    def process_query(cls, query: str, db_session: Optional[Any] = None) -> Dict[str, Any]:
        """
        Unified processor implementing all NLP Engine specifications.
        Processing order:
          1. Alias resolution on RAW query (before normalization strips markers)
          2. Normalization + Hinglish + Typo correction on the alias-stripped query
          3. Entity extraction
          4. Intent routing
          5. Confidence scoring
          6. Query rewrite
        """
        warnings = []
        original_query = query

        # 1. Alias resolution FIRST on raw query so @, a.k.a, alias markers are intact
        alias_stripped_query, name, alias = cls.resolve_aliases(query)

        # 2. Normalization (Hinglish + Typo correction) on alias-stripped query
        normalized = cls.normalize_query(alias_stripped_query)

        # 3. Multi-Intent Check
        is_multi_intent = cls.detect_multi_intent(normalized)
        if is_multi_intent:
            warnings.append("Multi-intent query detected.")

        # 4. Extract entities via delegating to EntityExtractor or using custom rules
        from app.ai.entity_extractor import EntityExtractor
        raw_ext = EntityExtractor.extract_all(normalized, db_session)

        # Inject resolved alias details
        if name:
            raw_ext["accused_name"] = name
            raw_ext["alias"] = alias

        # 5. Intent Routing prediction
        from app.ai.intent_router import IntentRouter
        intent_result = IntentRouter.detect(normalized)
        intent = intent_result.intent or "UNKNOWN"
        intent_confidence = intent_result.confidence

        # 6. Confidence calculation
        confidence_score = cls.calculate_confidence(normalized, intent, raw_ext, intent_confidence)

        # 7. Query Rewrite
        canonical_rewrite = cls.rewrite_query(intent, raw_ext)

        return {
            "normalized_query": normalized,
            "entities": raw_ext,
            "intent_candidates": [{
                "intent": intent,
                "confidence": intent_confidence
            }],
            "confidence": confidence_score,
            "canonical_rewrite": canonical_rewrite,
            "is_multi_intent": is_multi_intent,
            "warnings": warnings
        }

    @classmethod
    def calculate_confidence(cls, normalized: str, intent: str, entities: Dict[str, Any], router_conf: float) -> float:
        """
        6. Confidence Calculator: Evaluates keyword strength, parsing status, and metadata structure.
        """
        score = router_conf * 100.0

        # Adjust score based on parsing indicators
        has_district = bool(entities.get("district") or entities.get("raw_district"))
        has_crime = bool(entities.get("crime_type"))
        
        # High penalty for general unknown intents
        if intent == "UNKNOWN":
            score = min(score, 30.0)

        # Boost score if specific entity matches exist
        if intent == "SEARCH_CASES" and has_district and has_crime:
            score = max(score, 90.0)

        # Demote score if query contains multiple confusing triggers
        if len(re.findall(r"\b(show|predict|trend|hotspot)\b", normalized)) > 1:
            score = min(score, 50.0)

        return min(100.0, max(0.0, score))

    @classmethod
    def rewrite_query(cls, intent: str, entities: Dict[str, Any]) -> str:
        """
        7. Query Rewriter: Converts extracted state to canonical text representation.
        """
        parts = [f"INTENT={intent}"]
        
        for k, v in entities.items():
            if v and k in ["district", "crime_type", "accused_name", "police_station"]:
                parts.append(f"{k}={v}")
                
        return " ".join(parts)

    @classmethod
    def detect_multi_intent(cls, normalized: str) -> bool:
        """
        8. Multi Intent Detection
        """
        # Checks if query contains sequential verbs/action commands separated by conjunctions
        conjunctions = [r"\band\b", r"\bas\s+well\s+as\b", r"\balso\b"]
        verbs = [r"\bshow\b", r"\bfind\b", r"\bpredict\b", r"\btrend\b", r"\bhotspot\b"]
        
        has_conjunction = any(re.search(pat, normalized) for pat in conjunctions)
        has_multiple_verbs = len(re.findall(r"\b(show|predict|trend|hotspot|identify|list)\b", normalized)) > 1
        
        return has_conjunction and has_multiple_verbs
