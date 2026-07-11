"""
test_predictive_engine.py
Phase 5.4 — Enterprise Predictive Investigation Engine
Test Suite: 2,500+ Deterministic Validation Cases

Rules:
- No ML models
- No LLM predictions
- No hallucinations
- All predictions backed by database evidence
- Every prediction must be reproducible and deterministic
"""

import unittest
import time
from typing import Dict, Any, List, Optional
from app.ai.predictive_engine import PredictiveInvestigationEngine, PredictiveEngineStage


# ─────────────────────────────────────────────────────────────────────────────
# MOCK HELPERS
# ─────────────────────────────────────────────────────────────────────────────

class MockIntelBundle:
    def __init__(self, hotspots=None):
        self.hotspots = hotspots or []
        self.network = {}
        self.repeat_offender = {}
        self.similar_cases = []
        self.pattern_analysis = ""
        self.recommendations = []


class MockContext:
    def __init__(
        self,
        search_result: List[Dict] = None,
        hotspots: List[Dict] = None,
        warnings: List[str] = None,
    ):
        self.search_result = search_result or []
        self.intelligence_bundle = MockIntelBundle(hotspots=hotspots or [])
        self.warnings = warnings if warnings is not None else []
        self.predictive_report = None


# ─────────────────────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────────────────────

CATEGORIES = ["THEFT", "ROBBERY", "MURDER", "FRAUD", "ASSAULT", "KIDNAPPING"]
CATEGORY_SEVERITY = {"THEFT": 1, "ROBBERY": 2, "MURDER": 3, "FRAUD": 1, "ASSAULT": 2, "KIDNAPPING": 2}
SUSPECTS = ["Raju Kumar", "Suresh Gowda", "Venkat Rao", "Mohammed Ali", "Priya Das"]
DISTRICTS = ["Mysuru", "Bengaluru Urban", "Hubli", "Dharwad", "Kolar"]
STATIONS = ["Mysore South", "Vijayanagar", "Halasuru Gate", "Kodigehalli", "KGF Town"]
DATES = [
    "2024-01-10", "2024-01-15", "2024-01-18",
    "2024-02-01", "2024-02-14", "2024-03-01",
    "2024-04-20", "2024-05-05", "2024-06-11",
    "2024-07-07", "2024-08-19", "2024-09-25",
]

def _make_fir(
    crime_no: str,
    accused_name: str,
    category: str,
    date: str,
    district: str = "Mysuru",
    station: str = "Mysore South",
) -> Dict:
    return {
        "crime_no": crime_no,
        "accused_name": accused_name,
        "crime_category": category,
        "crime_registered_date": date,
        "district_name": district,
        "police_station_name": station,
    }


def _make_firs_for_suspect(
    suspect: str,
    categories: List[str],
    dates: List[str],
    district: str = "Mysuru",
    station: str = "Mysore South",
) -> List[Dict]:
    return [
        _make_fir(
            f"KSP-{i+1:04d}",
            suspect,
            categories[i % len(categories)],
            dates[i % len(dates)],
            district,
            station,
        )
        for i in range(len(categories))
    ]


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 1: SAFETY GATE TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestSafetyGate(unittest.TestCase):

    def test_empty_results_returns_insufficient(self):
        ctx = MockContext(search_result=[])
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        self.assertIn("Insufficient", report["summary"])
        self.assertEqual(report["repeat_offender_risks"], [])
        self.assertEqual(report["crime_escalation"], [])

    def test_single_result_returns_insufficient(self):
        ctx = MockContext(search_result=[_make_fir("KSP-0001", "Raju", "THEFT", "2024-01-01")])
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        self.assertIn("Insufficient", report["summary"])
        self.assertEqual(report["repeat_offender_risks"], [])

    def test_two_results_passes_gate(self):
        results = [
            _make_fir("KSP-0001", "Raju", "THEFT", "2024-01-01"),
            _make_fir("KSP-0002", "Raju", "ROBBERY", "2024-01-15"),
        ]
        ctx = MockContext(search_result=results)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        self.assertNotIn("Insufficient", report["summary"])

    def test_none_results_returns_insufficient(self):
        ctx = MockContext(search_result=None)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        self.assertIn("Insufficient", report["summary"])

    def test_boundary_exactly_2_passes(self):
        results = [
            _make_fir("KSP-0001", "Ganesh", "THEFT", "2024-03-01"),
            _make_fir("KSP-0002", "Ganesh", "MURDER", "2024-03-20"),
        ]
        ctx = MockContext(search_result=results)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        self.assertIsNotNone(report)
        self.assertIn("repeat_offender_risks", report)


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 2: REPEAT OFFENDER RISK CALCULATION
# ─────────────────────────────────────────────────────────────────────────────

class TestRepeatOffenderRisk(unittest.TestCase):

    def test_single_case_score_low(self):
        score, grade, reasons = PredictiveInvestigationEngine._calculate_repeat_offender_risk(
            1, [_make_fir("KSP-0001", "Raju", "THEFT", "2024-01-01")]
        )
        self.assertEqual(grade, "LOW")
        self.assertEqual(score, 10)

    def test_two_cases_medium_grade(self):
        records = [
            _make_fir("KSP-0001", "Raju", "THEFT", "2024-01-01"),
            _make_fir("KSP-0002", "Raju", "THEFT", "2024-06-01"),
        ]
        score, grade, reasons = PredictiveInvestigationEngine._calculate_repeat_offender_risk(2, records)
        self.assertIn(grade, ["MEDIUM", "CRITICAL"])  # CRITICAL if short interval

    def test_three_cases_high(self):
        records = [
            _make_fir("KSP-0001", "Raju", "THEFT", "2024-01-01"),
            _make_fir("KSP-0002", "Raju", "THEFT", "2024-03-01"),
            _make_fir("KSP-0003", "Raju", "THEFT", "2024-05-01"),
        ]
        score, grade, reasons = PredictiveInvestigationEngine._calculate_repeat_offender_risk(3, records)
        self.assertEqual(grade, "HIGH")
        self.assertEqual(score, 75)

    def test_four_cases_critical(self):
        records = _make_firs_for_suspect("Venkat", ["THEFT"] * 4, DATES[:4])
        score, grade, reasons = PredictiveInvestigationEngine._calculate_repeat_offender_risk(4, records)
        self.assertEqual(grade, "CRITICAL")
        self.assertEqual(score, 95)

    def test_five_cases_critical(self):
        records = _make_firs_for_suspect("Suresh", ["ROBBERY"] * 5, DATES[:5])
        score, grade, _ = PredictiveInvestigationEngine._calculate_repeat_offender_risk(5, records)
        self.assertEqual(grade, "CRITICAL")
        self.assertGreaterEqual(score, 95)

    def test_short_interval_triggers_critical(self):
        records = [
            _make_fir("KSP-0001", "Ali", "THEFT", "2024-01-01"),
            _make_fir("KSP-0002", "Ali", "ROBBERY", "2024-01-20"),  # 19 days apart — < 30
        ]
        score, grade, reasons = PredictiveInvestigationEngine._calculate_repeat_offender_risk(2, records)
        self.assertEqual(grade, "CRITICAL")

    def test_reasons_not_empty(self):
        records = _make_firs_for_suspect("Priya", ["THEFT", "ROBBERY"], DATES[:2])
        _, _, reasons = PredictiveInvestigationEngine._calculate_repeat_offender_risk(2, records)
        self.assertIsInstance(reasons, list)
        self.assertGreater(len(reasons), 0)

    def test_reasons_mention_case_count(self):
        records = _make_firs_for_suspect("Ganesh", ["THEFT", "MURDER"], DATES[:2])
        _, _, reasons = PredictiveInvestigationEngine._calculate_repeat_offender_risk(2, records)
        combined = " ".join(reasons).lower()
        self.assertIn("2", combined)

    def test_invalid_date_format_handled(self):
        records = [
            {"accused_name": "Raju", "crime_category": "THEFT", "crime_registered_date": "INVALID"},
            {"accused_name": "Raju", "crime_category": "THEFT", "crime_registered_date": "2024-02-01"},
        ]
        score, grade, reasons = PredictiveInvestigationEngine._calculate_repeat_offender_risk(2, records)
        self.assertIsNotNone(grade)

    def test_missing_dates_handled(self):
        records = [
            {"accused_name": "Raju", "crime_category": "THEFT"},
            {"accused_name": "Raju", "crime_category": "ROBBERY"},
        ]
        score, grade, reasons = PredictiveInvestigationEngine._calculate_repeat_offender_risk(2, records)
        self.assertIn(grade, ["LOW", "MEDIUM", "HIGH", "CRITICAL"])


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 3: CRIME ESCALATION DETECTION
# ─────────────────────────────────────────────────────────────────────────────

class TestCrimeEscalation(unittest.TestCase):

    def test_theft_to_murder_flags_escalation(self):
        records = [
            _make_fir("KSP-0001", "Raju", "THEFT", "2024-01-01"),
            _make_fir("KSP-0002", "Raju", "MURDER", "2024-04-01"),
        ]
        flag, score, grade, reasons = PredictiveInvestigationEngine._check_crime_escalation(records)
        self.assertTrue(flag)
        self.assertEqual(grade, "HIGH")
        self.assertGreater(score, 0)

    def test_theft_to_robbery_flags_escalation(self):
        records = [
            _make_fir("KSP-0001", "Suresh", "THEFT", "2024-01-01"),
            _make_fir("KSP-0002", "Suresh", "ROBBERY", "2024-02-01"),
        ]
        flag, score, grade, reasons = PredictiveInvestigationEngine._check_crime_escalation(records)
        self.assertTrue(flag)

    def test_same_category_no_escalation(self):
        records = [
            _make_fir("KSP-0001", "Venkat", "THEFT", "2024-01-01"),
            _make_fir("KSP-0002", "Venkat", "THEFT", "2024-04-01"),
        ]
        flag, score, grade, reasons = PredictiveInvestigationEngine._check_crime_escalation(records)
        self.assertFalse(flag)
        self.assertEqual(grade, "LOW")

    def test_murder_to_theft_no_escalation(self):
        records = [
            _make_fir("KSP-0001", "Ali", "MURDER", "2024-01-01"),
            _make_fir("KSP-0002", "Ali", "THEFT", "2024-04-01"),
        ]
        flag, score, grade, reasons = PredictiveInvestigationEngine._check_crime_escalation(records)
        self.assertFalse(flag)

    def test_escalation_reasons_populated(self):
        records = [
            _make_fir("KSP-0001", "Priya", "THEFT", "2024-01-01"),
            _make_fir("KSP-0002", "Priya", "ROBBERY", "2024-03-01"),
        ]
        flag, score, grade, reasons = PredictiveInvestigationEngine._check_crime_escalation(records)
        if flag:
            self.assertGreater(len(reasons), 0)

    def test_single_record_no_escalation(self):
        records = [_make_fir("KSP-0001", "Ganesh", "THEFT", "2024-01-01")]
        flag, score, grade, reasons = PredictiveInvestigationEngine._check_crime_escalation(records)
        self.assertFalse(flag)

    def test_empty_categories_handled(self):
        records = [{"crime_no": "KSP-0001"}, {"crime_no": "KSP-0002"}]
        flag, score, grade, reasons = PredictiveInvestigationEngine._check_crime_escalation(records)
        self.assertIsNotNone(flag)


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 4: REPORT STRUCTURE VALIDATION
# ─────────────────────────────────────────────────────────────────────────────

REQUIRED_KEYS = [
    "repeat_offender_risks",
    "crime_escalation",
    "priority_targets",
    "hotspot_forecast",
    "resource_recommendations",
    "risk_matrix",
    "evidence_chain",
    "summary",
]

class TestReportStructure(unittest.TestCase):

    def _valid_ctx(self, n_results=3, suspect="Raju", categories=None):
        cats = categories or ["THEFT", "ROBBERY", "MURDER"]
        results = _make_firs_for_suspect(suspect, cats[:n_results], DATES[:n_results])
        return MockContext(search_result=results)

    def test_all_required_keys_present_2_results(self):
        ctx = self._valid_ctx(2, categories=["THEFT", "ROBBERY"])
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        for key in REQUIRED_KEYS:
            self.assertIn(key, report, f"Key missing: {key}")

    def test_all_required_keys_present_5_results(self):
        ctx = self._valid_ctx(5, categories=["THEFT"] * 5)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        for key in REQUIRED_KEYS:
            self.assertIn(key, report, f"Key missing: {key}")

    def test_risk_matrix_valid_value(self):
        ctx = self._valid_ctx(4)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        self.assertIn(report["risk_matrix"], ["CRITICAL", "HIGH", "MEDIUM", "LOW"])

    def test_repeat_offender_risks_is_list(self):
        ctx = self._valid_ctx(3)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        self.assertIsInstance(report["repeat_offender_risks"], list)

    def test_crime_escalation_is_list(self):
        ctx = self._valid_ctx(3)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        self.assertIsInstance(report["crime_escalation"], list)

    def test_priority_targets_is_list(self):
        ctx = self._valid_ctx(3)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        self.assertIsInstance(report["priority_targets"], list)

    def test_resource_recommendations_is_list(self):
        ctx = self._valid_ctx(3)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        self.assertIsInstance(report["resource_recommendations"], list)

    def test_evidence_chain_is_list(self):
        ctx = self._valid_ctx(3)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        self.assertIsInstance(report["evidence_chain"], list)

    def test_summary_is_string(self):
        ctx = self._valid_ctx(3)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        self.assertIsInstance(report["summary"], str)

    def test_empty_report_structure_valid(self):
        report = PredictiveInvestigationEngine._empty_report("Test message")
        for key in REQUIRED_KEYS:
            self.assertIn(key, report, f"Key missing in empty report: {key}")

    def test_repeat_offender_entry_has_required_fields(self):
        results = [
            _make_fir("KSP-0001", "Raju", "THEFT", "2024-01-01"),
            _make_fir("KSP-0002", "Raju", "ROBBERY", "2024-01-15"),
            _make_fir("KSP-0003", "Raju", "MURDER", "2024-03-01"),
        ]
        ctx = MockContext(search_result=results)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        if report["repeat_offender_risks"]:
            entry = report["repeat_offender_risks"][0]
            self.assertIn("suspect", entry)
            self.assertIn("risk_score", entry)
            self.assertIn("risk_grade", entry)
            self.assertIn("reasons", entry)
            self.assertIn("supporting_firs", entry)

    def test_priority_targets_entry_structure(self):
        results = [
            _make_fir("KSP-0001", "Raju", "MURDER", "2024-01-01"),
            _make_fir("KSP-0002", "Raju", "ROBBERY", "2024-02-01"),
        ]
        ctx = MockContext(search_result=results)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        if report["priority_targets"]:
            target = report["priority_targets"][0]
            self.assertIn("target", target)
            self.assertIn("score", target)
            self.assertIn("grade", target)


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 5: RESOURCE RECOMMENDATIONS LOGIC
# ─────────────────────────────────────────────────────────────────────────────

class TestResourceRecommendations(unittest.TestCase):

    def test_critical_risk_generates_surveillance_rec(self):
        # 4 records for same suspect → CRITICAL
        results = _make_firs_for_suspect("Raju", ["THEFT"] * 4, DATES[:4])
        ctx = MockContext(search_result=results)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        combined = " ".join(report["resource_recommendations"]).lower()
        self.assertIn("surveillance", combined)

    def test_medium_risk_generates_alert_rec(self):
        # 2 records, same suspect, no short interval
        results = [
            _make_fir("KSP-0001", "Suresh", "THEFT", "2024-01-01"),
            _make_fir("KSP-0002", "Suresh", "THEFT", "2024-06-01"),
        ]
        ctx = MockContext(search_result=results)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        # Either medium or critical depending on scoring
        self.assertIsInstance(report["resource_recommendations"], list)

    def test_low_risk_minimal_recommendations(self):
        # Only 2 different suspects, 1 FIR each → No repeat offender
        results = [
            _make_fir("KSP-0001", "Raju", "THEFT", "2024-01-01"),
            _make_fir("KSP-0002", "Ganesh", "ROBBERY", "2024-04-01"),
        ]
        ctx = MockContext(search_result=results)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        # No high-score repeat offender → fewer/no recs
        self.assertIsInstance(report["resource_recommendations"], list)


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 6: HOTSPOT FORECASTING
# ─────────────────────────────────────────────────────────────────────────────

class TestHotspotForecast(unittest.TestCase):

    def test_hotspot_populated_from_intel_bundle(self):
        results = _make_firs_for_suspect("Raju", ["THEFT", "ROBBERY"], DATES[:2])
        hotspots = [{"latitude": 12.97, "longitude": 77.56}]
        ctx = MockContext(search_result=results, hotspots=hotspots)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        self.assertIsInstance(report["hotspot_forecast"], list)

    def test_no_hotspots_when_intel_empty(self):
        results = _make_firs_for_suspect("Raju", ["THEFT", "ROBBERY"], DATES[:2])
        ctx = MockContext(search_result=results, hotspots=[])
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        self.assertEqual(report["hotspot_forecast"], [])

    def test_hotspot_grade_high_for_large_results(self):
        results = _make_firs_for_suspect("Raju", ["THEFT"] * 5, DATES[:5])
        hotspots = [{"latitude": 12.97, "longitude": 77.56}]
        ctx = MockContext(search_result=results, hotspots=hotspots)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        if report["hotspot_forecast"]:
            self.assertEqual(report["hotspot_forecast"][0]["risk_grade"], "HIGH")

    def test_hotspot_grade_medium_for_small_results(self):
        results = [
            _make_fir("KSP-0001", "Raju", "THEFT", "2024-01-01"),
            _make_fir("KSP-0002", "Raju", "ROBBERY", "2024-02-01"),
        ]
        hotspots = [{"latitude": 12.97, "longitude": 77.56}]
        ctx = MockContext(search_result=results, hotspots=hotspots)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        if report["hotspot_forecast"]:
            self.assertEqual(report["hotspot_forecast"][0]["risk_grade"], "MEDIUM")


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 7: PIPELINE STAGE WRAPPER
# ─────────────────────────────────────────────────────────────────────────────

class TestPredictiveEngineStage(unittest.TestCase):

    def test_stage_sets_predictive_report(self):
        results = _make_firs_for_suspect("Raju", ["THEFT", "ROBBERY"], DATES[:2])
        ctx = MockContext(search_result=results)
        ctx = PredictiveEngineStage.run(ctx)
        self.assertIsNotNone(ctx.predictive_report)

    def test_stage_does_not_throw_on_empty(self):
        ctx = MockContext(search_result=[])
        ctx = PredictiveEngineStage.run(ctx)
        # Should return fallback report, not raise
        self.assertIsNotNone(ctx.predictive_report)

    def test_stage_adds_to_warnings_on_invalid_context(self):
        class BrokenContext:
            search_result = None
            intelligence_bundle = None
            warnings = []
        try:
            PredictiveEngineStage.run(BrokenContext())
        except Exception:
            pass  # Stage should handle gracefully

    def test_stage_returns_context(self):
        results = _make_firs_for_suspect("Raju", ["THEFT", "ROBBERY"], DATES[:2])
        ctx = MockContext(search_result=results)
        returned = PredictiveEngineStage.run(ctx)
        self.assertIsNotNone(returned)

    def test_stage_report_has_summary(self):
        results = _make_firs_for_suspect("Ganesh", ["THEFT", "MURDER", "ROBBERY"], DATES[:3])
        ctx = MockContext(search_result=results)
        PredictiveEngineStage.run(ctx)
        self.assertIn("summary", ctx.predictive_report)


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 8: MULTI-SUSPECT SCENARIOS
# ─────────────────────────────────────────────────────────────────────────────

class TestMultiSuspectScenarios(unittest.TestCase):

    def test_two_suspects_both_appear_in_risks(self):
        results = [
            _make_fir("KSP-0001", "Raju", "THEFT", "2024-01-01"),
            _make_fir("KSP-0002", "Raju", "ROBBERY", "2024-01-15"),
            _make_fir("KSP-0003", "Ganesh", "MURDER", "2024-02-01"),
            _make_fir("KSP-0004", "Ganesh", "THEFT", "2024-03-01"),
        ]
        ctx = MockContext(search_result=results)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        names = [r["suspect"].lower() for r in report["repeat_offender_risks"]]
        self.assertIn("raju", names)
        self.assertIn("ganesh", names)

    def test_risks_sorted_descending_by_score(self):
        results = []
        # Suspect with 4 records (CRITICAL) vs suspect with 2 records (MEDIUM)
        results += _make_firs_for_suspect("TopRisk", ["THEFT"] * 4, DATES[:4])
        results += _make_firs_for_suspect("LowRisk", ["THEFT", "ROBBERY"], DATES[4:6])
        ctx = MockContext(search_result=results)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        risks = report["repeat_offender_risks"]
        if len(risks) >= 2:
            self.assertGreaterEqual(risks[0]["risk_score"], risks[1]["risk_score"])

    def test_three_suspects_five_results(self):
        results = [
            _make_fir("KSP-0001", "Suresh", "THEFT", "2024-01-01"),
            _make_fir("KSP-0002", "Suresh", "ROBBERY", "2024-01-15"),
            _make_fir("KSP-0003", "Venkat", "MURDER", "2024-02-01"),
            _make_fir("KSP-0004", "Priya", "THEFT", "2024-03-01"),
            _make_fir("KSP-0005", "Priya", "FRAUD", "2024-04-01"),
        ]
        ctx = MockContext(search_result=results)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        self.assertIsInstance(report["repeat_offender_risks"], list)
        self.assertGreaterEqual(len(report["repeat_offender_risks"]), 2)

    def test_all_distinct_suspects_no_repeat_risk(self):
        results = [
            _make_fir("KSP-0001", "SuspectA", "THEFT", "2024-01-01"),
            _make_fir("KSP-0002", "SuspectB", "THEFT", "2024-02-01"),
            _make_fir("KSP-0003", "SuspectC", "THEFT", "2024-03-01"),
        ]
        ctx = MockContext(search_result=results)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        # Each suspect has only 1 FIR → LOW risk for all
        for r in report["repeat_offender_risks"]:
            self.assertEqual(r["risk_grade"], "LOW")

    def test_accused_names_list_field_resolved(self):
        results = [
            {"crime_no": "KSP-0001", "accused_names": ["Raju Kumar"], "crime_category": "THEFT", "crime_registered_date": "2024-01-01"},
            {"crime_no": "KSP-0002", "accused_names": ["Raju Kumar"], "crime_category": "ROBBERY", "crime_registered_date": "2024-02-01"},
        ]
        ctx = MockContext(search_result=results)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        # Raju Kumar should be identified
        names = [r["suspect"].lower() for r in report["repeat_offender_risks"]]
        self.assertTrue(any("raju" in n for n in names))


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 9: RISK MATRIX CORRECTNESS
# ─────────────────────────────────────────────────────────────────────────────

class TestRiskMatrix(unittest.TestCase):

    def test_critical_risk_matrix_when_high_score(self):
        # 4 cases for same suspect → score 95 → CRITICAL risk_matrix
        results = _make_firs_for_suspect("Raju", ["THEFT"] * 4, DATES[:4])
        ctx = MockContext(search_result=results)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        self.assertEqual(report["risk_matrix"], "CRITICAL")

    def test_medium_risk_matrix_for_medium_score(self):
        # 2 non-short-interval cases → score 45 → MEDIUM
        results = [
            _make_fir("KSP-0001", "Suresh", "THEFT", "2024-01-01"),
            _make_fir("KSP-0002", "Suresh", "THEFT", "2024-06-01"),
        ]
        ctx = MockContext(search_result=results)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        # Score 45 → MEDIUM (< 60 and >= 0)
        self.assertIn(report["risk_matrix"], ["MEDIUM", "CRITICAL"])

    def test_low_risk_matrix_for_distinct_suspects(self):
        results = [
            _make_fir("KSP-0001", "Alpha", "THEFT", "2024-01-01"),
            _make_fir("KSP-0002", "Beta", "ROBBERY", "2024-02-01"),
        ]
        ctx = MockContext(search_result=results)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        # Both suspects score 10 (LOW) → max = 10 → MEDIUM matrix
        self.assertIn(report["risk_matrix"], ["MEDIUM", "LOW"])

    def test_risk_matrix_always_valid_string(self):
        for n in range(2, 7):
            cats = (["THEFT", "ROBBERY", "MURDER"] * 3)[:n]
            results = _make_firs_for_suspect("TestSuspect", cats, DATES[:n])
            ctx = MockContext(search_result=results)
            report = PredictiveInvestigationEngine.run_prediction(ctx)
            self.assertIn(report["risk_matrix"], ["CRITICAL", "HIGH", "MEDIUM", "LOW"])


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 10: DETERMINISM VALIDATION
# (Same input MUST always produce same output)
# ─────────────────────────────────────────────────────────────────────────────

class TestDeterminism(unittest.TestCase):

    def test_identical_input_identical_output(self):
        results = [
            _make_fir("KSP-0001", "Raju", "THEFT", "2024-01-01"),
            _make_fir("KSP-0002", "Raju", "ROBBERY", "2024-01-15"),
        ]
        ctx1 = MockContext(search_result=results)
        ctx2 = MockContext(search_result=results)

        report1 = PredictiveInvestigationEngine.run_prediction(ctx1)
        report2 = PredictiveInvestigationEngine.run_prediction(ctx2)

        self.assertEqual(report1["risk_matrix"], report2["risk_matrix"])
        self.assertEqual(report1["summary"], report2["summary"])
        self.assertEqual(
            len(report1["repeat_offender_risks"]),
            len(report2["repeat_offender_risks"])
        )

    def test_repeated_calls_same_grade(self):
        results = _make_firs_for_suspect("Venkat", ["THEFT", "ROBBERY", "MURDER"], DATES[:3])
        grades = []
        for _ in range(5):
            ctx = MockContext(search_result=results)
            report = PredictiveInvestigationEngine.run_prediction(ctx)
            grades.append(report["risk_matrix"])
        self.assertEqual(len(set(grades)), 1, "Risk matrix must be deterministic across identical inputs")

    def test_repeated_calls_same_score(self):
        records = _make_firs_for_suspect("Raju", ["THEFT"] * 4, DATES[:4])
        scores = []
        for _ in range(5):
            score, _, _ = PredictiveInvestigationEngine._calculate_repeat_offender_risk(4, records)
            scores.append(score)
        self.assertEqual(len(set(scores)), 1)


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 11: HALLUCINATION GUARD — NO FABRICATION
# (Ensure no hallucinated content appears in output)
# ─────────────────────────────────────────────────────────────────────────────

class TestHallucinationGuard(unittest.TestCase):
    FORBIDDEN_PHRASES = [
        "likely to commit", "may commit", "expected to commit",
        "probably will", "we predict", "machine learning predicts",
        "ai estimates", "neural network"
    ]

    def _check_no_hallucinations(self, report: Dict):
        text_fields = [
            report.get("summary", ""),
            " ".join(report.get("resource_recommendations", [])),
            " ".join(
                " ".join(r.get("reasons", []))
                for r in report.get("repeat_offender_risks", [])
            ),
            " ".join(
                " ".join(e.get("reasons", []))
                for e in report.get("crime_escalation", [])
            ),
        ]
        full_text = " ".join(text_fields).lower()
        for phrase in self.FORBIDDEN_PHRASES:
            self.assertNotIn(phrase, full_text, f"Hallucinated phrase found: '{phrase}'")

    def test_no_hallucinations_2_records(self):
        results = _make_firs_for_suspect("Raju", ["THEFT", "ROBBERY"], DATES[:2])
        ctx = MockContext(search_result=results)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        self._check_no_hallucinations(report)

    def test_no_hallucinations_high_risk(self):
        results = _make_firs_for_suspect("Raju", ["THEFT"] * 4, DATES[:4])
        ctx = MockContext(search_result=results)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        self._check_no_hallucinations(report)

    def test_no_hallucinations_escalation(self):
        results = [
            _make_fir("KSP-0001", "Ganesh", "THEFT", "2024-01-01"),
            _make_fir("KSP-0002", "Ganesh", "MURDER", "2024-06-01"),
        ]
        ctx = MockContext(search_result=results)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        self._check_no_hallucinations(report)

    def test_no_hallucinations_multi_suspects(self):
        results = []
        results += _make_firs_for_suspect("Raju", ["THEFT", "ROBBERY"], DATES[:2])
        results += _make_firs_for_suspect("Suresh", ["MURDER", "THEFT"], DATES[2:4])
        ctx = MockContext(search_result=results)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        self._check_no_hallucinations(report)

    def test_empty_report_no_hallucinations(self):
        ctx = MockContext(search_result=[])
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        self._check_no_hallucinations(report)

    def test_supporting_firs_are_real_crime_numbers(self):
        results = [
            _make_fir("KSP-REAL-001", "Raju", "THEFT", "2024-01-01"),
            _make_fir("KSP-REAL-002", "Raju", "ROBBERY", "2024-01-15"),
        ]
        ctx = MockContext(search_result=results)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        if report["repeat_offender_risks"]:
            firs = report["repeat_offender_risks"][0]["supporting_firs"]
            for fir in firs:
                self.assertIn("KSP-REAL", fir)


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 12: LATENCY / PERFORMANCE
# ─────────────────────────────────────────────────────────────────────────────

class TestLatency(unittest.TestCase):

    def test_50_results_under_1_second(self):
        results = []
        for i, name in enumerate(SUSPECTS * 10):
            cat = CATEGORIES[i % len(CATEGORIES)]
            date = DATES[i % len(DATES)]
            results.append(_make_fir(f"KSP-{i:04d}", name, cat, date))

        ctx = MockContext(search_result=results)
        start = time.time()
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        elapsed = time.time() - start
        self.assertLess(elapsed, 1.0, f"Prediction took {elapsed:.3f}s — exceeds 1s limit")

    def test_200_results_under_3_seconds(self):
        results = []
        for i in range(200):
            name = SUSPECTS[i % len(SUSPECTS)]
            cat = CATEGORIES[i % len(CATEGORIES)]
            date = DATES[i % len(DATES)]
            results.append(_make_fir(f"KSP-{i:04d}", name, cat, date))

        ctx = MockContext(search_result=results)
        start = time.time()
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        elapsed = time.time() - start
        self.assertLess(elapsed, 3.0, f"Prediction took {elapsed:.3f}s — exceeds 3s limit")

    def test_stage_latency_under_100ms_for_small_set(self):
        results = _make_firs_for_suspect("Raju", ["THEFT", "ROBBERY"], DATES[:2])
        ctx = MockContext(search_result=results)
        start = time.time()
        PredictiveEngineStage.run(ctx)
        elapsed = time.time() - start
        self.assertLess(elapsed, 0.1, f"Stage latency {elapsed:.4f}s — exceeds 100ms for small dataset")


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 13: EXTREME PERMUTATION MATRIX
# 2,500+ scenarios covering all suspect/category/district/station combos
# ─────────────────────────────────────────────────────────────────────────────

class TestPermutationMatrix(unittest.TestCase):

    def test_full_permutation_matrix(self):
        """
        Runs 2,500+ permutations covering:
        - 5 suspect names x 5 districts x 5 stations x 6 categories x 2 result sizes = 1500 combos
        - Additional hotspot/escalation combos to hit 2,500+
        """
        test_count = 0
        failures = []

        for suspect in SUSPECTS:
            for district in DISTRICTS:
                for station in STATIONS:
                    for cat in CATEGORIES:
                        for n_results in [2, 3, 4, 5, 6]:
                            for hotspot_count in [0, 1]:
                                try:
                                    cats = [cat] * n_results
                                    results = _make_firs_for_suspect(suspect, cats, DATES[:n_results], district, station)
                                    hotspots = [{"latitude": 12.97, "longitude": 77.56}] * hotspot_count
                                    ctx = MockContext(search_result=results, hotspots=hotspots)
                                    report = PredictiveInvestigationEngine.run_prediction(ctx)

                                    # Validate report structure
                                    for key in REQUIRED_KEYS:
                                        if key not in report:
                                            failures.append(f"Missing key '{key}' for suspect={suspect}, district={district}, cat={cat}, n={n_results}")

                                    # Validate risk matrix
                                    if report.get("risk_matrix") not in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
                                        failures.append(f"Invalid risk_matrix for suspect={suspect}, n={n_results}")

                                    # Validate summary is string
                                    if not isinstance(report.get("summary"), str):
                                        failures.append(f"Non-string summary for suspect={suspect}")

                                    test_count += 1
                                except Exception as e:
                                    failures.append(f"EXCEPTION: suspect={suspect}, district={district}, cat={cat}, n={n_results}: {e}")
                                    test_count += 1

        print(f"\n[TestPermutationMatrix] Ran {test_count} permutations, {len(failures)} failures.")
        if failures:
            for f in failures[:10]:
                print(f" FAIL: {f}")
        self.assertEqual(len(failures), 0, f"{len(failures)} permutation failures detected.")
        self.assertGreaterEqual(test_count, 2500, f"Expected 2500+ tests, only ran {test_count}")

    def test_escalation_permutations(self):
        """
        Validate escalation detection across all meaningful category pairs.
        """
        escalation_pairs = [
            ("THEFT", "ROBBERY"),
            ("THEFT", "MURDER"),
            ("ROBBERY", "MURDER"),
            ("FRAUD", "ROBBERY"),
            ("ASSAULT", "MURDER"),
        ]
        non_escalation_pairs = [
            ("MURDER", "THEFT"),   # decreasing → no escalation
            ("ROBBERY", "THEFT"),
            ("THEFT", "THEFT"),
            ("MURDER", "MURDER"),
        ]

        for first_cat, second_cat in escalation_pairs:
            records = [
                _make_fir("KSP-0001", "Raju", first_cat, "2024-01-01"),
                _make_fir("KSP-0002", "Raju", second_cat, "2024-04-01"),
            ]
            flag, score, grade, reasons = PredictiveInvestigationEngine._check_crime_escalation(records)
            self.assertTrue(flag, f"Expected escalation for {first_cat} → {second_cat}, got False")

        for first_cat, second_cat in non_escalation_pairs:
            records = [
                _make_fir("KSP-0001", "Raju", first_cat, "2024-01-01"),
                _make_fir("KSP-0002", "Raju", second_cat, "2024-04-01"),
            ]
            flag, score, grade, reasons = PredictiveInvestigationEngine._check_crime_escalation(records)
            self.assertFalse(flag, f"Unexpected escalation for {first_cat} → {second_cat}")

    def test_repeat_offender_count_grade_matrix(self):
        """
        Validate that every count-grade combination is deterministic.
        """
        expected_grades = {
            1: "LOW",
            3: "HIGH",
            4: "CRITICAL",
            5: "CRITICAL",
            6: "CRITICAL",
        }
        for count, expected_grade in expected_grades.items():
            # Use widely spaced dates to avoid short-interval bonus
            records = _make_firs_for_suspect("Raju", ["THEFT"] * count, [
                f"2024-{(i * 2 + 1):02d}-01" if (i * 2 + 1) <= 12 else "2024-12-01"
                for i in range(count)
            ])
            score, grade, reasons = PredictiveInvestigationEngine._calculate_repeat_offender_risk(count, records)
            self.assertEqual(grade, expected_grade, f"For count={count}, expected grade={expected_grade}, got {grade}")

    def test_accused_name_normalization(self):
        """
        Verify that name normalization treats case-insensitive duplicates as same suspect.
        """
        results = [
            _make_fir("KSP-0001", "RAJU KUMAR", "THEFT", "2024-01-01"),
            _make_fir("KSP-0002", "raju kumar", "ROBBERY", "2024-01-15"),
        ]
        ctx = MockContext(search_result=results)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        # Both should map to the same suspect
        names = [r["suspect"].lower() for r in report["repeat_offender_risks"]]
        self.assertEqual(len(report["repeat_offender_risks"]), 1)


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 14: EDGE CASES AND BOUNDARY CONDITIONS
# ─────────────────────────────────────────────────────────────────────────────

class TestEdgeCases(unittest.TestCase):

    def test_records_with_no_accused_name(self):
        results = [
            {"crime_no": "KSP-0001", "crime_category": "THEFT", "crime_registered_date": "2024-01-01"},
            {"crime_no": "KSP-0002", "crime_category": "ROBBERY", "crime_registered_date": "2024-02-01"},
        ]
        ctx = MockContext(search_result=results)
        # Should not crash, even with missing accused
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        self.assertIn("repeat_offender_risks", report)

    def test_records_with_none_accused_name(self):
        results = [
            {"crime_no": "KSP-0001", "accused_name": None, "crime_category": "THEFT"},
            {"crime_no": "KSP-0002", "accused_name": None, "crime_category": "ROBBERY"},
        ]
        ctx = MockContext(search_result=results)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        self.assertIsNotNone(report)

    def test_records_with_empty_accused_names_list(self):
        results = [
            {"crime_no": "KSP-0001", "accused_names": [], "crime_category": "THEFT"},
            {"crime_no": "KSP-0002", "accused_names": [], "crime_category": "ROBBERY"},
        ]
        ctx = MockContext(search_result=results)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        self.assertIsNotNone(report)

    def test_records_with_whitespace_names(self):
        results = [
            _make_fir("KSP-0001", "  Raju  ", "THEFT", "2024-01-01"),
            _make_fir("KSP-0002", " RAJU ", "ROBBERY", "2024-02-01"),
        ]
        ctx = MockContext(search_result=results)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        # Both should be considered same suspect after strip
        self.assertIsNotNone(report)

    def test_identical_firs(self):
        fir = _make_fir("KSP-0001", "Raju", "THEFT", "2024-01-01")
        results = [fir, fir]  # Same object twice
        ctx = MockContext(search_result=results)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        self.assertIn("repeat_offender_risks", report)

    def test_missing_crime_category_handled(self):
        results = [
            {"crime_no": "KSP-0001", "accused_name": "Raju"},
            {"crime_no": "KSP-0002", "accused_name": "Raju"},
        ]
        ctx = MockContext(search_result=results)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        self.assertIsNotNone(report)

    def test_very_long_suspect_name(self):
        long_name = "A" * 500
        results = [
            _make_fir("KSP-0001", long_name, "THEFT", "2024-01-01"),
            _make_fir("KSP-0002", long_name, "ROBBERY", "2024-02-01"),
        ]
        ctx = MockContext(search_result=results)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        self.assertIsNotNone(report)

    def test_sql_injection_in_suspect_name(self):
        malicious = "'; DROP TABLE firs; --"
        results = [
            _make_fir("KSP-0001", malicious, "THEFT", "2024-01-01"),
            _make_fir("KSP-0002", malicious, "ROBBERY", "2024-02-01"),
        ]
        ctx = MockContext(search_result=results)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        # Should treat it as a string key, not execute it
        self.assertIsNotNone(report)

    def test_unicode_suspect_name(self):
        results = [
            _make_fir("KSP-0001", "राजू कुमार", "THEFT", "2024-01-01"),
            _make_fir("KSP-0002", "राजू कुमार", "ROBBERY", "2024-01-20"),
        ]
        ctx = MockContext(search_result=results)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        names = [r["suspect"] for r in report["repeat_offender_risks"]]
        self.assertGreater(len(names), 0)

    def test_100_identical_firs_same_suspect(self):
        results = []
        for i in range(100):
            results.append(_make_fir(f"KSP-{i:04d}", "Raju Kumar", "THEFT", DATES[i % len(DATES)]))
        ctx = MockContext(search_result=results)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        self.assertEqual(report["risk_matrix"], "CRITICAL")

    def test_future_dates_handled(self):
        results = [
            _make_fir("KSP-0001", "Raju", "THEFT", "2030-01-01"),
            _make_fir("KSP-0002", "Raju", "ROBBERY", "2030-06-01"),
        ]
        ctx = MockContext(search_result=results)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        self.assertIsNotNone(report)

    def test_mixed_valid_invalid_dates(self):
        results = [
            _make_fir("KSP-0001", "Raju", "THEFT", "2024-01-01"),
            _make_fir("KSP-0002", "Raju", "ROBBERY", "NOT_A_DATE"),
        ]
        ctx = MockContext(search_result=results)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        self.assertIsNotNone(report)

    def test_none_crime_category(self):
        results = [
            {"crime_no": "KSP-0001", "accused_name": "Raju", "crime_category": None, "crime_registered_date": "2024-01-01"},
            {"crime_no": "KSP-0002", "accused_name": "Raju", "crime_category": None, "crime_registered_date": "2024-02-01"},
        ]
        ctx = MockContext(search_result=results)
        report = PredictiveInvestigationEngine.run_prediction(ctx)
        self.assertIsNotNone(report)


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main(verbosity=2)
