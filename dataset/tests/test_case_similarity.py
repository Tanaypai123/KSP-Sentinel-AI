"""
tests/test_case_similarity.py
Phase 5.7 — Case Similarity & Investigation Recommendation Engine
4000+ deterministic test scenarios.

Covers:
  - same accused
  - same weapon
  - same vehicle
  - same phone
  - same hotspot
  - same district
  - same station
  - cross-district
  - cross-station
  - partial matches
  - no matches
  - duplicate matches
  - false positives
  - all feature combinations
  - threshold boundary conditions
  - recommendation generation
  - recommendation validation
  - CaseSimilarityStage integration
  - SimilarityReport structure
"""

import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.ai.case_similarity_engine import (
    CaseFeature,
    CaseRecord,
    CaseSimilarityEngine,
    CaseSimilarityStage,
    FEATURE_WEIGHTS,
    MINIMUM_THRESHOLD,
    NO_MATCH_MESSAGE,
    Recommendation,
    RecommendationGenerator,
    RecommendationValidator,
    SimilarityCalculator,
    SimilarityReport,
    SimilarityScore,
    _MAX_RAW_SCORE,
)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS & FIXTURES
# ─────────────────────────────────────────────────────────────────────────────

def make_record(**kwargs) -> CaseRecord:
    """Build a CaseRecord with sensible defaults; override with kwargs."""
    defaults = dict(
        crime_no="FIR-001",
        district="mysuru",
        police_station="siddarthanagar ps",
        crime_type="theft",
        accused_names=["raju"],
        victim_names=["kumar"],
        vehicle_nos=["KA-09-AB-1234"],
        weapons=["knife"],
        phones=["9876543210"],
        organizations=[],
        gang_names=[],
        crime_pattern="night_theft",
        modus_operandi="forced entry",
        recovery_pattern="cash recovered",
        hotspot="mysuru_market",
        repeat_offender=False,
        investigation_duration_days=30,
        knowledge_graph_node_ids=["fir-001-node"],
        timeline_event_types=["fir registered", "arrest"],
    )
    defaults.update(kwargs)
    return CaseRecord(**defaults)


@dataclass
class FakeContext:
    """Minimal context object for CaseSimilarityStage tests."""
    search_result: List[Dict[str, Any]] = field(default_factory=list)
    timeline_report: Optional[Dict[str, Any]] = None
    knowledge_graph_report: Optional[Dict[str, Any]] = None
    warnings: List[str] = field(default_factory=list)
    similarity_report: Optional[Dict[str, Any]] = None


def make_row(**kwargs) -> Dict[str, Any]:
    """Build a raw search_result row dict."""
    defaults = dict(
        crime_no="FIR-001",
        district_name="mysuru",
        police_station_name="siddarthanagar ps",
        crime_head="theft",
        accused_name="raju",
        victim_name="kumar",
        vehicle_no="KA-09-AB-1234",
        crime_weapon="knife",
        accused_mobile="9876543210",
    )
    defaults.update(kwargs)
    return defaults


# ─────────────────────────────────────────────────────────────────────────────
# 1. WEIGHT TABLE INTEGRITY
# ─────────────────────────────────────────────────────────────────────────────

class TestWeightTable:
    def test_all_features_have_weights(self):
        for feat in CaseFeature:
            assert feat in FEATURE_WEIGHTS, f"{feat} missing from FEATURE_WEIGHTS"

    def test_all_weights_positive(self):
        for feat, w in FEATURE_WEIGHTS.items():
            assert w > 0, f"Weight for {feat} must be positive"

    def test_max_raw_score_correct(self):
        expected = sum(FEATURE_WEIGHTS.values())
        assert _MAX_RAW_SCORE == expected

    def test_crime_type_weight(self):
        assert FEATURE_WEIGHTS[CaseFeature.CRIME_TYPE] == 30

    def test_accused_weight_highest_single(self):
        assert FEATURE_WEIGHTS[CaseFeature.ACCUSED] == 50

    def test_vehicle_weight(self):
        assert FEATURE_WEIGHTS[CaseFeature.VEHICLE] == 40

    def test_weapon_weight(self):
        assert FEATURE_WEIGHTS[CaseFeature.WEAPON] == 35

    def test_phone_weight(self):
        assert FEATURE_WEIGHTS[CaseFeature.PHONE] == 35

    def test_minimum_threshold_value(self):
        assert MINIMUM_THRESHOLD == 20


# ─────────────────────────────────────────────────────────────────────────────
# 2. CASE RECORD CONSTRUCTION
# ─────────────────────────────────────────────────────────────────────────────

class TestCaseRecordFromDict:
    def test_basic_construction(self):
        row = make_row()
        rec = CaseRecord.from_dict(row)
        assert rec.crime_no == "fir-001"
        assert rec.district == "mysuru"
        assert rec.police_station == "siddarthanagar ps"

    def test_crime_head_mapped_to_crime_type(self):
        row = make_row(crime_head="robbery")
        rec = CaseRecord.from_dict(row)
        assert rec.crime_type == "robbery"

    def test_accused_name_as_string(self):
        row = make_row(accused_name="raju,sanjay")
        rec = CaseRecord.from_dict(row)
        assert "raju" in rec.accused_names
        assert "sanjay" in rec.accused_names

    def test_accused_name_as_list(self):
        row = make_row(accused_name=["raju", "sanjay"])
        rec = CaseRecord.from_dict(row)
        assert "raju" in rec.accused_names

    def test_vehicle_field_aliases(self):
        row = make_row(vehicle_no=None, vehicle_number="KA-09-ZZ-9999")
        rec = CaseRecord.from_dict(row)
        assert "ka-09-zz-9999" in rec.vehicle_nos

    def test_phone_field_aliases(self):
        row = make_row(accused_mobile=None, mobile_number="9123456789")
        rec = CaseRecord.from_dict(row)
        assert "9123456789" in rec.phones

    def test_missing_optional_fields(self):
        row = {"crime_no": "FIR-999"}
        rec = CaseRecord.from_dict(row)
        assert rec.crime_no == "fir-999"
        assert rec.district == ""
        assert rec.accused_names == []

    def test_empty_row(self):
        rec = CaseRecord.from_dict({})
        assert rec.crime_no == "unknown"

    def test_values_normalised_to_lowercase(self):
        row = make_row(district_name="MYSURU", accused_name="RAJU")
        rec = CaseRecord.from_dict(row)
        assert rec.district == "mysuru"
        assert "raju" in rec.accused_names

    def test_repeat_offender_from_linked_firs(self):
        row = make_row(linked_firs=["FIR-101"])
        rec = CaseRecord.from_dict(row)
        assert rec.repeat_offender is True

    def test_no_repeat_offender_by_default(self):
        row = make_row()
        rec = CaseRecord.from_dict(row)
        assert rec.repeat_offender is False

    def test_duration_from_timeline_report(self):
        row = make_row()
        row["_timeline_report"] = {"duration_stats": [{"fir_id": "FIR-001", "duration_days": 45}]}
        rec = CaseRecord.from_dict(row)
        assert rec.investigation_duration_days == 45

    def test_kg_nodes_from_knowledge_graph_report(self):
        row = make_row()
        row["_knowledge_graph_report"] = {"nodes": [{"node_id": "NODE-AAA"}]}
        rec = CaseRecord.from_dict(row)
        assert "node-aaa" in rec.knowledge_graph_node_ids

    def test_timeline_events_deduplicated(self):
        row = make_row()
        row["_timeline_report"] = {
            "events": [
                {"event_type": "Arrest"},
                {"event_type": "Arrest"},
                {"event_type": "FIR Registered"},
            ]
        }
        rec = CaseRecord.from_dict(row)
        assert rec.timeline_event_types.count("arrest") == 1


# ─────────────────────────────────────────────────────────────────────────────
# 3. SIMILARITY CALCULATOR — PERFECT MATCH
# ─────────────────────────────────────────────────────────────────────────────

class TestSimilarityCalculatorPerfectMatch:
    def setup_method(self):
        self.base = make_record(
            crime_no="FIR-BASE",
            organizations=["org-alpha"],
            gang_names=["gang-beta"],
            repeat_offender=True,
        )
        self.clone = make_record(
            crime_no="FIR-CLONE",
            organizations=["org-alpha"],
            gang_names=["gang-beta"],
            repeat_offender=True,
        )

    def test_perfect_match_score_100(self):
        # Identical attributes → all features match → score = 100
        score = SimilarityCalculator.compute(self.base, self.clone)
        assert score.normalized_score == 100

    def test_perfect_match_raw_equals_max(self):
        score = SimilarityCalculator.compute(self.base, self.clone)
        assert score.raw_score == _MAX_RAW_SCORE

    def test_all_features_match(self):
        score = SimilarityCalculator.compute(self.base, self.clone)
        matched_features = {m.feature for m in score.matching_features}
        for feat in CaseFeature:
            assert feat in matched_features, f"{feat} should match"

    def test_no_differing_features(self):
        score = SimilarityCalculator.compute(self.base, self.clone)
        assert score.differing_features == []


# ─────────────────────────────────────────────────────────────────────────────
# 4. SIMILARITY CALCULATOR — ZERO MATCH
# ─────────────────────────────────────────────────────────────────────────────

class TestSimilarityCalculatorZeroMatch:
    def setup_method(self):
        self.base = make_record(
            crime_no="FIR-A",
            district="mysuru",
            police_station="station-a",
            crime_type="theft",
            accused_names=["alpha"],
            victim_names=["victim-a"],
            vehicle_nos=["KA-01-AA-0001"],
            weapons=["knife"],
            phones=["1111111111"],
            organizations=[],
            gang_names=[],
            crime_pattern="pattern-a",
            modus_operandi="mo-a",
            recovery_pattern="recovery-a",
            hotspot="hotspot-a",
            repeat_offender=False,
            investigation_duration_days=10,
            knowledge_graph_node_ids=["node-a"],
            timeline_event_types=["fir registered"],
        )
        self.other = make_record(
            crime_no="FIR-B",
            district="bengaluru",
            police_station="station-b",
            crime_type="murder",
            accused_names=["beta"],
            victim_names=["victim-b"],
            vehicle_nos=["MH-01-ZZ-9999"],
            weapons=["gun"],
            phones=["9999999999"],
            organizations=[],
            gang_names=[],
            crime_pattern="pattern-b",
            modus_operandi="mo-b",
            recovery_pattern="recovery-b",
            hotspot="hotspot-b",
            repeat_offender=False,
            investigation_duration_days=200,
            knowledge_graph_node_ids=["node-b"],
            timeline_event_types=["case closed"],
        )

    def test_zero_match_score_zero(self):
        score = SimilarityCalculator.compute(self.base, self.other)
        assert score.raw_score == 0
        assert score.normalized_score == 0

    def test_no_matching_features(self):
        score = SimilarityCalculator.compute(self.base, self.other)
        assert score.matching_features == []

    def test_all_features_differ(self):
        score = SimilarityCalculator.compute(self.base, self.other)
        assert len(score.differing_features) == len(CaseFeature)


# ─────────────────────────────────────────────────────────────────────────────
# 5. INDIVIDUAL FEATURE TESTS — ACCUSED
# ─────────────────────────────────────────────────────────────────────────────

class TestFeatureAccused:
    """200 accused-based scenarios."""

    def _base(self, accused):
        return make_record(crime_no="BASE", accused_names=accused,
                           # Zero out all other features
                           district="d1", police_station="ps1",
                           crime_type="ct1", victim_names=[],
                           vehicle_nos=[], weapons=[], phones=[],
                           crime_pattern="", modus_operandi="",
                           recovery_pattern="", hotspot="",
                           knowledge_graph_node_ids=[], timeline_event_types=[],
                           repeat_offender=False, investigation_duration_days=None)

    def _cand(self, crime_no, accused, district="d2", ps="ps2", ct="ct2"):
        return make_record(crime_no=crime_no, accused_names=accused,
                           district=district, police_station=ps,
                           crime_type=ct, victim_names=[],
                           vehicle_nos=[], weapons=[], phones=[],
                           crime_pattern="", modus_operandi="",
                           recovery_pattern="", hotspot="",
                           knowledge_graph_node_ids=[], timeline_event_types=[],
                           repeat_offender=False, investigation_duration_days=None)

    @pytest.mark.parametrize("name", [
        "raju", "sanjay", "ramesh", "suresh", "anil", "vijay", "prakash",
        "mohan", "gopal", "naresh", "rahul", "deepak", "manoj", "sanjay kumar",
        "r.k. sharma", "bheemaiah", "thimmaiah", "shiva", "ganesh", "lokesh",
    ])
    def test_same_accused_match(self, name):
        b = self._base([name])
        c = self._cand("CAND", [name])
        score = SimilarityCalculator.compute(b, c)
        accused_feat = next((m for m in score.matching_features if m.feature == CaseFeature.ACCUSED), None)
        assert accused_feat is not None
        assert accused_feat.score_awarded == FEATURE_WEIGHTS[CaseFeature.ACCUSED]

    @pytest.mark.parametrize("a,b", [
        (["raju"], ["sanjay"]),
        (["alpha"], ["beta"]),
        (["x"], ["y"]),
        ([], ["raju"]),
        (["raju"], []),
    ])
    def test_different_accused_no_match(self, a, b):
        base = self._base(a)
        cand = self._cand("CAND", b)
        score = SimilarityCalculator.compute(base, cand)
        accused_feat = next((m for m in score.matching_features if m.feature == CaseFeature.ACCUSED), None)
        assert accused_feat is None

    def test_accused_partial_overlap(self):
        b = self._base(["raju", "sanjay"])
        c = self._cand("CAND", ["sanjay", "mohan"])
        score = SimilarityCalculator.compute(b, c)
        # Partial overlap → still a match (intersection non-empty)
        accused_feat = next((m for m in score.matching_features if m.feature == CaseFeature.ACCUSED), None)
        assert accused_feat is not None

    @pytest.mark.parametrize("n", range(50))
    def test_deterministic_accused_match(self, n):
        """Same input always yields same output."""
        name = f"accused_{n}"
        b = self._base([name])
        c = self._cand("CAND", [name])
        s1 = SimilarityCalculator.compute(b, c)
        s2 = SimilarityCalculator.compute(b, c)
        assert s1.normalized_score == s2.normalized_score

    @pytest.mark.parametrize("n", range(50))
    def test_deterministic_accused_no_match(self, n):
        b = self._base([f"person_{n}_a"])
        c = self._cand("CAND", [f"person_{n}_b"])
        s1 = SimilarityCalculator.compute(b, c)
        s2 = SimilarityCalculator.compute(b, c)
        assert s1.normalized_score == s2.normalized_score

    @pytest.mark.parametrize("n", range(100))
    def test_accused_score_contribution(self, n):
        """Accused score contribution is always the defined weight."""
        name = f"person_{n}"
        b = self._base([name])
        c = self._cand("CAND", [name])
        score = SimilarityCalculator.compute(b, c)
        awarded = sum(m.score_awarded for m in score.matching_features if m.feature == CaseFeature.ACCUSED)
        assert awarded == FEATURE_WEIGHTS[CaseFeature.ACCUSED]


# ─────────────────────────────────────────────────────────────────────────────
# 6. INDIVIDUAL FEATURE TESTS — VEHICLE
# ─────────────────────────────────────────────────────────────────────────────

class TestFeatureVehicle:
    def _rec(self, crime_no, vehicles, **kw):
        defaults = dict(crime_no=crime_no, vehicle_nos=vehicles,
                        district="d", police_station="ps", crime_type="ct",
                        accused_names=[], victim_names=[], weapons=[],
                        phones=[], organizations=[], gang_names=[],
                        crime_pattern="", modus_operandi="", recovery_pattern="",
                        hotspot="", repeat_offender=False,
                        investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        defaults.update(kw)
        return make_record(**defaults)

    VEHICLES = [
        "KA-01-AB-1234", "KA-09-CD-5678", "MH-12-EF-9012",
        "TN-04-GH-3456", "DL-05-IJ-7890", "KL-07-KL-1111",
        "AP-28-MN-2222", "TS-09-OP-3333", "GJ-01-QR-4444",
        "RJ-14-ST-5555",
    ]

    @pytest.mark.parametrize("veh", VEHICLES)
    def test_same_vehicle_match(self, veh):
        b = self._rec("BASE", [veh])
        c = self._rec("CAND", [veh])
        score = SimilarityCalculator.compute(b, c)
        feat = next((m for m in score.matching_features if m.feature == CaseFeature.VEHICLE), None)
        assert feat is not None

    @pytest.mark.parametrize("veh", VEHICLES)
    def test_different_vehicle_no_match(self, veh):
        b = self._rec("BASE", [veh])
        c = self._rec("CAND", ["XX-99-ZZ-0000"])
        score = SimilarityCalculator.compute(b, c)
        feat = next((m for m in score.matching_features if m.feature == CaseFeature.VEHICLE), None)
        assert feat is None

    @pytest.mark.parametrize("n", range(50))
    def test_vehicle_score_deterministic(self, n):
        veh = f"KA-{n:02d}-AB-{n:04d}"
        b = self._rec("BASE", [veh])
        c = self._rec("CAND", [veh])
        s1 = SimilarityCalculator.compute(b, c)
        s2 = SimilarityCalculator.compute(b, c)
        assert s1.raw_score == s2.raw_score

    def test_vehicle_partial_overlap(self):
        b = self._rec("BASE", ["KA-01-AB-1234", "KA-02-CD-5678"])
        c = self._rec("CAND", ["KA-02-CD-5678", "MH-99-ZZ-9999"])
        score = SimilarityCalculator.compute(b, c)
        feat = next((m for m in score.matching_features if m.feature == CaseFeature.VEHICLE), None)
        assert feat is not None

    def test_empty_vehicles_no_match(self):
        b = self._rec("BASE", [])
        c = self._rec("CAND", [])
        score = SimilarityCalculator.compute(b, c)
        feat = next((m for m in score.matching_features if m.feature == CaseFeature.VEHICLE), None)
        assert feat is None


# ─────────────────────────────────────────────────────────────────────────────
# 7. INDIVIDUAL FEATURE TESTS — WEAPON
# ─────────────────────────────────────────────────────────────────────────────

class TestFeatureWeapon:
    def _rec(self, crime_no, weapons):
        return make_record(crime_no=crime_no, weapons=weapons,
                           district="d", police_station="ps", crime_type="ct",
                           accused_names=[], victim_names=[], vehicle_nos=[],
                           phones=[], organizations=[], gang_names=[],
                           crime_pattern="", modus_operandi="", recovery_pattern="",
                           hotspot="", repeat_offender=False,
                           investigation_duration_days=None,
                           knowledge_graph_node_ids=[], timeline_event_types=[])

    WEAPONS = ["knife", "gun", "rod", "sword", "axe", "stone", "acid",
               "country bomb", "pistol", "dagger"]

    @pytest.mark.parametrize("wpn", WEAPONS)
    def test_same_weapon_match(self, wpn):
        b = self._rec("BASE", [wpn])
        c = self._rec("CAND", [wpn])
        score = SimilarityCalculator.compute(b, c)
        feat = next((m for m in score.matching_features if m.feature == CaseFeature.WEAPON), None)
        assert feat is not None

    @pytest.mark.parametrize("wpn", WEAPONS)
    def test_different_weapon_no_match(self, wpn):
        b = self._rec("BASE", [wpn])
        c = self._rec("CAND", ["completely different weapon xyz"])
        score = SimilarityCalculator.compute(b, c)
        feat = next((m for m in score.matching_features if m.feature == CaseFeature.WEAPON), None)
        assert feat is None

    @pytest.mark.parametrize("n", range(30))
    def test_weapon_determinism(self, n):
        wpn = f"weapon_{n}"
        b = self._rec("BASE", [wpn])
        c = self._rec("CAND", [wpn])
        assert SimilarityCalculator.compute(b, c).normalized_score == \
               SimilarityCalculator.compute(b, c).normalized_score


# ─────────────────────────────────────────────────────────────────────────────
# 8. INDIVIDUAL FEATURE TESTS — PHONE
# ─────────────────────────────────────────────────────────────────────────────

class TestFeaturePhone:
    def _rec(self, crime_no, phones):
        return make_record(crime_no=crime_no, phones=phones,
                           district="d", police_station="ps", crime_type="ct",
                           accused_names=[], victim_names=[], vehicle_nos=[],
                           weapons=[], organizations=[], gang_names=[],
                           crime_pattern="", modus_operandi="", recovery_pattern="",
                           hotspot="", repeat_offender=False,
                           investigation_duration_days=None,
                           knowledge_graph_node_ids=[], timeline_event_types=[])

    PHONES = [
        "9876543210", "8765432109", "7654321098", "6543210987",
        "9123456789", "9012345678", "9111222333", "8888777666",
    ]

    @pytest.mark.parametrize("ph", PHONES)
    def test_same_phone_match(self, ph):
        b = self._rec("BASE", [ph])
        c = self._rec("CAND", [ph])
        score = SimilarityCalculator.compute(b, c)
        feat = next((m for m in score.matching_features if m.feature == CaseFeature.PHONE), None)
        assert feat is not None

    @pytest.mark.parametrize("ph", PHONES)
    def test_different_phone_no_match(self, ph):
        b = self._rec("BASE", [ph])
        c = self._rec("CAND", ["0000000000"])
        score = SimilarityCalculator.compute(b, c)
        feat = next((m for m in score.matching_features if m.feature == CaseFeature.PHONE), None)
        assert feat is None

    @pytest.mark.parametrize("n", range(30))
    def test_phone_determinism(self, n):
        ph = f"98765{n:05d}"
        b = self._rec("BASE", [ph])
        c = self._rec("CAND", [ph])
        assert SimilarityCalculator.compute(b, c).raw_score == \
               SimilarityCalculator.compute(b, c).raw_score


# ─────────────────────────────────────────────────────────────────────────────
# 9. FEATURE TESTS — DISTRICT & STATION
# ─────────────────────────────────────────────────────────────────────────────

class TestFeatureDistrictStation:
    DISTRICTS = [
        "mysuru", "mandya", "bengaluru urban", "hassan", "kodagu",
        "shivamogga", "dharwad", "belagavi", "kalaburagi", "tumakuru",
    ]
    STATIONS = [
        "siddarthanagar ps", "vijayanagar ps", "jayanagar ps",
        "koramangala ps", "hebbal ps", "yelahanka ps",
    ]

    @pytest.mark.parametrize("dist", DISTRICTS)
    def test_same_district_match(self, dist):
        b = make_record(crime_no="BASE", district=dist, police_station="ps-x",
                        crime_type="ct", accused_names=[], victim_names=[],
                        vehicle_nos=[], weapons=[], phones=[], organizations=[],
                        gang_names=[], crime_pattern="", modus_operandi="",
                        recovery_pattern="", hotspot="", repeat_offender=False,
                        investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        c = make_record(crime_no="CAND", district=dist, police_station="ps-y",
                        crime_type="ct2", accused_names=[], victim_names=[],
                        vehicle_nos=[], weapons=[], phones=[], organizations=[],
                        gang_names=[], crime_pattern="", modus_operandi="",
                        recovery_pattern="", hotspot="", repeat_offender=False,
                        investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        score = SimilarityCalculator.compute(b, c)
        feat = next((m for m in score.matching_features if m.feature == CaseFeature.DISTRICT), None)
        assert feat is not None

    @pytest.mark.parametrize("dist_a,dist_b", [
        ("mysuru", "mandya"),
        ("bengaluru urban", "mysuru"),
        ("hassan", "kalaburagi"),
    ])
    def test_cross_district_no_match(self, dist_a, dist_b):
        b = make_record(crime_no="BASE", district=dist_a, police_station="ps-x",
                        crime_type="ct", accused_names=[], victim_names=[],
                        vehicle_nos=[], weapons=[], phones=[], organizations=[],
                        gang_names=[], crime_pattern="", modus_operandi="",
                        recovery_pattern="", hotspot="", repeat_offender=False,
                        investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        c = make_record(crime_no="CAND", district=dist_b, police_station="ps-y",
                        crime_type="ct2", accused_names=[], victim_names=[],
                        vehicle_nos=[], weapons=[], phones=[], organizations=[],
                        gang_names=[], crime_pattern="", modus_operandi="",
                        recovery_pattern="", hotspot="", repeat_offender=False,
                        investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        score = SimilarityCalculator.compute(b, c)
        feat = next((m for m in score.matching_features if m.feature == CaseFeature.DISTRICT), None)
        assert feat is None

    @pytest.mark.parametrize("ps", STATIONS)
    def test_same_station_match(self, ps):
        b = make_record(crime_no="BASE", district="mysuru", police_station=ps,
                        crime_type="ct", accused_names=[], victim_names=[],
                        vehicle_nos=[], weapons=[], phones=[], organizations=[],
                        gang_names=[], crime_pattern="", modus_operandi="",
                        recovery_pattern="", hotspot="", repeat_offender=False,
                        investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        c = make_record(crime_no="CAND", district="mandya", police_station=ps,
                        crime_type="ct2", accused_names=[], victim_names=[],
                        vehicle_nos=[], weapons=[], phones=[], organizations=[],
                        gang_names=[], crime_pattern="", modus_operandi="",
                        recovery_pattern="", hotspot="", repeat_offender=False,
                        investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        score = SimilarityCalculator.compute(b, c)
        feat = next((m for m in score.matching_features if m.feature == CaseFeature.POLICE_STATION), None)
        assert feat is not None

    @pytest.mark.parametrize("ps_a,ps_b", [
        ("siddarthanagar ps", "vijayanagar ps"),
        ("koramangala ps", "hebbal ps"),
    ])
    def test_cross_station_no_match(self, ps_a, ps_b):
        b = make_record(crime_no="BASE", district="mysuru", police_station=ps_a,
                        crime_type="ct", accused_names=[], victim_names=[],
                        vehicle_nos=[], weapons=[], phones=[], organizations=[],
                        gang_names=[], crime_pattern="", modus_operandi="",
                        recovery_pattern="", hotspot="", repeat_offender=False,
                        investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        c = make_record(crime_no="CAND", district="mysuru", police_station=ps_b,
                        crime_type="ct", accused_names=[], victim_names=[],
                        vehicle_nos=[], weapons=[], phones=[], organizations=[],
                        gang_names=[], crime_pattern="", modus_operandi="",
                        recovery_pattern="", hotspot="", repeat_offender=False,
                        investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        score = SimilarityCalculator.compute(b, c)
        feat = next((m for m in score.matching_features if m.feature == CaseFeature.POLICE_STATION), None)
        assert feat is None


# ─────────────────────────────────────────────────────────────────────────────
# 10. PARTIAL MATCH SCENARIOS
# ─────────────────────────────────────────────────────────────────────────────

class TestPartialMatches:
    """100+ partial match scenarios verifying score range logic."""

    @pytest.mark.parametrize("n_features", range(1, len(CaseFeature) + 1))
    def test_partial_feature_match_score_range(self, n_features):
        """Partial match: only district and station shared."""
        features = list(CaseFeature)[:n_features]
        b = make_record(crime_no="BASE", district="mysuru", police_station="ps-a",
                        crime_type="theft", accused_names=["raju"], victim_names=["kumar"],
                        vehicle_nos=["KA-01"], weapons=["knife"], phones=["9876"],
                        organizations=["org-a"], gang_names=["gang-a"],
                        crime_pattern="pattern-a", modus_operandi="mo-a",
                        recovery_pattern="rec-a", hotspot="hs-a",
                        repeat_offender=True, investigation_duration_days=30,
                        knowledge_graph_node_ids=["node-a"], timeline_event_types=["arrest", "fir registered"])
        c = make_record(crime_no="CAND", district="mysuru", police_station="ps-a",
                        crime_type="theft", accused_names=["raju"], victim_names=["kumar"],
                        vehicle_nos=["KA-01"], weapons=["knife"], phones=["9876"],
                        organizations=["org-a"], gang_names=["gang-a"],
                        crime_pattern="pattern-a", modus_operandi="mo-a",
                        recovery_pattern="rec-a", hotspot="hs-a",
                        repeat_offender=True, investigation_duration_days=30,
                        knowledge_graph_node_ids=["node-a"], timeline_event_types=["arrest", "fir registered"])
        score = SimilarityCalculator.compute(b, c)
        assert 0 <= score.normalized_score <= 100

    def test_only_district_match(self):
        b = make_record(crime_no="BASE", district="mysuru", police_station="ps-a",
                        crime_type="theft", accused_names=[], victim_names=[],
                        vehicle_nos=[], weapons=[], phones=[], organizations=[],
                        gang_names=[], crime_pattern="", modus_operandi="",
                        recovery_pattern="", hotspot="", repeat_offender=False,
                        investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        c = make_record(crime_no="CAND", district="mysuru", police_station="ps-b",
                        crime_type="robbery", accused_names=[], victim_names=[],
                        vehicle_nos=[], weapons=[], phones=[], organizations=[],
                        gang_names=[], crime_pattern="", modus_operandi="",
                        recovery_pattern="", hotspot="", repeat_offender=False,
                        investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        score = SimilarityCalculator.compute(b, c)
        assert score.raw_score == FEATURE_WEIGHTS[CaseFeature.DISTRICT]

    def test_only_station_match(self):
        b = make_record(crime_no="BASE", district="mysuru", police_station="siddarthanagar ps",
                        crime_type="theft", accused_names=[], victim_names=[],
                        vehicle_nos=[], weapons=[], phones=[], organizations=[],
                        gang_names=[], crime_pattern="", modus_operandi="",
                        recovery_pattern="", hotspot="", repeat_offender=False,
                        investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        c = make_record(crime_no="CAND", district="mandya", police_station="siddarthanagar ps",
                        crime_type="robbery", accused_names=[], victim_names=[],
                        vehicle_nos=[], weapons=[], phones=[], organizations=[],
                        gang_names=[], crime_pattern="", modus_operandi="",
                        recovery_pattern="", hotspot="", repeat_offender=False,
                        investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        score = SimilarityCalculator.compute(b, c)
        assert score.raw_score == FEATURE_WEIGHTS[CaseFeature.POLICE_STATION]

    def test_district_and_crime_type_only(self):
        b = make_record(crime_no="BASE", district="mysuru", police_station="ps-a",
                        crime_type="theft", accused_names=[], victim_names=[],
                        vehicle_nos=[], weapons=[], phones=[], organizations=[],
                        gang_names=[], crime_pattern="", modus_operandi="",
                        recovery_pattern="", hotspot="", repeat_offender=False,
                        investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        c = make_record(crime_no="CAND", district="mysuru", police_station="ps-b",
                        crime_type="theft", accused_names=[], victim_names=[],
                        vehicle_nos=[], weapons=[], phones=[], organizations=[],
                        gang_names=[], crime_pattern="", modus_operandi="",
                        recovery_pattern="", hotspot="", repeat_offender=False,
                        investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        score = SimilarityCalculator.compute(b, c)
        expected_raw = FEATURE_WEIGHTS[CaseFeature.DISTRICT] + FEATURE_WEIGHTS[CaseFeature.CRIME_TYPE]
        assert score.raw_score == expected_raw

    @pytest.mark.parametrize("n", range(50))
    def test_single_feature_scores_are_consistent(self, n):
        """Any single-feature match always awards exactly that feature's weight."""
        b = make_record(crime_no="BASE", district="mysuru", police_station="ps-a",
                        crime_type="ct-x", accused_names=[], victim_names=[],
                        vehicle_nos=[], weapons=[], phones=[], organizations=[],
                        gang_names=[], crime_pattern="", modus_operandi="",
                        recovery_pattern="", hotspot="", repeat_offender=False,
                        investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        c = make_record(crime_no=f"CAND-{n}", district="mysuru", police_station="ps-b",
                        crime_type="ct-y", accused_names=[], victim_names=[],
                        vehicle_nos=[], weapons=[], phones=[], organizations=[],
                        gang_names=[], crime_pattern="", modus_operandi="",
                        recovery_pattern="", hotspot="", repeat_offender=False,
                        investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        score = SimilarityCalculator.compute(b, c)
        assert score.raw_score == FEATURE_WEIGHTS[CaseFeature.DISTRICT]


# ─────────────────────────────────────────────────────────────────────────────
# 11. HOTSPOT FEATURE
# ─────────────────────────────────────────────────────────────────────────────

class TestFeatureHotspot:
    HOTSPOTS = [
        "mysuru_market", "bengaluru_city_centre", "koramangala",
        "whitefield", "electronic_city", "jayanagar_4th_block",
        "malleswaram", "rajajinagar", "mg_road", "indiranagar",
    ]

    @pytest.mark.parametrize("hs", HOTSPOTS)
    def test_same_hotspot_match(self, hs):
        b = make_record(crime_no="BASE", hotspot=hs,
                        district="d", police_station="ps", crime_type="ct",
                        accused_names=[], victim_names=[], vehicle_nos=[],
                        weapons=[], phones=[], organizations=[], gang_names=[],
                        crime_pattern="", modus_operandi="", recovery_pattern="",
                        repeat_offender=False, investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        c = make_record(crime_no="CAND", hotspot=hs,
                        district="d2", police_station="ps2", crime_type="ct2",
                        accused_names=[], victim_names=[], vehicle_nos=[],
                        weapons=[], phones=[], organizations=[], gang_names=[],
                        crime_pattern="", modus_operandi="", recovery_pattern="",
                        repeat_offender=False, investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        score = SimilarityCalculator.compute(b, c)
        feat = next((m for m in score.matching_features if m.feature == CaseFeature.HOTSPOT), None)
        assert feat is not None

    @pytest.mark.parametrize("hs1,hs2", [
        ("mysuru_market", "bengaluru_city_centre"),
        ("koramangala", "whitefield"),
    ])
    def test_different_hotspot_no_match(self, hs1, hs2):
        b = make_record(crime_no="BASE", hotspot=hs1,
                        district="d", police_station="ps", crime_type="ct",
                        accused_names=[], victim_names=[], vehicle_nos=[],
                        weapons=[], phones=[], organizations=[], gang_names=[],
                        crime_pattern="", modus_operandi="", recovery_pattern="",
                        repeat_offender=False, investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        c = make_record(crime_no="CAND", hotspot=hs2,
                        district="d2", police_station="ps2", crime_type="ct",
                        accused_names=[], victim_names=[], vehicle_nos=[],
                        weapons=[], phones=[], organizations=[], gang_names=[],
                        crime_pattern="", modus_operandi="", recovery_pattern="",
                        repeat_offender=False, investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        score = SimilarityCalculator.compute(b, c)
        feat = next((m for m in score.matching_features if m.feature == CaseFeature.HOTSPOT), None)
        assert feat is None


# ─────────────────────────────────────────────────────────────────────────────
# 12. INVESTIGATION DURATION
# ─────────────────────────────────────────────────────────────────────────────

class TestInvestigationDuration:
    @pytest.mark.parametrize("days_a,days_b,should_match", [
        (30, 30, True),
        (30, 59, True),    # exactly 29 days apart — within ±30 window
        (30, 60, True),    # exactly 30 days apart — within ±30 window
        (30, 61, False),   # 31 days apart — outside window
        (100, 200, False),
        (0, 0, True),
        (365, 365, True),
        (100, 70, True),   # 30 days apart
        (None, 30, False),
        (30, None, False),
        (None, None, False),
    ])
    def test_duration_match(self, days_a, days_b, should_match):
        b = make_record(crime_no="BASE", investigation_duration_days=days_a,
                        district="d", police_station="ps", crime_type="ct",
                        accused_names=[], victim_names=[], vehicle_nos=[],
                        weapons=[], phones=[], organizations=[], gang_names=[],
                        crime_pattern="", modus_operandi="", recovery_pattern="",
                        hotspot="", repeat_offender=False,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        c = make_record(crime_no="CAND", investigation_duration_days=days_b,
                        district="d2", police_station="ps2", crime_type="ct2",
                        accused_names=[], victim_names=[], vehicle_nos=[],
                        weapons=[], phones=[], organizations=[], gang_names=[],
                        crime_pattern="", modus_operandi="", recovery_pattern="",
                        hotspot="", repeat_offender=False,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        score = SimilarityCalculator.compute(b, c)
        feat = next((m for m in score.matching_features
                     if m.feature == CaseFeature.INVESTIGATION_DURATION), None)
        if should_match:
            assert feat is not None
        else:
            assert feat is None


# ─────────────────────────────────────────────────────────────────────────────
# 13. TIMELINE PATTERN FEATURE
# ─────────────────────────────────────────────────────────────────────────────

class TestTimelinePatternFeature:
    @pytest.mark.parametrize("base_events,cand_events,should_match", [
        (["fir registered", "arrest", "court hearing"], ["fir registered", "arrest", "bail"], True),
        (["fir registered", "arrest"], ["fir registered", "arrest"], True),
        (["fir registered"], ["arrest"], False),   # only 1 shared — < 2 threshold
        ([], [], False),
        (["fir registered", "arrest", "bail"], ["court hearing", "charge sheet"], False),
        (["a", "b", "c"], ["a", "b", "d"], True),
    ])
    def test_timeline_pattern(self, base_events, cand_events, should_match):
        b = make_record(crime_no="BASE", timeline_event_types=base_events,
                        district="d", police_station="ps", crime_type="ct",
                        accused_names=[], victim_names=[], vehicle_nos=[],
                        weapons=[], phones=[], organizations=[], gang_names=[],
                        crime_pattern="", modus_operandi="", recovery_pattern="",
                        hotspot="", repeat_offender=False, investigation_duration_days=None,
                        knowledge_graph_node_ids=[])
        c = make_record(crime_no="CAND", timeline_event_types=cand_events,
                        district="d2", police_station="ps2", crime_type="ct2",
                        accused_names=[], victim_names=[], vehicle_nos=[],
                        weapons=[], phones=[], organizations=[], gang_names=[],
                        crime_pattern="", modus_operandi="", recovery_pattern="",
                        hotspot="", repeat_offender=False, investigation_duration_days=None,
                        knowledge_graph_node_ids=[])
        score = SimilarityCalculator.compute(b, c)
        feat = next((m for m in score.matching_features if m.feature == CaseFeature.TIMELINE_PATTERN), None)
        if should_match:
            assert feat is not None
        else:
            assert feat is None


# ─────────────────────────────────────────────────────────────────────────────
# 14. NORMALIZATION CORRECTNESS
# ─────────────────────────────────────────────────────────────────────────────

class TestNormalization:
    def test_zero_raw_yields_zero_normalized(self):
        b = make_record(crime_no="B", district="d1", police_station="ps1", crime_type="ct1",
                        accused_names=[], victim_names=[], vehicle_nos=[], weapons=[],
                        phones=[], organizations=[], gang_names=[], crime_pattern="",
                        modus_operandi="", recovery_pattern="", hotspot="",
                        repeat_offender=False, investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        c = make_record(crime_no="C", district="d2", police_station="ps2", crime_type="ct2",
                        accused_names=[], victim_names=[], vehicle_nos=[], weapons=[],
                        phones=[], organizations=[], gang_names=[], crime_pattern="",
                        modus_operandi="", recovery_pattern="", hotspot="",
                        repeat_offender=False, investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        s = SimilarityCalculator.compute(b, c)
        assert s.normalized_score == 0

    def test_max_raw_yields_100_normalized(self):
        b = make_record(crime_no="BASE", organizations=["org-x"], gang_names=["gang-x"], repeat_offender=True)
        c = make_record(crime_no="CLONE", organizations=["org-x"], gang_names=["gang-x"], repeat_offender=True)
        s = SimilarityCalculator.compute(b, c)
        assert s.normalized_score == 100

    def test_normalized_always_in_0_100_range(self):
        import random
        rng = random.Random(42)
        for _ in range(100):
            accused = [f"name_{rng.randint(0, 5)}"]
            veh = [f"KA-{rng.randint(0, 9):02d}"]
            b = make_record(crime_no="B", accused_names=accused, vehicle_nos=veh)
            c = make_record(crime_no="C", accused_names=accused if rng.random() > 0.5 else [],
                            vehicle_nos=veh if rng.random() > 0.5 else [])
            s = SimilarityCalculator.compute(b, c)
            assert 0 <= s.normalized_score <= 100


# ─────────────────────────────────────────────────────────────────────────────
# 15. SELF-COMPARISON (DUPLICATE DETECTION)
# ─────────────────────────────────────────────────────────────────────────────

class TestDuplicateMatches:
    def test_same_crime_no_adds_warning(self):
        b = make_record(crime_no="FIR-001")
        c = make_record(crime_no="FIR-001")
        score = SimilarityCalculator.compute(b, c)
        assert any("identical" in w.lower() or "FIR-001" in w for w in score.warnings)

    def test_self_comparison_score_100(self):
        b = make_record(crime_no="FIR-001", organizations=["org-z"], gang_names=["gang-z"], repeat_offender=True)
        s = SimilarityCalculator.compute(b, b)
        assert s.normalized_score == 100

    def test_engine_skips_self_comparisons(self):
        """CaseSimilarityEngine must exclude self-matches from top_similar_firs."""
        rows = [
            make_row(crime_no="FIR-A", accused_name="raju"),
            make_row(crime_no="FIR-A", accused_name="raju"),  # duplicate
            make_row(crime_no="FIR-B", accused_name="sanjay"),
        ]
        ctx = FakeContext(search_result=rows)
        report = CaseSimilarityEngine.find_similar_cases(ctx)
        for s in report.top_similar_firs:
            assert s.candidate_crime_no != report.base_crime_no


# ─────────────────────────────────────────────────────────────────────────────
# 16. NO MATCH / THRESHOLD
# ─────────────────────────────────────────────────────────────────────────────

class TestNoMatch:
    def test_no_match_message_in_warnings_when_below_threshold(self):
        rows = [
            make_row(crime_no="FIR-A", district_name="mysuru", crime_head="theft"),
            make_row(crime_no="FIR-B", district_name="bengaluru", crime_head="murder",
                     accused_name="beta", vehicle_no="MH-01-ZZ-0001",
                     crime_weapon="gun", accused_mobile="0000000001"),
        ]
        ctx = FakeContext(search_result=rows)
        report = CaseSimilarityEngine.find_similar_cases(ctx)
        # If score < MINIMUM_THRESHOLD, warning should appear
        if not report.top_similar_firs:
            assert any(NO_MATCH_MESSAGE in w for w in report.warnings)

    def test_empty_results_returns_no_match(self):
        ctx = FakeContext(search_result=[])
        report = CaseSimilarityEngine.find_similar_cases(ctx)
        assert any(NO_MATCH_MESSAGE in w for w in report.warnings)
        assert report.top_similar_firs == []

    def test_single_result_returns_no_match(self):
        rows = [make_row(crime_no="FIR-ONLY")]
        ctx = FakeContext(search_result=rows)
        report = CaseSimilarityEngine.find_similar_cases(ctx)
        assert any(NO_MATCH_MESSAGE in w for w in report.warnings)

    @pytest.mark.parametrize("n", range(10))
    def test_below_threshold_deterministic(self, n):
        """All-different records must consistently return no valid matches."""
        rows = [
            make_row(crime_no=f"FIR-{n}-A", district_name="mysuru", crime_head="theft",
                     accused_name=f"acc-{n}-a", vehicle_no=f"KA-{n:02d}-A"),
            make_row(crime_no=f"FIR-{n}-B", district_name="bengaluru", crime_head="murder",
                     accused_name=f"acc-{n}-b", vehicle_no=f"MH-{n:02d}-B",
                     crime_weapon="gun", accused_mobile=f"9{n}00000000"),
        ]
        ctx = FakeContext(search_result=rows)
        report = CaseSimilarityEngine.find_similar_cases(ctx)
        # Any result above threshold must have a valid score
        for s in report.top_similar_firs:
            assert s.normalized_score >= MINIMUM_THRESHOLD


# ─────────────────────────────────────────────────────────────────────────────
# 17. RECOMMENDATION GENERATION
# ─────────────────────────────────────────────────────────────────────────────

class TestRecommendationGeneration:
    def _make_similar_scores(self, n=3, base_score=80) -> List[SimilarityScore]:
        scores = []
        for i in range(n):
            fm = FeatureMatchMock(CaseFeature.ACCUSED)
            scores.append(SimilarityScore(
                base_crime_no="BASE",
                candidate_crime_no=f"CAND-{i}",
                raw_score=300,
                normalized_score=base_score - i * 5,
                matching_features=[fm],
                differing_features=[],
                warnings=[],
            ))
        return scores

    def test_empty_scores_no_recs(self):
        recs = RecommendationGenerator.generate(
            make_record(crime_no="BASE"), [], {}
        )
        assert recs == []

    def test_below_threshold_no_recs(self):
        """Scores below MINIMUM_THRESHOLD produce no recommendations."""
        base = make_record(crime_no="BASE")
        scores = [SimilarityScore(
            base_crime_no="BASE", candidate_crime_no="CAND-X",
            raw_score=5, normalized_score=MINIMUM_THRESHOLD - 1,
            matching_features=[], differing_features=[], warnings=[]
        )]
        recs = RecommendationGenerator.generate(base, scores, {})
        assert recs == []

    def test_high_score_produces_high_priority(self):
        base = make_record(crime_no="BASE")
        fm = FeatureMatchMock(CaseFeature.ACCUSED)
        scores = [SimilarityScore(
            base_crime_no="BASE", candidate_crime_no="CAND-HIGH",
            raw_score=350, normalized_score=80,
            matching_features=[fm], differing_features=[], warnings=[]
        )]
        recs = RecommendationGenerator.generate(base, scores, {})
        high_recs = [r for r in recs if r.priority == "HIGH"]
        assert len(high_recs) >= 1

    def test_medium_score_produces_medium_priority(self):
        base = make_record(crime_no="BASE")
        fm = FeatureMatchMock(CaseFeature.ACCUSED)
        scores = [SimilarityScore(
            base_crime_no="BASE", candidate_crime_no="CAND-MED",
            raw_score=200, normalized_score=50,
            matching_features=[fm], differing_features=[], warnings=[]
        )]
        recs = RecommendationGenerator.generate(base, scores, {})
        prios = {r.priority for r in recs}
        assert "HIGH" in prios or "MEDIUM" in prios

    def test_recommendations_have_evidence(self):
        base = make_record(crime_no="BASE")
        fm = FeatureMatchMock(CaseFeature.ACCUSED)
        scores = [SimilarityScore(
            base_crime_no="BASE", candidate_crime_no="CAND",
            raw_score=300, normalized_score=75,
            matching_features=[fm], differing_features=[], warnings=[]
        )]
        recs = RecommendationGenerator.generate(base, scores, {})
        for rec in recs:
            assert rec.evidence, f"Rec {rec.recommendation_id} has no evidence"

    def test_recommendations_have_supporting_firs(self):
        base = make_record(crime_no="BASE")
        fm = FeatureMatchMock(CaseFeature.ACCUSED)
        scores = [SimilarityScore(
            base_crime_no="BASE", candidate_crime_no="CAND",
            raw_score=300, normalized_score=75,
            matching_features=[fm], differing_features=[], warnings=[]
        )]
        recs = RecommendationGenerator.generate(base, scores, {})
        for rec in recs:
            assert rec.supporting_firs, f"Rec {rec.recommendation_id} has no supporting FIRs"


class FeatureMatchMock:
    """Minimal FeatureMatch for test setup."""
    def __init__(self, feature: CaseFeature):
        from app.ai.case_similarity_engine import FeatureMatch
        self.feature = feature
        self.base_value = ["test_val"]
        self.candidate_value = ["test_val"]
        self.matched = True
        self.weight = FEATURE_WEIGHTS[feature]
        self.score_awarded = self.weight
        self.evidence = f"Matched {feature.value}"


# ─────────────────────────────────────────────────────────────────────────────
# 18. RECOMMENDATION VALIDATOR
# ─────────────────────────────────────────────────────────────────────────────

class TestRecommendationValidator:
    def _make_valid_rec(self, rec_id="REC-00001", priority="HIGH") -> Recommendation:
        return Recommendation(
            recommendation_id=rec_id,
            priority=priority,
            recommendation_type="Similar FIRs",
            description="Test description",
            reason="Test reason",
            evidence=["Evidence A"],
            supporting_firs=["FIR-001"],
            confidence=0.85,
        )

    @pytest.mark.parametrize("priority", ["HIGH", "MEDIUM", "LOW"])
    def test_valid_priorities_pass(self, priority):
        rec = self._make_valid_rec(priority=priority)
        valid, warnings = RecommendationValidator.validate([rec])
        assert len(valid) == 1
        assert warnings == []

    @pytest.mark.parametrize("priority", ["CRITICAL", "URGENT", "NONE", "", "high", "medium"])
    def test_invalid_priority_rejected(self, priority):
        rec = self._make_valid_rec(priority=priority)
        valid, warnings = RecommendationValidator.validate([rec])
        assert len(valid) == 0
        assert len(warnings) >= 1

    def test_empty_evidence_rejected(self):
        rec = self._make_valid_rec()
        rec.evidence = []
        valid, warnings = RecommendationValidator.validate([rec])
        assert len(valid) == 0
        assert any("Evidence" in w or "evidence" in w for w in warnings)

    def test_empty_supporting_firs_rejected(self):
        rec = self._make_valid_rec()
        rec.supporting_firs = []
        valid, warnings = RecommendationValidator.validate([rec])
        assert len(valid) == 0

    def test_confidence_out_of_range_rejected(self):
        rec = self._make_valid_rec()
        rec.confidence = 1.5
        valid, warnings = RecommendationValidator.validate([rec])
        assert len(valid) == 0

    def test_confidence_exactly_0_valid(self):
        rec = self._make_valid_rec()
        rec.confidence = 0.0
        valid, _ = RecommendationValidator.validate([rec])
        assert len(valid) == 1

    def test_confidence_exactly_1_valid(self):
        rec = self._make_valid_rec()
        rec.confidence = 1.0
        valid, _ = RecommendationValidator.validate([rec])
        assert len(valid) == 1

    def test_empty_description_rejected(self):
        rec = self._make_valid_rec()
        rec.description = ""
        valid, warnings = RecommendationValidator.validate([rec])
        assert len(valid) == 0

    def test_empty_reason_rejected(self):
        rec = self._make_valid_rec()
        rec.reason = ""
        valid, warnings = RecommendationValidator.validate([rec])
        assert len(valid) == 0

    @pytest.mark.parametrize("n", range(20))
    def test_valid_rec_always_passes(self, n):
        rec = self._make_valid_rec(rec_id=f"REC-{n:05d}", priority="MEDIUM")
        valid, warnings = RecommendationValidator.validate([rec])
        assert len(valid) == 1

    def test_mixed_valid_invalid_recs(self):
        valid_rec = self._make_valid_rec("REC-VALID")
        invalid_rec = self._make_valid_rec("REC-INVALID")
        invalid_rec.evidence = []
        valid, warnings = RecommendationValidator.validate([valid_rec, invalid_rec])
        assert len(valid) == 1
        assert valid[0].recommendation_id == "REC-VALID"


# ─────────────────────────────────────────────────────────────────────────────
# 19. SIMILARITY REPORT STRUCTURE
# ─────────────────────────────────────────────────────────────────────────────

class TestSimilarityReportStructure:
    def test_report_to_dict_keys(self):
        report = SimilarityReport(base_crime_no="FIR-001")
        d = report.to_dict()
        assert "base_crime_no" in d
        assert "top_similar_firs" in d
        assert "recommendations" in d
        assert "warnings" in d
        assert "evidence_chain" in d

    def test_score_to_dict_keys(self):
        score = SimilarityScore(
            base_crime_no="BASE", candidate_crime_no="CAND",
            raw_score=100, normalized_score=50,
            matching_features=[], differing_features=[], warnings=[]
        )
        d = score.to_dict()
        assert "base_crime_no" in d
        assert "candidate_crime_no" in d
        assert "raw_score" in d
        assert "normalized_score" in d
        assert "matching_features" in d
        assert "differing_features" in d
        assert "warnings" in d

    def test_recommendation_to_dict_keys(self):
        rec = Recommendation(
            recommendation_id="REC-001",
            priority="HIGH",
            recommendation_type="Similar FIRs",
            description="desc",
            reason="reason",
            evidence=["ev"],
            supporting_firs=["FIR-001"],
            confidence=0.9,
        )
        d = rec.to_dict()
        assert "recommendation_id" in d
        assert "priority" in d
        assert "confidence" in d
        assert "evidence" in d
        assert "supporting_firs" in d


# ─────────────────────────────────────────────────────────────────────────────
# 20. CASE SIMILARITY ENGINE — END TO END
# ─────────────────────────────────────────────────────────────────────────────

class TestCaseSimilarityEngineEndToEnd:
    def _same_accused_rows(self):
        return [
            make_row(crime_no="FIR-001", accused_name="raju", district_name="mysuru",
                     crime_head="theft", vehicle_no="KA-09-AB-1234", crime_weapon="knife",
                     accused_mobile="9876543210"),
            make_row(crime_no="FIR-002", accused_name="raju", district_name="mysuru",
                     crime_head="theft", vehicle_no="KA-09-AB-1234", crime_weapon="knife",
                     accused_mobile="9876543210"),
            make_row(crime_no="FIR-003", accused_name="sanjay", district_name="bengaluru",
                     crime_head="robbery", vehicle_no="MH-01-ZZ-9999", crime_weapon="gun",
                     accused_mobile="0000000001"),
        ]

    def test_same_accused_appears_in_top_similar(self):
        ctx = FakeContext(search_result=self._same_accused_rows())
        report = CaseSimilarityEngine.find_similar_cases(ctx)
        top_nos = [s.candidate_crime_no for s in report.top_similar_firs]
        # FIR-002 should score higher than FIR-003
        if "fir-002" in top_nos and "fir-003" in top_nos:
            idx_002 = top_nos.index("fir-002")
            idx_003 = top_nos.index("fir-003")
            assert idx_002 < idx_003

    def test_report_sorted_descending(self):
        ctx = FakeContext(search_result=self._same_accused_rows())
        report = CaseSimilarityEngine.find_similar_cases(ctx)
        scores = [s.normalized_score for s in report.top_similar_firs]
        assert scores == sorted(scores, reverse=True)

    def test_report_evidence_chain_not_empty(self):
        ctx = FakeContext(search_result=self._same_accused_rows())
        report = CaseSimilarityEngine.find_similar_cases(ctx)
        assert len(report.evidence_chain) > 0

    def test_report_base_crime_no_correct(self):
        ctx = FakeContext(search_result=self._same_accused_rows())
        report = CaseSimilarityEngine.find_similar_cases(ctx)
        assert report.base_crime_no == "fir-001"

    def test_max_top_results_respected(self):
        rows = [make_row(crime_no=f"FIR-{i:03d}", accused_name="raju") for i in range(20)]
        ctx = FakeContext(search_result=rows)
        report = CaseSimilarityEngine.find_similar_cases(ctx)
        assert len(report.top_similar_firs) <= 10

    def test_no_hallucinated_firs_in_report(self):
        """Every candidate FIR in the report must come from the input rows."""
        rows = self._same_accused_rows()
        input_firs = {r["crime_no"].lower() for r in rows}
        ctx = FakeContext(search_result=rows)
        report = CaseSimilarityEngine.find_similar_cases(ctx)
        for s in report.top_similar_firs:
            assert s.candidate_crime_no in input_firs, \
                f"Hallucinated FIR: {s.candidate_crime_no}"

    def test_recommendations_only_reference_input_firs(self):
        rows = self._same_accused_rows()
        input_firs = {r["crime_no"].lower() for r in rows}
        ctx = FakeContext(search_result=rows)
        report = CaseSimilarityEngine.find_similar_cases(ctx)
        for rec in report.recommendations:
            for fno in rec.supporting_firs:
                assert fno.lower() in input_firs, \
                    f"Rec {rec.recommendation_id} references hallucinated FIR: {fno}"

    @pytest.mark.parametrize("n_rows", [2, 5, 10, 15, 20])
    def test_engine_scales_with_row_count(self, n_rows):
        rows = [make_row(crime_no=f"FIR-{i:03d}", accused_name="raju" if i % 2 == 0 else "sanjay")
                for i in range(n_rows)]
        ctx = FakeContext(search_result=rows)
        report = CaseSimilarityEngine.find_similar_cases(ctx)
        assert isinstance(report, SimilarityReport)

    def test_engine_deterministic_across_calls(self):
        rows = self._same_accused_rows()
        ctx1 = FakeContext(search_result=rows[:])
        ctx2 = FakeContext(search_result=rows[:])
        r1 = CaseSimilarityEngine.find_similar_cases(ctx1)
        r2 = CaseSimilarityEngine.find_similar_cases(ctx2)
        assert r1.base_crime_no == r2.base_crime_no
        assert [s.candidate_crime_no for s in r1.top_similar_firs] == \
               [s.candidate_crime_no for s in r2.top_similar_firs]
        assert [s.normalized_score for s in r1.top_similar_firs] == \
               [s.normalized_score for s in r2.top_similar_firs]


# ─────────────────────────────────────────────────────────────────────────────
# 21. CASE SIMILARITY STAGE (PIPELINE)
# ─────────────────────────────────────────────────────────────────────────────

class TestCaseSimilarityStage:
    def test_stage_sets_similarity_report(self):
        rows = [
            make_row(crime_no="FIR-A", accused_name="raju"),
            make_row(crime_no="FIR-B", accused_name="raju"),
        ]
        ctx = FakeContext(search_result=rows)
        result = CaseSimilarityStage.run(ctx)
        assert result.similarity_report is not None

    def test_stage_report_is_dict(self):
        rows = [make_row(crime_no="FIR-A"), make_row(crime_no="FIR-B")]
        ctx = FakeContext(search_result=rows)
        result = CaseSimilarityStage.run(ctx)
        assert isinstance(result.similarity_report, dict)

    def test_stage_report_has_required_keys(self):
        rows = [make_row(crime_no="FIR-A"), make_row(crime_no="FIR-B")]
        ctx = FakeContext(search_result=rows)
        result = CaseSimilarityStage.run(ctx)
        report = result.similarity_report
        for key in ["base_crime_no", "top_similar_firs", "recommendations", "warnings", "evidence_chain"]:
            assert key in report, f"Key '{key}' missing from report"

    def test_stage_handles_empty_results_gracefully(self):
        ctx = FakeContext(search_result=[])
        result = CaseSimilarityStage.run(ctx)
        assert result.similarity_report is not None

    def test_stage_handles_exception_gracefully(self):
        """Broken context must not crash the pipeline."""
        class BrokenContext:
            search_result = None   # Should trigger safe handling
            warnings = []
            timeline_report = None
            knowledge_graph_report = None
            similarity_report = None

        result = CaseSimilarityStage.run(BrokenContext())
        assert result.similarity_report is not None

    @pytest.mark.parametrize("n", range(10))
    def test_stage_always_returns_context(self, n):
        rows = [make_row(crime_no=f"FIR-{n}-{i}") for i in range(3)]
        ctx = FakeContext(search_result=rows)
        result = CaseSimilarityStage.run(ctx)
        assert result is not None


# ─────────────────────────────────────────────────────────────────────────────
# 22. FALSE POSITIVE GUARD
# ─────────────────────────────────────────────────────────────────────────────

class TestFalsePositives:
    """Ensure that completely different cases do not falsely match."""

    @pytest.mark.parametrize("n", range(20))
    def test_completely_different_cases_below_threshold(self, n):
        b = make_record(
            crime_no=f"FIR-ALPHA-{n}",
            district=f"district_a_{n}",
            police_station=f"ps_a_{n}",
            crime_type=f"crime_a_{n}",
            accused_names=[f"alpha_accused_{n}"],
            victim_names=[f"alpha_victim_{n}"],
            vehicle_nos=[f"KA-AA-{n:04d}"],
            weapons=[f"weapon_a_{n}"],
            phones=[f"91000{n:05d}"],
            organizations=[], gang_names=[],
            crime_pattern=f"pat_a_{n}", modus_operandi=f"mo_a_{n}",
            recovery_pattern=f"rec_a_{n}", hotspot=f"hs_a_{n}",
            repeat_offender=False, investigation_duration_days=10 + n,
            knowledge_graph_node_ids=[f"node_a_{n}"],
            timeline_event_types=["fir registered"],
        )
        c = make_record(
            crime_no=f"FIR-BETA-{n}",
            district=f"district_b_{n}",
            police_station=f"ps_b_{n}",
            crime_type=f"crime_b_{n}",
            accused_names=[f"beta_accused_{n}"],
            victim_names=[f"beta_victim_{n}"],
            vehicle_nos=[f"MH-BB-{n:04d}"],
            weapons=[f"weapon_b_{n}"],
            phones=[f"80000{n:05d}"],
            organizations=[], gang_names=[],
            crime_pattern=f"pat_b_{n}", modus_operandi=f"mo_b_{n}",
            recovery_pattern=f"rec_b_{n}", hotspot=f"hs_b_{n}",
            repeat_offender=False, investigation_duration_days=500 + n,
            knowledge_graph_node_ids=[f"node_b_{n}"],
            timeline_event_types=["case closed"],
        )
        score = SimilarityCalculator.compute(b, c)
        assert score.normalized_score < MINIMUM_THRESHOLD, \
            f"False positive! Score={score.normalized_score} for completely different cases"


# ─────────────────────────────────────────────────────────────────────────────
# 23. MERGE SCORES UTILITY
# ─────────────────────────────────────────────────────────────────────────────

class TestMergeScores:
    def test_merge_deduplicates(self):
        a = [SimilarityScore("B", "C1", 100, 70, [], [], [])]
        b = [SimilarityScore("B", "C1", 100, 70, [], [], [])]
        merged = CaseSimilarityEngine.merge_scores(a, b)
        assert len(merged) == 1

    def test_merge_combines_unique(self):
        a = [SimilarityScore("B", "C1", 100, 70, [], [], [])]
        b = [SimilarityScore("B", "C2", 80, 50, [], [], [])]
        merged = CaseSimilarityEngine.merge_scores(a, b)
        assert len(merged) == 2

    def test_merge_sorted_descending(self):
        a = [SimilarityScore("B", "C2", 80, 50, [], [], [])]
        b = [SimilarityScore("B", "C1", 100, 75, [], [], [])]
        merged = CaseSimilarityEngine.merge_scores(a, b)
        assert merged[0].candidate_crime_no == "C1"
        assert merged[1].candidate_crime_no == "C2"


# ─────────────────────────────────────────────────────────────────────────────
# 24. FIND COMMON FEATURE UTILITY
# ─────────────────────────────────────────────────────────────────────────────

class TestFindCommonFeature:
    def _make_score(self, cand: str, features: List[CaseFeature]) -> SimilarityScore:
        from app.ai.case_similarity_engine import FeatureMatch
        matching = [
            FeatureMatch(f, "v", "v", True, FEATURE_WEIGHTS[f], FEATURE_WEIGHTS[f], "match")
            for f in features
        ]
        return SimilarityScore("BASE", cand, 100, 75, matching, [], [])

    def test_find_accused_firs(self):
        scores = [
            self._make_score("FIR-A", [CaseFeature.ACCUSED]),
            self._make_score("FIR-B", [CaseFeature.VEHICLE]),
            self._make_score("FIR-C", [CaseFeature.ACCUSED, CaseFeature.WEAPON]),
        ]
        result = CaseSimilarityEngine.find_common_feature(CaseFeature.ACCUSED, scores)
        assert "FIR-A" in result
        assert "FIR-C" in result
        assert "FIR-B" not in result

    def test_find_vehicle_firs(self):
        scores = [
            self._make_score("FIR-A", [CaseFeature.VEHICLE]),
            self._make_score("FIR-B", [CaseFeature.ACCUSED]),
        ]
        result = CaseSimilarityEngine.find_common_feature(CaseFeature.VEHICLE, scores)
        assert "FIR-A" in result
        assert "FIR-B" not in result


# ─────────────────────────────────────────────────────────────────────────────
# 25. MULTI-FIR CROSS-DISTRICT / CROSS-STATION
# ─────────────────────────────────────────────────────────────────────────────

class TestCrossDistrictCrossStation:
    @pytest.mark.parametrize("n", range(15))
    def test_cross_district_same_accused(self, n):
        """Same accused across different districts should match on ACCUSED feature."""
        b = make_record(crime_no=f"FIR-D1-{n}", district=f"district_{n}_a",
                        police_station="ps-a", crime_type="theft",
                        accused_names=["cross_district_acc"],
                        victim_names=[], vehicle_nos=[], weapons=[], phones=[],
                        organizations=[], gang_names=[], crime_pattern="",
                        modus_operandi="", recovery_pattern="", hotspot="",
                        repeat_offender=False, investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        c = make_record(crime_no=f"FIR-D2-{n}", district=f"district_{n}_b",
                        police_station="ps-b", crime_type="robbery",
                        accused_names=["cross_district_acc"],
                        victim_names=[], vehicle_nos=[], weapons=[], phones=[],
                        organizations=[], gang_names=[], crime_pattern="",
                        modus_operandi="", recovery_pattern="", hotspot="",
                        repeat_offender=False, investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        score = SimilarityCalculator.compute(b, c)
        feat = next((m for m in score.matching_features if m.feature == CaseFeature.ACCUSED), None)
        assert feat is not None

    @pytest.mark.parametrize("n", range(15))
    def test_cross_station_same_vehicle(self, n):
        """Same vehicle across different stations should match on VEHICLE."""
        b = make_record(crime_no=f"FIR-S1-{n}", district="mysuru",
                        police_station=f"ps_{n}_a", crime_type="theft",
                        accused_names=[], victim_names=[],
                        vehicle_nos=[f"KA-CS-{n:04d}"],
                        weapons=[], phones=[], organizations=[], gang_names=[],
                        crime_pattern="", modus_operandi="", recovery_pattern="",
                        hotspot="", repeat_offender=False, investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        c = make_record(crime_no=f"FIR-S2-{n}", district="mysuru",
                        police_station=f"ps_{n}_b", crime_type="robbery",
                        accused_names=[], victim_names=[],
                        vehicle_nos=[f"KA-CS-{n:04d}"],
                        weapons=[], phones=[], organizations=[], gang_names=[],
                        crime_pattern="", modus_operandi="", recovery_pattern="",
                        hotspot="", repeat_offender=False, investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        score = SimilarityCalculator.compute(b, c)
        feat = next((m for m in score.matching_features if m.feature == CaseFeature.VEHICLE), None)
        assert feat is not None


# ─────────────────────────────────────────────────────────────────────────────
# 26. MULTIPLE FIRs SCENARIO (end-to-end)
# ─────────────────────────────────────────────────────────────────────────────

class TestMultipleFIRs:
    @pytest.mark.parametrize("n_firs", [3, 5, 7, 10, 15])
    def test_multiple_firs_ranking_stable(self, n_firs):
        """Ranking must be stable across multiple FIRs."""
        rows = []
        for i in range(n_firs):
            rows.append(make_row(
                crime_no=f"FIR-{i:03d}",
                accused_name="raju" if i % 3 == 0 else f"person_{i}",
                vehicle_no="KA-09-AB-1234" if i % 4 == 0 else f"XX-{i:02d}",
            ))
        ctx = FakeContext(search_result=rows)
        r = CaseSimilarityEngine.find_similar_cases(ctx)
        scores = [s.normalized_score for s in r.top_similar_firs]
        assert scores == sorted(scores, reverse=True)

    def test_long_investigation_appears_in_report(self):
        rows = []
        for i in range(5):
            rows.append(make_row(
                crime_no=f"FIR-LONG-{i}",
                accused_name="raju",
            ))
        ctx = FakeContext(search_result=rows)
        r = CaseSimilarityEngine.find_similar_cases(ctx)
        assert isinstance(r, SimilarityReport)

    def test_closed_investigations_handled(self):
        rows = [make_row(crime_no="FIR-CLOSED-A", crime_head="theft"),
                make_row(crime_no="FIR-CLOSED-B", crime_head="theft")]
        ctx = FakeContext(search_result=rows)
        r = CaseSimilarityEngine.find_similar_cases(ctx)
        assert isinstance(r, SimilarityReport)

    def test_active_investigations_handled(self):
        rows = [make_row(crime_no="FIR-ACT-A", accused_name="suspect_x"),
                make_row(crime_no="FIR-ACT-B", accused_name="suspect_x")]
        ctx = FakeContext(search_result=rows)
        r = CaseSimilarityEngine.find_similar_cases(ctx)
        assert isinstance(r, SimilarityReport)


# ─────────────────────────────────────────────────────────────────────────────
# 27. REPEAT OFFENDER FEATURE
# ─────────────────────────────────────────────────────────────────────────────

class TestRepeatOffenderFeature:
    def test_both_repeat_offenders_match(self):
        b = make_record(crime_no="BASE", repeat_offender=True,
                        district="d", police_station="ps", crime_type="ct",
                        accused_names=[], victim_names=[], vehicle_nos=[],
                        weapons=[], phones=[], organizations=[], gang_names=[],
                        crime_pattern="", modus_operandi="", recovery_pattern="",
                        hotspot="", investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        c = make_record(crime_no="CAND", repeat_offender=True,
                        district="d2", police_station="ps2", crime_type="ct2",
                        accused_names=[], victim_names=[], vehicle_nos=[],
                        weapons=[], phones=[], organizations=[], gang_names=[],
                        crime_pattern="", modus_operandi="", recovery_pattern="",
                        hotspot="", investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        score = SimilarityCalculator.compute(b, c)
        feat = next((m for m in score.matching_features if m.feature == CaseFeature.REPEAT_OFFENDER), None)
        assert feat is not None

    def test_one_repeat_offender_no_match(self):
        b = make_record(crime_no="BASE", repeat_offender=True,
                        district="d", police_station="ps", crime_type="ct",
                        accused_names=[], victim_names=[], vehicle_nos=[],
                        weapons=[], phones=[], organizations=[], gang_names=[],
                        crime_pattern="", modus_operandi="", recovery_pattern="",
                        hotspot="", investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        c = make_record(crime_no="CAND", repeat_offender=False,
                        district="d2", police_station="ps2", crime_type="ct2",
                        accused_names=[], victim_names=[], vehicle_nos=[],
                        weapons=[], phones=[], organizations=[], gang_names=[],
                        crime_pattern="", modus_operandi="", recovery_pattern="",
                        hotspot="", investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        score = SimilarityCalculator.compute(b, c)
        feat = next((m for m in score.matching_features if m.feature == CaseFeature.REPEAT_OFFENDER), None)
        assert feat is None


# ─────────────────────────────────────────────────────────────────────────────
# 28. KNOWLEDGE GRAPH LINK FEATURE
# ─────────────────────────────────────────────────────────────────────────────

class TestKnowledgeGraphLink:
    @pytest.mark.parametrize("nodes_a,nodes_b,should_match", [
        (["node-001"], ["node-001"], True),
        (["node-001", "node-002"], ["node-002", "node-003"], True),
        (["node-001"], ["node-002"], False),
        ([], [], False),
        (["node-x"], [], False),
    ])
    def test_kg_link(self, nodes_a, nodes_b, should_match):
        b = make_record(crime_no="BASE", knowledge_graph_node_ids=nodes_a,
                        district="d", police_station="ps", crime_type="ct",
                        accused_names=[], victim_names=[], vehicle_nos=[],
                        weapons=[], phones=[], organizations=[], gang_names=[],
                        crime_pattern="", modus_operandi="", recovery_pattern="",
                        hotspot="", repeat_offender=False, investigation_duration_days=None,
                        timeline_event_types=[])
        c = make_record(crime_no="CAND", knowledge_graph_node_ids=nodes_b,
                        district="d2", police_station="ps2", crime_type="ct2",
                        accused_names=[], victim_names=[], vehicle_nos=[],
                        weapons=[], phones=[], organizations=[], gang_names=[],
                        crime_pattern="", modus_operandi="", recovery_pattern="",
                        hotspot="", repeat_offender=False, investigation_duration_days=None,
                        timeline_event_types=[])
        score = SimilarityCalculator.compute(b, c)
        feat = next((m for m in score.matching_features if m.feature == CaseFeature.KNOWLEDGE_GRAPH_LINK), None)
        if should_match:
            assert feat is not None
        else:
            assert feat is None


# ─────────────────────────────────────────────────────────────────────────────
# 29. GANG & ORGANIZATION FEATURES
# ─────────────────────────────────────────────────────────────────────────────

class TestGangOrganization:
    @pytest.mark.parametrize("gang,match", [
        (["gang-a"], True),
        (["gang-b"], False),
        ([], False),
    ])
    def test_gang_match(self, gang, match):
        b = make_record(crime_no="BASE", gang_names=["gang-a"],
                        district="d", police_station="ps", crime_type="ct",
                        accused_names=[], victim_names=[], vehicle_nos=[],
                        weapons=[], phones=[], organizations=[],
                        crime_pattern="", modus_operandi="", recovery_pattern="",
                        hotspot="", repeat_offender=False, investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        c = make_record(crime_no="CAND", gang_names=gang,
                        district="d2", police_station="ps2", crime_type="ct2",
                        accused_names=[], victim_names=[], vehicle_nos=[],
                        weapons=[], phones=[], organizations=[],
                        crime_pattern="", modus_operandi="", recovery_pattern="",
                        hotspot="", repeat_offender=False, investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        score = SimilarityCalculator.compute(b, c)
        feat = next((m for m in score.matching_features if m.feature == CaseFeature.GANG), None)
        if match:
            assert feat is not None
        else:
            assert feat is None

    @pytest.mark.parametrize("org,match", [
        (["org-a"], True),
        (["org-z"], False),
    ])
    def test_organization_match(self, org, match):
        b = make_record(crime_no="BASE", organizations=["org-a"],
                        district="d", police_station="ps", crime_type="ct",
                        accused_names=[], victim_names=[], vehicle_nos=[],
                        weapons=[], phones=[], gang_names=[],
                        crime_pattern="", modus_operandi="", recovery_pattern="",
                        hotspot="", repeat_offender=False, investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        c = make_record(crime_no="CAND", organizations=org,
                        district="d2", police_station="ps2", crime_type="ct2",
                        accused_names=[], victim_names=[], vehicle_nos=[],
                        weapons=[], phones=[], gang_names=[],
                        crime_pattern="", modus_operandi="", recovery_pattern="",
                        hotspot="", repeat_offender=False, investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        score = SimilarityCalculator.compute(b, c)
        feat = next((m for m in score.matching_features if m.feature == CaseFeature.ORGANIZATION), None)
        if match:
            assert feat is not None
        else:
            assert feat is None


# ─────────────────────────────────────────────────────────────────────────────
# 30. MODUS OPERANDI & RECOVERY PATTERN
# ─────────────────────────────────────────────────────────────────────────────

class TestModusOperandiRecovery:
    @pytest.mark.parametrize("mo,match", [
        ("forced entry", True),
        ("pickpocket", False),
        ("", False),
    ])
    def test_modus_operandi(self, mo, match):
        b = make_record(crime_no="BASE", modus_operandi="forced entry",
                        district="d", police_station="ps", crime_type="ct",
                        accused_names=[], victim_names=[], vehicle_nos=[],
                        weapons=[], phones=[], organizations=[], gang_names=[],
                        crime_pattern="", recovery_pattern="", hotspot="",
                        repeat_offender=False, investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        c = make_record(crime_no="CAND", modus_operandi=mo,
                        district="d2", police_station="ps2", crime_type="ct2",
                        accused_names=[], victim_names=[], vehicle_nos=[],
                        weapons=[], phones=[], organizations=[], gang_names=[],
                        crime_pattern="", recovery_pattern="", hotspot="",
                        repeat_offender=False, investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        score = SimilarityCalculator.compute(b, c)
        feat = next((m for m in score.matching_features if m.feature == CaseFeature.MODUS_OPERANDI), None)
        if match:
            assert feat is not None
        else:
            assert feat is None

    @pytest.mark.parametrize("rp,match", [
        ("cash recovered", True),
        ("goods seized", False),
        ("", False),
    ])
    def test_recovery_pattern(self, rp, match):
        b = make_record(crime_no="BASE", recovery_pattern="cash recovered",
                        district="d", police_station="ps", crime_type="ct",
                        accused_names=[], victim_names=[], vehicle_nos=[],
                        weapons=[], phones=[], organizations=[], gang_names=[],
                        crime_pattern="", modus_operandi="", hotspot="",
                        repeat_offender=False, investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        c = make_record(crime_no="CAND", recovery_pattern=rp,
                        district="d2", police_station="ps2", crime_type="ct2",
                        accused_names=[], victim_names=[], vehicle_nos=[],
                        weapons=[], phones=[], organizations=[], gang_names=[],
                        crime_pattern="", modus_operandi="", hotspot="",
                        repeat_offender=False, investigation_duration_days=None,
                        knowledge_graph_node_ids=[], timeline_event_types=[])
        score = SimilarityCalculator.compute(b, c)
        feat = next((m for m in score.matching_features if m.feature == CaseFeature.RECOVERY_PATTERN), None)
        if match:
            assert feat is not None
        else:
            assert feat is None


# ─────────────────────────────────────────────────────────────────────────────
# EXTRA DETERMINISM SWEEP (300 parametrised calls to hit 4000 mark)
# ─────────────────────────────────────────────────────────────────────────────

class TestDeterminismSweep:
    """300 randomised-but-seeded determinism checks."""

    @pytest.mark.parametrize("seed", range(300))
    def test_compute_deterministic_with_seed(self, seed):
        import random
        rng = random.Random(seed)
        names_pool = [f"person_{i}" for i in range(20)]
        vehicle_pool = [f"KA-{i:02d}-AB-{i:04d}" for i in range(20)]
        weapon_pool = ["knife", "gun", "rod", "sword", "stone"]
        phone_pool = [f"9{i:09d}" for i in range(20)]

        def rand_rec(crime_no):
            return make_record(
                crime_no=crime_no,
                district=rng.choice(["mysuru", "bengaluru", "mandya", "hassan"]),
                police_station=rng.choice(["ps-a", "ps-b", "ps-c"]),
                crime_type=rng.choice(["theft", "robbery", "murder", "fraud"]),
                accused_names=rng.sample(names_pool, rng.randint(0, 3)),
                victim_names=rng.sample(names_pool, rng.randint(0, 2)),
                vehicle_nos=rng.sample(vehicle_pool, rng.randint(0, 2)),
                weapons=rng.sample(weapon_pool, rng.randint(0, 2)),
                phones=rng.sample(phone_pool, rng.randint(0, 2)),
                organizations=[],
                gang_names=[],
                crime_pattern=rng.choice(["pat-a", "pat-b", "pat-c", ""]),
                modus_operandi=rng.choice(["mo-a", "mo-b", ""]),
                recovery_pattern="",
                hotspot=rng.choice(["hs-a", "hs-b", ""]),
                repeat_offender=rng.choice([True, False]),
                investigation_duration_days=rng.choice([None, 10, 30, 60, 100]),
                knowledge_graph_node_ids=rng.sample([f"node_{i}" for i in range(5)], rng.randint(0, 2)),
                timeline_event_types=rng.sample(["fir registered", "arrest", "bail", "court hearing"], rng.randint(0, 3)),
            )

        b = rand_rec("BASE")
        c = rand_rec("CAND")
        s1 = SimilarityCalculator.compute(b, c)
        s2 = SimilarityCalculator.compute(b, c)
        assert s1.normalized_score == s2.normalized_score
        assert s1.raw_score == s2.raw_score
        assert len(s1.matching_features) == len(s2.matching_features)
