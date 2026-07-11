import datetime
from typing import List, Dict, Any, Tuple, Set

class SimilarityEngine:
    """
    Production-grade O(n) similarity ranking engine.
    Calculates weighted overlap between a target FIR and candidate FIRs.
    """
    
    # Configurable weights (Total = 100)
    WEIGHTS = {
        "crime_type": 20,
        "police_station": 10,
        "district": 5,
        "accused": 15,
        "victim": 10,
        "mo_keywords": 20,
        "time_window": 20
    }

    _STOP_WORDS = {
        "the", "a", "an", "and", "or", "but", "is", "are", "was", "were", 
        "in", "on", "at", "to", "for", "of", "with", "by", "from", "that", 
        "this", "it", "he", "she", "they", "their", "his", "her", "who", "which",
        "accused", "victim", "police", "station", "complainant", "case", "fir",
        "registered", "unknown", "person", "incident", "crime", "report", "reported"
    }

    @classmethod
    def _extract_keywords(cls, text: str) -> Set[str]:
        if not text or not isinstance(text, str):
            return set()
        words = [w.strip(".,;:!?()[]{}\"'").lower() for w in text.split()]
        return {w for w in words if len(w) > 3 and w not in cls._STOP_WORDS and not w.isdigit()}

    @classmethod
    def _parse_date(cls, dt_val: Any) -> datetime.datetime:
        if not dt_val:
            return None
        if isinstance(dt_val, datetime.datetime):
            return dt_val
        if isinstance(dt_val, datetime.date):
            return datetime.datetime.combine(dt_val, datetime.time.min)
        if isinstance(dt_val, str):
            try:
                if "T" in dt_val:
                    return datetime.datetime.fromisoformat(dt_val.replace("Z", "+00:00")).replace(tzinfo=None)
                elif " " in dt_val:
                    return datetime.datetime.strptime(dt_val, "%Y-%m-%d %H:%M:%S")
                else:
                    return datetime.datetime.strptime(dt_val, "%Y-%m-%d")
            except ValueError:
                pass
        return None

    @classmethod
    def _time_distance_score(cls, dt1: datetime.datetime, dt2: datetime.datetime) -> float:
        if not dt1 or not dt2:
            return 0.0
        
        diff_days = abs((dt1 - dt2).days)
        if diff_days <= 1:
            return 1.0
        elif diff_days <= 7:
            return 0.8
        elif diff_days <= 30:
            return 0.5
        elif diff_days <= 180:
            return 0.2
        return 0.0

    @classmethod
    def calculate_similarity(cls, target_features: Dict[str, Any], candidate: Dict[str, Any]) -> Tuple[int, List[str]]:
        score = 0.0
        explanations = []
        
        # 1. Crime Type (20%)
        t_crime = target_features.get("crime_type")
        c_crime = candidate.get("crime_group_name") or candidate.get("crime_head_name")
        if t_crime and c_crime and t_crime.lower() == c_crime.lower():
            score += cls.WEIGHTS["crime_type"]
            explanations.append("Same Crime Type")
            
        # 2. Police Station (10%)
        t_ps = target_features.get("police_station")
        c_ps = candidate.get("police_station_name")
        if t_ps and c_ps and t_ps.lower() == c_ps.lower():
            score += cls.WEIGHTS["police_station"]
            explanations.append("Same Police Station")
            
        # 3. District (5%)
        t_dist = target_features.get("district")
        c_dist = candidate.get("district_name")
        if t_dist and c_dist and t_dist.lower() == c_dist.lower():
            score += cls.WEIGHTS["district"]
            explanations.append("Same District")
            
        # 4. Accused (15%)
        t_accused = target_features.get("accused_set", set())
        c_accused = cls._extract_keywords(candidate.get("accused_name", ""))
        if t_accused and c_accused:
            overlap = len(t_accused.intersection(c_accused))
            if overlap > 0:
                score += cls.WEIGHTS["accused"]
                explanations.append("Same Accused Involved")
                
        # 5. Victim (10%)
        t_victim = target_features.get("victim_set", set())
        c_victim = cls._extract_keywords(candidate.get("victim_name", ""))
        if t_victim and c_victim:
            overlap = len(t_victim.intersection(c_victim))
            if overlap > 0:
                score += cls.WEIGHTS["victim"]
                explanations.append("Same Victim Involved")
                
        # 6. MO Keywords (20%)
        t_mo = target_features.get("mo_keywords", set())
        c_mo = cls._extract_keywords(candidate.get("brief_facts", ""))
        if t_mo and c_mo:
            overlap = len(t_mo.intersection(c_mo))
            if overlap >= 3:
                score += cls.WEIGHTS["mo_keywords"]
                explanations.append("Highly similar Modus Operandi")
            elif overlap >= 1:
                score += (cls.WEIGHTS["mo_keywords"] * 0.5)
                explanations.append("Similar Modus Operandi keywords")
                
        # 7. Time Window (20%)
        t_time = target_features.get("time")
        c_time = cls._parse_date(candidate.get("crime_registered_date") or candidate.get("incident_from_date"))
        if t_time and c_time:
            t_score = cls._time_distance_score(t_time, c_time)
            if t_score > 0:
                score += (cls.WEIGHTS["time_window"] * t_score)
                if t_score == 1.0:
                    explanations.append("Occurred on the same day")
                elif t_score == 0.8:
                    explanations.append("Occurred within a week")
                elif t_score == 0.5:
                    explanations.append("Occurred within a month")
                    
        return int(score), explanations

    @classmethod
    def find_top_similar(cls, target_fir: Dict[str, Any], pool: List[Dict[str, Any]], limit: int = 5) -> List[Tuple[Dict[str, Any], int, str]]:
        if not target_fir or not pool:
            return []
            
        target_id = str(target_fir.get("fir_no", "")) + str(target_fir.get("crime_no", ""))
        
        # Pre-compute target features once to ensure O(n) performance
        target_features = {
            "crime_type": target_fir.get("crime_group_name") or target_fir.get("crime_head_name"),
            "police_station": target_fir.get("police_station_name"),
            "district": target_fir.get("district_name"),
            "accused_set": cls._extract_keywords(target_fir.get("accused_name", "")),
            "victim_set": cls._extract_keywords(target_fir.get("victim_name", "")),
            "mo_keywords": cls._extract_keywords(target_fir.get("brief_facts", "")),
            "time": cls._parse_date(target_fir.get("crime_registered_date") or target_fir.get("incident_from_date"))
        }
        
        scored_candidates = []
        seen_ids = {target_id} # Exclude self
        
        for candidate in pool:
            c_id = str(candidate.get("fir_no", "")) + str(candidate.get("crime_no", ""))
            if not c_id or c_id in seen_ids:
                continue
                
            seen_ids.add(c_id)
            score, explanations = cls.calculate_similarity(target_features, candidate)
            
            if score > 0:
                explanation_str = f"**{score}% Similar:** " + ", ".join(explanations)
                scored_candidates.append((candidate, score, explanation_str))
                
        # Sort descending by score
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        return scored_candidates[:limit]
