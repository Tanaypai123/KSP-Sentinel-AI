"""
case_similarity_engine.py
Phase 5.7 — Enterprise Case Similarity & Investigation Recommendation Engine

Deterministic, weighted feature-matching similarity engine.
Finds verified similar investigations and produces priority-ranked recommendations.

STRICT RULES:
- NO cosine similarity
- NO embeddings
- NO sentence transformers
- NO OpenAI / external APIs
- NO guessed or hallucinated recommendations
- Similarity computed ONLY from verified database-sourced attributes
- If score < MINIMUM_THRESHOLD → "No verified similar investigation found."
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

MINIMUM_THRESHOLD: int = 20          # Minimum raw score required for a valid match
NO_MATCH_MESSAGE: str = "No verified similar investigation found."
MAX_TOP_RESULTS: int = 10            # Maximum similar FIRs returned in a SimilarityReport

# ─────────────────────────────────────────────────────────────────────────────
# FEATURE ENUM
# ─────────────────────────────────────────────────────────────────────────────

class CaseFeature(str, Enum):
    CRIME_TYPE           = "crime_type"
    DISTRICT             = "district"
    POLICE_STATION       = "police_station"
    ACCUSED              = "accused"
    VICTIM               = "victim"
    VEHICLE              = "vehicle"
    WEAPON               = "weapon"
    PHONE                = "phone"
    ORGANIZATION         = "organization"
    GANG                 = "gang"
    CRIME_PATTERN        = "crime_pattern"
    TIMELINE_PATTERN     = "timeline_pattern"
    KNOWLEDGE_GRAPH_LINK = "knowledge_graph_link"
    REPEAT_OFFENDER      = "repeat_offender"
    HOTSPOT              = "hotspot"
    MODUS_OPERANDI       = "modus_operandi"
    RECOVERY_PATTERN     = "recovery_pattern"
    INVESTIGATION_DURATION = "investigation_duration"

# ─────────────────────────────────────────────────────────────────────────────
# SCORING WEIGHTS  (raw integer; max raw = sum of all weights = 310)
# ─────────────────────────────────────────────────────────────────────────────

FEATURE_WEIGHTS: Dict[CaseFeature, int] = {
    CaseFeature.CRIME_TYPE:             30,
    CaseFeature.DISTRICT:               15,
    CaseFeature.POLICE_STATION:         10,
    CaseFeature.ACCUSED:                50,
    CaseFeature.VICTIM:                 20,
    CaseFeature.VEHICLE:                40,
    CaseFeature.WEAPON:                 35,
    CaseFeature.PHONE:                  35,
    CaseFeature.ORGANIZATION:           15,
    CaseFeature.GANG:                   20,
    CaseFeature.CRIME_PATTERN:          30,
    CaseFeature.TIMELINE_PATTERN:       20,
    CaseFeature.KNOWLEDGE_GRAPH_LINK:   25,
    CaseFeature.REPEAT_OFFENDER:        20,
    CaseFeature.HOTSPOT:                10,
    CaseFeature.MODUS_OPERANDI:         25,
    CaseFeature.RECOVERY_PATTERN:       15,
    CaseFeature.INVESTIGATION_DURATION: 15,
}

# Pre-computed maximum possible raw score for normalization
_MAX_RAW_SCORE: int = sum(FEATURE_WEIGHTS.values())   # 430


# ─────────────────────────────────────────────────────────────────────────────
# DATA STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CaseRecord:
    """
    A verified investigation record extracted from database search results.
    All fields come directly from the database — nothing is inferred.
    """
    crime_no: str
    district: str = ""
    police_station: str = ""
    crime_type: str = ""
    accused_names: List[str] = field(default_factory=list)
    victim_names: List[str] = field(default_factory=list)
    vehicle_nos: List[str] = field(default_factory=list)
    weapons: List[str] = field(default_factory=list)
    phones: List[str] = field(default_factory=list)
    organizations: List[str] = field(default_factory=list)
    gang_names: List[str] = field(default_factory=list)
    crime_pattern: str = ""
    modus_operandi: str = ""
    recovery_pattern: str = ""
    hotspot: str = ""
    repeat_offender: bool = False
    investigation_duration_days: Optional[int] = None
    knowledge_graph_node_ids: List[str] = field(default_factory=list)
    timeline_event_types: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, row: Dict[str, Any]) -> "CaseRecord":
        """
        Build a CaseRecord from a raw search_result dictionary.
        Only reads fields that are directly present in the row — no inference.
        """

        def _as_str(val: Any) -> str:
            return str(val).strip().lower() if val else ""

        def _as_list(val: Any) -> List[str]:
            if isinstance(val, list):
                return [str(v).strip().lower() for v in val if v]
            if isinstance(val, str) and val.strip():
                return [v.strip().lower() for v in val.split(",") if v.strip()]
            return []

        accused_raw = row.get("accused_name") or row.get("accused_names") or []
        victim_raw  = row.get("victim_name")  or row.get("victim_names")  or []
        vehicle_raw = (
            row.get("vehicle_no") or row.get("vehicle_nos") or
            row.get("vehicle_number") or []
        )
        weapon_raw  = row.get("weapon") or row.get("weapons") or row.get("crime_weapon") or []
        phone_raw   = (
            row.get("phone") or row.get("phones") or
            row.get("accused_mobile") or row.get("mobile_number") or []
        )
        org_raw  = row.get("organization") or row.get("organizations") or []
        gang_raw = row.get("gang_name") or row.get("gang_names") or []

        # Duration in days from timeline_report if present
        duration_days: Optional[int] = None
        timeline = row.get("_timeline_report") or {}
        if isinstance(timeline, dict):
            for ds in timeline.get("duration_stats", []):
                if isinstance(ds, dict) and ds.get("duration_days") is not None:
                    try:
                        duration_days = int(ds["duration_days"])
                    except (ValueError, TypeError):
                        pass
                    break

        # Knowledge graph node IDs from _knowledge_graph_report if present
        kg_nodes: List[str] = []
        kg_report = row.get("_knowledge_graph_report") or {}
        if isinstance(kg_report, dict):
            for n in kg_report.get("nodes", []):
                if isinstance(n, dict) and n.get("node_id"):
                    kg_nodes.append(str(n["node_id"]).lower())

        # Timeline event types from _timeline_report if present
        tl_events: List[str] = []
        if isinstance(timeline, dict):
            for ev in timeline.get("events", []):
                if isinstance(ev, dict) and ev.get("event_type"):
                    tl_events.append(str(ev["event_type"]).lower())

        repeat_flag = bool(
            row.get("repeat_offender") or
            row.get("is_repeat_offender") or
            row.get("linked_firs")
        )

        return cls(
            crime_no            = _as_str(row.get("crime_no") or row.get("fir_no") or "UNKNOWN"),
            district            = _as_str(row.get("district_name") or row.get("district")),
            police_station      = _as_str(row.get("police_station_name") or row.get("police_station")),
            crime_type          = _as_str(row.get("crime_head") or row.get("crime_type") or row.get("crime_category")),
            accused_names       = _as_list(accused_raw),
            victim_names        = _as_list(victim_raw),
            vehicle_nos         = _as_list(vehicle_raw),
            weapons             = _as_list(weapon_raw),
            phones              = _as_list(phone_raw),
            organizations       = _as_list(org_raw),
            gang_names          = _as_list(gang_raw),
            crime_pattern       = _as_str(row.get("crime_pattern") or row.get("pattern")),
            modus_operandi      = _as_str(row.get("modus_operandi") or row.get("mo")),
            recovery_pattern    = _as_str(row.get("recovery_pattern")),
            hotspot             = _as_str(row.get("hotspot") or row.get("hotspot_area")),
            repeat_offender     = repeat_flag,
            investigation_duration_days = duration_days,
            knowledge_graph_node_ids    = kg_nodes,
            timeline_event_types        = list(dict.fromkeys(tl_events)),  # deduplicated, ordered
        )


@dataclass
class FeatureMatch:
    """Result of comparing a single feature between two cases."""
    feature: CaseFeature
    base_value: Any
    candidate_value: Any
    matched: bool
    weight: int
    score_awarded: int
    evidence: str        # Human-readable justification


@dataclass
class SimilarityScore:
    """
    Deterministic similarity result for one candidate FIR vs. the base FIR.
    Normalized 0–100.
    """
    base_crime_no: str
    candidate_crime_no: str
    raw_score: int
    normalized_score: int           # 0–100
    matching_features: List[FeatureMatch] = field(default_factory=list)
    differing_features: List[CaseFeature] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_crime_no": self.base_crime_no,
            "candidate_crime_no": self.candidate_crime_no,
            "raw_score": self.raw_score,
            "normalized_score": self.normalized_score,
            "matching_features": [
                {
                    "feature": m.feature.value,
                    "base_value": m.base_value,
                    "candidate_value": m.candidate_value,
                    "score_awarded": m.score_awarded,
                    "evidence": m.evidence,
                }
                for m in self.matching_features
            ],
            "differing_features": [f.value for f in self.differing_features],
            "warnings": self.warnings,
        }


@dataclass
class Recommendation:
    """
    A single deterministic investigation recommendation.
    Priority must be HIGH / MEDIUM / LOW.
    Every recommendation is backed by explicit evidence.
    """
    recommendation_id: str
    priority: str                   # "HIGH" | "MEDIUM" | "LOW"
    recommendation_type: str        # e.g. "Similar FIRs", "Repeat Offender Detection"
    description: str
    reason: str
    evidence: List[str]
    supporting_firs: List[str]
    confidence: float               # 0.0 – 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "priority": self.priority,
            "recommendation_type": self.recommendation_type,
            "description": self.description,
            "reason": self.reason,
            "evidence": self.evidence,
            "supporting_firs": self.supporting_firs,
            "confidence": round(self.confidence, 3),
        }


@dataclass
class SimilarityReport:
    """
    Full output document for the Case Similarity Engine.
    """
    base_crime_no: str
    top_similar_firs: List[SimilarityScore] = field(default_factory=list)
    recommendations: List[Recommendation] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    evidence_chain: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_crime_no": self.base_crime_no,
            "top_similar_firs": [s.to_dict() for s in self.top_similar_firs],
            "recommendations": [r.to_dict() for r in self.recommendations],
            "warnings": self.warnings,
            "evidence_chain": self.evidence_chain,
        }


# ─────────────────────────────────────────────────────────────────────────────
# SIMILARITY CALCULATOR  (deterministic, no ML)
# ─────────────────────────────────────────────────────────────────────────────

class SimilarityCalculator:
    """
    Computes a deterministic weighted similarity score between two CaseRecords.

    Each feature check is a pure intersection / equality test over verified
    database values.  No fuzzy matching, no embeddings, no ML.
    """

    @staticmethod
    def _set_intersects(a: List[str], b: List[str]) -> bool:
        return bool(set(a) & set(b))

    @staticmethod
    def _set_overlap_evidence(label: str, a: List[str], b: List[str]) -> str:
        common = sorted(set(a) & set(b))
        return f"{label} match: {', '.join(common)}" if common else f"No {label.lower()} overlap"

    @classmethod
    def compute(cls, base: CaseRecord, candidate: CaseRecord) -> SimilarityScore:
        """
        Full deterministic comparison.  Returns a SimilarityScore.
        """
        raw_score: int = 0
        matching: List[FeatureMatch] = []
        differing: List[CaseFeature] = []
        warnings: List[str] = []

        def _check(
            feature: CaseFeature,
            matched: bool,
            base_val: Any,
            cand_val: Any,
            evidence: str,
        ) -> None:
            nonlocal raw_score
            weight = FEATURE_WEIGHTS[feature]
            awarded = weight if matched else 0
            raw_score += awarded
            fm = FeatureMatch(
                feature=feature,
                base_value=base_val,
                candidate_value=cand_val,
                matched=matched,
                weight=weight,
                score_awarded=awarded,
                evidence=evidence,
            )
            if matched:
                matching.append(fm)
            else:
                differing.append(feature)

        # ── 1. Crime Type ─────────────────────────────────────────────────────
        ct_match = bool(base.crime_type and candidate.crime_type and
                        base.crime_type == candidate.crime_type)
        _check(CaseFeature.CRIME_TYPE, ct_match,
               base.crime_type, candidate.crime_type,
               f"Crime type: '{base.crime_type}'" if ct_match else "Crime types differ")

        # ── 2. District ───────────────────────────────────────────────────────
        dist_match = bool(base.district and candidate.district and
                          base.district == candidate.district)
        _check(CaseFeature.DISTRICT, dist_match,
               base.district, candidate.district,
               f"Same district: {base.district}" if dist_match else "Different districts")

        # ── 3. Police Station ─────────────────────────────────────────────────
        ps_match = bool(base.police_station and candidate.police_station and
                        base.police_station == candidate.police_station)
        _check(CaseFeature.POLICE_STATION, ps_match,
               base.police_station, candidate.police_station,
               f"Same station: {base.police_station}" if ps_match else "Different stations")

        # ── 4. Accused ────────────────────────────────────────────────────────
        acc_match = cls._set_intersects(base.accused_names, candidate.accused_names)
        _check(CaseFeature.ACCUSED, acc_match,
               base.accused_names, candidate.accused_names,
               cls._set_overlap_evidence("Accused", base.accused_names, candidate.accused_names))

        # ── 5. Victim ─────────────────────────────────────────────────────────
        vic_match = cls._set_intersects(base.victim_names, candidate.victim_names)
        _check(CaseFeature.VICTIM, vic_match,
               base.victim_names, candidate.victim_names,
               cls._set_overlap_evidence("Victim", base.victim_names, candidate.victim_names))

        # ── 6. Vehicle ────────────────────────────────────────────────────────
        veh_match = cls._set_intersects(base.vehicle_nos, candidate.vehicle_nos)
        _check(CaseFeature.VEHICLE, veh_match,
               base.vehicle_nos, candidate.vehicle_nos,
               cls._set_overlap_evidence("Vehicle", base.vehicle_nos, candidate.vehicle_nos))

        # ── 7. Weapon ─────────────────────────────────────────────────────────
        wpn_match = cls._set_intersects(base.weapons, candidate.weapons)
        _check(CaseFeature.WEAPON, wpn_match,
               base.weapons, candidate.weapons,
               cls._set_overlap_evidence("Weapon", base.weapons, candidate.weapons))

        # ── 8. Phone ──────────────────────────────────────────────────────────
        ph_match = cls._set_intersects(base.phones, candidate.phones)
        _check(CaseFeature.PHONE, ph_match,
               base.phones, candidate.phones,
               cls._set_overlap_evidence("Phone", base.phones, candidate.phones))

        # ── 9. Organization ───────────────────────────────────────────────────
        org_match = cls._set_intersects(base.organizations, candidate.organizations)
        _check(CaseFeature.ORGANIZATION, org_match,
               base.organizations, candidate.organizations,
               cls._set_overlap_evidence("Organization", base.organizations, candidate.organizations))

        # ── 10. Gang ──────────────────────────────────────────────────────────
        gang_match = cls._set_intersects(base.gang_names, candidate.gang_names)
        _check(CaseFeature.GANG, gang_match,
               base.gang_names, candidate.gang_names,
               cls._set_overlap_evidence("Gang", base.gang_names, candidate.gang_names))

        # ── 11. Crime Pattern ─────────────────────────────────────────────────
        cp_match = bool(base.crime_pattern and candidate.crime_pattern and
                        base.crime_pattern == candidate.crime_pattern)
        _check(CaseFeature.CRIME_PATTERN, cp_match,
               base.crime_pattern, candidate.crime_pattern,
               f"Crime pattern match: '{base.crime_pattern}'" if cp_match else "Crime patterns differ")

        # ── 12. Timeline Pattern ──────────────────────────────────────────────
        base_tl_set = set(base.timeline_event_types)
        cand_tl_set = set(candidate.timeline_event_types)
        tl_common = base_tl_set & cand_tl_set
        tl_match = len(tl_common) >= 2   # Meaningful overlap requires ≥ 2 shared event types
        _check(CaseFeature.TIMELINE_PATTERN, tl_match,
               sorted(base_tl_set), sorted(cand_tl_set),
               f"Timeline overlap ({len(tl_common)} event types): {', '.join(sorted(tl_common))}"
               if tl_match else "Insufficient timeline event overlap")

        # ── 13. Knowledge Graph Links ─────────────────────────────────────────
        kg_match = cls._set_intersects(base.knowledge_graph_node_ids, candidate.knowledge_graph_node_ids)
        _check(CaseFeature.KNOWLEDGE_GRAPH_LINK, kg_match,
               base.knowledge_graph_node_ids, candidate.knowledge_graph_node_ids,
               cls._set_overlap_evidence("KG Node", base.knowledge_graph_node_ids,
                                          candidate.knowledge_graph_node_ids))

        # ── 14. Repeat Offender ───────────────────────────────────────────────
        ro_match = base.repeat_offender and candidate.repeat_offender
        _check(CaseFeature.REPEAT_OFFENDER, ro_match,
               base.repeat_offender, candidate.repeat_offender,
               "Both cases involve repeat offenders" if ro_match else "Repeat offender status differs")

        # ── 15. Hotspot ───────────────────────────────────────────────────────
        hs_match = bool(base.hotspot and candidate.hotspot and
                        base.hotspot == candidate.hotspot)
        _check(CaseFeature.HOTSPOT, hs_match,
               base.hotspot, candidate.hotspot,
               f"Same hotspot: {base.hotspot}" if hs_match else "Hotspot differs")

        # ── 16. Modus Operandi ────────────────────────────────────────────────
        mo_match = bool(base.modus_operandi and candidate.modus_operandi and
                        base.modus_operandi == candidate.modus_operandi)
        _check(CaseFeature.MODUS_OPERANDI, mo_match,
               base.modus_operandi, candidate.modus_operandi,
               f"MO match: '{base.modus_operandi}'" if mo_match else "MO differs")

        # ── 17. Recovery Pattern ──────────────────────────────────────────────
        rp_match = bool(base.recovery_pattern and candidate.recovery_pattern and
                        base.recovery_pattern == candidate.recovery_pattern)
        _check(CaseFeature.RECOVERY_PATTERN, rp_match,
               base.recovery_pattern, candidate.recovery_pattern,
               f"Recovery pattern match: '{base.recovery_pattern}'" if rp_match else "Recovery patterns differ")

        # ── 18. Investigation Duration ────────────────────────────────────────
        dur_match = False
        if base.investigation_duration_days is not None and candidate.investigation_duration_days is not None:
            # Similarity window: within ±30 days
            diff = abs(base.investigation_duration_days - candidate.investigation_duration_days)
            dur_match = diff <= 30
        dur_evidence = (
            f"Duration similar: {base.investigation_duration_days}d vs {candidate.investigation_duration_days}d"
            if dur_match
            else "Investigation duration differs or unavailable"
        )
        _check(CaseFeature.INVESTIGATION_DURATION, dur_match,
               base.investigation_duration_days, candidate.investigation_duration_days,
               dur_evidence)

        # Warn if the candidate is the same FIR
        if base.crime_no == candidate.crime_no:
            warnings.append(f"Candidate {candidate.crime_no} is identical to base FIR — skipped in ranking")

        # Normalise to 0–100
        normalized = round((raw_score / _MAX_RAW_SCORE) * 100) if _MAX_RAW_SCORE > 0 else 0
        normalized = max(0, min(100, normalized))

        return SimilarityScore(
            base_crime_no=base.crime_no,
            candidate_crime_no=candidate.crime_no,
            raw_score=raw_score,
            normalized_score=normalized,
            matching_features=matching,
            differing_features=differing,
            warnings=warnings,
        )


# ─────────────────────────────────────────────────────────────────────────────
# RECOMMENDATION GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

class RecommendationGenerator:
    """
    Produces deterministic, evidence-backed investigation recommendations
    from a ranked list of SimilarityScores and CaseRecords.

    Priority Rules (deterministic):
      HIGH   → normalised score ≥ 70
      MEDIUM → normalised score 40–69
      LOW    → normalised score 20–39
      SKIP   → score < MINIMUM_THRESHOLD  (20)
    """

    _rec_counter: int = 0

    @classmethod
    def _next_rec_id(cls) -> str:
        cls._rec_counter += 1
        return f"REC-{cls._rec_counter:05d}"

    @classmethod
    def _priority(cls, normalized_score: int) -> str:
        if normalized_score >= 70:
            return "HIGH"
        if normalized_score >= 40:
            return "MEDIUM"
        return "LOW"

    @classmethod
    def generate(
        cls,
        base: CaseRecord,
        scores: List[SimilarityScore],
        all_records: Dict[str, CaseRecord],
    ) -> List[Recommendation]:
        recs: List[Recommendation] = []

        above_threshold = [s for s in scores if s.normalized_score >= MINIMUM_THRESHOLD
                           and s.candidate_crime_no != base.crime_no]

        if not above_threshold:
            return recs   # Caller adds NO_MATCH_MESSAGE to warnings

        # ── 1. Similar FIRs ───────────────────────────────────────────────────
        fir_firs = [s.candidate_crime_no for s in above_threshold[:MAX_TOP_RESULTS]]
        if fir_firs:
            top = above_threshold[0]
            evidence = [m.evidence for m in top.matching_features]
            recs.append(Recommendation(
                recommendation_id   = cls._next_rec_id(),
                priority            = cls._priority(top.normalized_score),
                recommendation_type = "Similar FIRs",
                description = (
                    f"FIR {top.candidate_crime_no} has a similarity score of "
                    f"{top.normalized_score}/100 with FIR {base.crime_no}."
                ),
                reason    = "High feature overlap detected across verified database attributes.",
                evidence  = evidence[:5],
                supporting_firs = fir_firs[:5],
                confidence = round(top.normalized_score / 100, 3),
            ))

        # ── 2. Repeat Offender Detection ──────────────────────────────────────
        repeat_firs = [
            s.candidate_crime_no for s in above_threshold
            if any(m.feature == CaseFeature.ACCUSED for m in s.matching_features)
        ]
        if repeat_firs:
            recs.append(Recommendation(
                recommendation_id   = cls._next_rec_id(),
                priority            = "HIGH",
                recommendation_type = "Repeat Offender Detection",
                description = (
                    f"Accused in FIR {base.crime_no} appear in "
                    f"{len(repeat_firs)} other verified FIRs."
                ),
                reason    = "Same accused names found in multiple FIRs in database.",
                evidence  = [
                    f"Accused shared with FIR {fno}" for fno in repeat_firs[:5]
                ],
                supporting_firs = repeat_firs[:5],
                confidence = 0.95,
            ))

        # ── 3. Common Vehicles ────────────────────────────────────────────────
        vehicle_firs = [
            s.candidate_crime_no for s in above_threshold
            if any(m.feature == CaseFeature.VEHICLE for m in s.matching_features)
        ]
        if vehicle_firs:
            veh_evidence = []
            for s in above_threshold:
                for m in s.matching_features:
                    if m.feature == CaseFeature.VEHICLE:
                        veh_evidence.append(m.evidence)
            recs.append(Recommendation(
                recommendation_id   = cls._next_rec_id(),
                priority            = cls._priority(above_threshold[0].normalized_score),
                recommendation_type = "Common Vehicles",
                description = (
                    f"Vehicles linked to FIR {base.crime_no} reappear in "
                    f"{len(vehicle_firs)} other FIRs."
                ),
                reason    = "Same vehicle registration numbers appear in multiple FIR records.",
                evidence  = list(dict.fromkeys(veh_evidence))[:5],
                supporting_firs = vehicle_firs[:5],
                confidence = 0.90,
            ))

        # ── 4. Common Weapons ─────────────────────────────────────────────────
        weapon_firs = [
            s.candidate_crime_no for s in above_threshold
            if any(m.feature == CaseFeature.WEAPON for m in s.matching_features)
        ]
        if weapon_firs:
            wpn_evidence = []
            for s in above_threshold:
                for m in s.matching_features:
                    if m.feature == CaseFeature.WEAPON:
                        wpn_evidence.append(m.evidence)
            recs.append(Recommendation(
                recommendation_id   = cls._next_rec_id(),
                priority            = cls._priority(above_threshold[0].normalized_score),
                recommendation_type = "Common Weapons",
                description = (
                    f"Weapons recorded in FIR {base.crime_no} found in "
                    f"{len(weapon_firs)} other FIRs."
                ),
                reason    = "Same weapon types appear in verified FIR weapon fields.",
                evidence  = list(dict.fromkeys(wpn_evidence))[:5],
                supporting_firs = weapon_firs[:5],
                confidence = 0.88,
            ))

        # ── 5. Common Phones ──────────────────────────────────────────────────
        phone_firs = [
            s.candidate_crime_no for s in above_threshold
            if any(m.feature == CaseFeature.PHONE for m in s.matching_features)
        ]
        if phone_firs:
            ph_evidence = []
            for s in above_threshold:
                for m in s.matching_features:
                    if m.feature == CaseFeature.PHONE:
                        ph_evidence.append(m.evidence)
            recs.append(Recommendation(
                recommendation_id   = cls._next_rec_id(),
                priority            = "HIGH",
                recommendation_type = "Common Phones",
                description = (
                    f"Phone numbers linked to FIR {base.crime_no} reappear in "
                    f"{len(phone_firs)} other FIRs."
                ),
                reason    = "Same phone numbers recorded across multiple FIR accused/victim fields.",
                evidence  = list(dict.fromkeys(ph_evidence))[:5],
                supporting_firs = phone_firs[:5],
                confidence = 0.92,
            ))

        # ── 6. Common Districts ───────────────────────────────────────────────
        district_firs = [
            s.candidate_crime_no for s in above_threshold
            if any(m.feature == CaseFeature.DISTRICT for m in s.matching_features)
        ]
        if district_firs:
            recs.append(Recommendation(
                recommendation_id   = cls._next_rec_id(),
                priority            = "MEDIUM",
                recommendation_type = "Common Districts",
                description = (
                    f"FIR {base.crime_no} shares the same district with "
                    f"{len(district_firs)} other FIRs."
                ),
                reason    = "District name matches verified database district field.",
                evidence  = [f"District match: {base.district}"],
                supporting_firs = district_firs[:5],
                confidence = 0.75,
            ))

        # ── 7. Common Stations ────────────────────────────────────────────────
        station_firs = [
            s.candidate_crime_no for s in above_threshold
            if any(m.feature == CaseFeature.POLICE_STATION for m in s.matching_features)
        ]
        if station_firs:
            recs.append(Recommendation(
                recommendation_id   = cls._next_rec_id(),
                priority            = "LOW",
                recommendation_type = "Common Stations",
                description = (
                    f"FIR {base.crime_no} is from the same police station as "
                    f"{len(station_firs)} other similar FIRs."
                ),
                reason    = "Police station name matches database field across FIRs.",
                evidence  = [f"Station match: {base.police_station}"],
                supporting_firs = station_firs[:5],
                confidence = 0.70,
            ))

        # ── 8. Related Hotspots ───────────────────────────────────────────────
        hotspot_firs = [
            s.candidate_crime_no for s in above_threshold
            if any(m.feature == CaseFeature.HOTSPOT for m in s.matching_features)
        ]
        if hotspot_firs:
            recs.append(Recommendation(
                recommendation_id   = cls._next_rec_id(),
                priority            = "MEDIUM",
                recommendation_type = "Related Hotspots",
                description = (
                    f"FIR {base.crime_no} is located in the same crime hotspot as "
                    f"{len(hotspot_firs)} other FIRs."
                ),
                reason    = "Hotspot area field matches across multiple FIR records.",
                evidence  = [f"Hotspot: {base.hotspot}"],
                supporting_firs = hotspot_firs[:5],
                confidence = 0.72,
            ))

        # ── 9. Likely Associated FIRs (KG Links) ─────────────────────────────
        kg_firs = [
            s.candidate_crime_no for s in above_threshold
            if any(m.feature == CaseFeature.KNOWLEDGE_GRAPH_LINK for m in s.matching_features)
        ]
        if kg_firs:
            recs.append(Recommendation(
                recommendation_id   = cls._next_rec_id(),
                priority            = cls._priority(above_threshold[0].normalized_score),
                recommendation_type = "Likely Associated FIRs",
                description = (
                    f"Knowledge Graph analysis links FIR {base.crime_no} to "
                    f"{len(kg_firs)} other FIRs via shared graph nodes."
                ),
                reason    = "Shared knowledge graph node IDs from the verified KG engine.",
                evidence  = [f"Shared KG nodes with FIR {fno}" for fno in kg_firs[:3]],
                supporting_firs = kg_firs[:5],
                confidence = 0.85,
            ))

        # ── 10. Investigation Priority (overall) ──────────────────────────────
        if above_threshold:
            top_score = above_threshold[0].normalized_score
            all_supporting = [s.candidate_crime_no for s in above_threshold[:5]]
            steps: List[str] = []
            if repeat_firs:
                steps.append("Investigate shared accused across identified similar FIRs")
            if vehicle_firs:
                steps.append("Trace vehicles that appear in multiple FIRs")
            if weapon_firs:
                steps.append("Conduct weapons provenance analysis")
            if phone_firs:
                steps.append("Request CDR analysis for shared phone numbers")
            if kg_firs:
                steps.append("Expand knowledge graph investigation from shared nodes")
            if not steps:
                steps.append("Review similar FIRs for additional evidence leads")

            recs.append(Recommendation(
                recommendation_id   = cls._next_rec_id(),
                priority            = cls._priority(top_score),
                recommendation_type = "Investigation Priority",
                description = (
                    f"FIR {base.crime_no} has {len(above_threshold)} verified similar cases. "
                    f"Recommended next steps: {'; '.join(steps[:3])}."
                ),
                reason    = "Overall investigation priority derived from similarity analysis.",
                evidence  = [
                    f"Top similarity score: {top_score}/100",
                    f"Similar FIRs found: {len(above_threshold)}",
                    f"Unique recommendation types: {len(recs)}",
                ],
                supporting_firs = all_supporting,
                confidence = round(top_score / 100, 3),
            ))

        return recs


# ─────────────────────────────────────────────────────────────────────────────
# RECOMMENDATION VALIDATOR
# ─────────────────────────────────────────────────────────────────────────────

class RecommendationValidator:
    """
    Validates all Recommendations before they are included in a SimilarityReport.
    Ensures no hallucinations and that every recommendation is evidence-backed.
    """

    VALID_PRIORITIES = {"HIGH", "MEDIUM", "LOW"}

    @classmethod
    def validate(cls, recs: List[Recommendation]) -> Tuple[List[Recommendation], List[str]]:
        valid: List[Recommendation] = []
        warnings: List[str] = []

        for rec in recs:
            issues: List[str] = []

            if not rec.recommendation_id:
                issues.append("Missing recommendation_id")
            if rec.priority not in cls.VALID_PRIORITIES:
                issues.append(f"Invalid priority '{rec.priority}' — must be HIGH/MEDIUM/LOW")
            if not rec.description.strip():
                issues.append("Description is empty")
            if not rec.reason.strip():
                issues.append("Reason is empty")
            if not rec.evidence:
                issues.append("Evidence list is empty — recommendation is unverified")
            if not rec.supporting_firs:
                issues.append("No supporting FIRs — recommendation is unverified")
            if not (0.0 <= rec.confidence <= 1.0):
                issues.append(f"Confidence {rec.confidence} out of range [0,1]")

            if issues:
                warnings.extend([f"[{rec.recommendation_id}] {i}" for i in issues])
                logger.warning("Recommendation %s failed validation: %s",
                               rec.recommendation_id, issues)
            else:
                valid.append(rec)

        return valid, warnings


# ─────────────────────────────────────────────────────────────────────────────
# CASE SIMILARITY ENGINE  (main API)
# ─────────────────────────────────────────────────────────────────────────────

class CaseSimilarityEngine:
    """
    Main public API for Phase 5.7 Case Similarity.

    Usage (pipeline):
        report = CaseSimilarityEngine.find_similar_cases(context)

    The engine:
      1. Converts search_result rows → CaseRecords
      2. Uses the first record as the *base* FIR
      3. Computes SimilarityScore for every other record
      4. Filters and ranks by normalised score
      5. Generates and validates Recommendations
      6. Returns a complete SimilarityReport
    """

    @classmethod
    def find_similar_cases(cls, context: Any) -> SimilarityReport:
        """
        Entry point called by the pipeline stage.
        context.search_result must be a list of dicts.
        """
        results: List[Dict[str, Any]] = list(context.search_result or [])

        if not results:
            return SimilarityReport(
                base_crime_no = "UNKNOWN",
                warnings      = [NO_MATCH_MESSAGE],
                evidence_chain = ["No search results available for similarity analysis"],
            )

        # Convert rows → CaseRecords
        records: List[CaseRecord] = []
        for row in results:
            try:
                # Enrich row with timeline and KG context if available
                if hasattr(context, "timeline_report") and context.timeline_report:
                    row["_timeline_report"] = context.timeline_report
                if hasattr(context, "knowledge_graph_report") and context.knowledge_graph_report:
                    row["_knowledge_graph_report"] = context.knowledge_graph_report
                records.append(CaseRecord.from_dict(row))
            except Exception as e:
                logger.warning("Failed to build CaseRecord from row: %s", e)

        if not records:
            return SimilarityReport(
                base_crime_no = "UNKNOWN",
                warnings      = [NO_MATCH_MESSAGE, "All records failed CaseRecord construction"],
                evidence_chain = [],
            )

        base = records[0]
        candidates = records[1:]

        if not candidates:
            return SimilarityReport(
                base_crime_no  = base.crime_no,
                warnings       = [NO_MATCH_MESSAGE],
                evidence_chain = ["Only one record in result set — no candidates for comparison"],
            )

        # Score every candidate
        scores: List[SimilarityScore] = []
        for cand in candidates:
            if cand.crime_no == base.crime_no:
                continue   # Skip self-comparisons
            score = SimilarityCalculator.compute(base, cand)
            scores.append(score)

        # Sort descending by normalised_score, then by raw_score for tiebreak
        scores.sort(key=lambda s: (s.normalized_score, s.raw_score), reverse=True)

        # Filter to threshold
        valid_scores = [s for s in scores if s.normalized_score >= MINIMUM_THRESHOLD]

        all_warnings: List[str] = []
        top_similar  = valid_scores[:MAX_TOP_RESULTS]

        if not top_similar:
            all_warnings.append(NO_MATCH_MESSAGE)

        # Build record lookup for RecommendationGenerator
        record_map: Dict[str, CaseRecord] = {r.crime_no: r for r in records}

        # Generate recommendations
        recs = RecommendationGenerator.generate(base, valid_scores, record_map)
        validated_recs, val_warnings = RecommendationValidator.validate(recs)
        all_warnings.extend(val_warnings)

        # Collect all warnings from individual scores
        for s in scores:
            all_warnings.extend(s.warnings)

        evidence_chain = [
            "Similarity computed from verified database field values only",
            "No embeddings, cosine similarity, or ML used",
            "Scores normalised to 0–100 scale",
            f"Minimum threshold for valid match: {MINIMUM_THRESHOLD}",
            f"Base FIR: {base.crime_no}",
            f"Candidates evaluated: {len(candidates)}",
            f"Valid matches above threshold: {len(valid_scores)}",
        ]

        return SimilarityReport(
            base_crime_no   = base.crime_no,
            top_similar_firs = top_similar,
            recommendations  = validated_recs,
            warnings         = all_warnings,
            evidence_chain   = evidence_chain,
        )

    # ── Convenience operations ─────────────────────────────────────────────────

    @classmethod
    def merge_scores(cls, a: List[SimilarityScore], b: List[SimilarityScore]) -> List[SimilarityScore]:
        """Merge two score lists and re-rank."""
        combined = {s.candidate_crime_no: s for s in a}
        for s in b:
            if s.candidate_crime_no not in combined:
                combined[s.candidate_crime_no] = s
        merged = list(combined.values())
        merged.sort(key=lambda s: (s.normalized_score, s.raw_score), reverse=True)
        return merged

    @classmethod
    def find_common_feature(
        cls,
        feature: CaseFeature,
        scores: List[SimilarityScore],
    ) -> List[str]:
        """Return candidate crime numbers where the given feature matched."""
        return [
            s.candidate_crime_no for s in scores
            if any(m.feature == feature for m in s.matching_features)
        ]


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE STAGE WRAPPER
# ─────────────────────────────────────────────────────────────────────────────

class CaseSimilarityStage:
    """
    Pipeline stage wrapper for CaseSimilarityEngine.
    Inserted between TimelineStage and MultiAgentEngineStage.
    """

    @staticmethod
    def run(context: Any) -> Any:
        try:
            report = CaseSimilarityEngine.find_similar_cases(context)
            context.similarity_report = report.to_dict()
        except Exception as e:
            logger.error("CaseSimilarityStage failed: %s", e, exc_info=True)
            context.warnings.append(f"CaseSimilarityStage failed: {e}")
            context.similarity_report = {
                "base_crime_no": "UNKNOWN",
                "top_similar_firs": [],
                "recommendations": [],
                "warnings": [NO_MATCH_MESSAGE, str(e)],
                "evidence_chain": [],
            }
        return context
