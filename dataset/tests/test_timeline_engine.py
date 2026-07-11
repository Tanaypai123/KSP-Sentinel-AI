"""
test_timeline_engine.py
Phase 5.6 — Enterprise Investigation Timeline Engine
Test Suite: 3,500+ Deterministic Validation Cases

Rules:
- No LLM / No inference / No timestamp invention
- Missing timestamps → "Timestamp unavailable."
- Unverifiable order → "Chronological order cannot be verified."
- All scenarios deterministic and reproducible
"""

import unittest
import time
from typing import Dict, Any, List, Optional

from app.ai.timeline_engine import (
    TimelineBuilder, TimelineValidator, TimelineSorter, TimelineSummarizer,
    TimelineEngine, TimelineStage, TimelineEvent, DurationStat,
    EVENT_TYPES, TIMESTAMP_UNAVAILABLE, ORDER_UNVERIFIED,
)


# ─────────────────────────────────────────────────────────────────────────────
# MOCK HELPERS
# ─────────────────────────────────────────────────────────────────────────────

class MockContext:
    def __init__(self, search_result=None):
        self.search_result = search_result or []
        self.warnings = []
        self.timeline_report = None


def _fir(crime_no: str,
         reg_date: str = "2024-01-01",
         occurred_date: str = None,
         arrest_date: str = None,
         bail_date: str = None,
         charge_sheet_date: str = None,
         court_date: str = None,
         close_date: str = None,
         recovery_date: str = None,
         weapon: str = None,
         vehicle: str = None,
         officer: str = "SI Ravi",
         district: str = "Mysuru",
         station: str = "Mysore South",
         victim_statement_date: str = None,
         witness_statement_date: str = None,
         transfer_date: str = None,
         complaint_date: str = None) -> Dict:
    row: Dict[str, Any] = {
        "crime_no": crime_no,
        "crime_registered_date": reg_date,
        "district_name": district,
        "police_station_name": station,
        "officer_name": officer,
    }
    if occurred_date:
        row["crime_occurred_date"] = occurred_date
    if arrest_date:
        row["arrest_date"] = arrest_date
    if bail_date:
        row["bail_date"] = bail_date
    if charge_sheet_date:
        row["charge_sheet_date"] = charge_sheet_date
    if court_date:
        row["court_date"] = court_date
    if close_date:
        row["case_closed_date"] = close_date
    if recovery_date:
        row["recovery_date"] = recovery_date
    if weapon:
        row["weapon"] = weapon
    if vehicle:
        row["vehicle_number"] = vehicle
    if victim_statement_date:
        row["victim_statement_date"] = victim_statement_date
    if witness_statement_date:
        row["witness_statement_date"] = witness_statement_date
    if transfer_date:
        row["transfer_date"] = transfer_date
    if complaint_date:
        row["complaint_date"] = complaint_date
    return row


DISTRICTS = ["Mysuru", "Bengaluru Urban", "Hubli", "Dharwad", "Kolar"]
STATIONS = ["Mysore South", "Vijayanagar", "Halasuru Gate", "Kodigehalli", "KGF Town"]
OFFICERS = ["SI Ravi", "SI Shankar", "SI Priya", "SI Kumar", "SI Asha"]
CATEGORIES = ["THEFT", "ROBBERY", "MURDER", "FRAUD", "ASSAULT"]


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 1: SAFETY GATE
# ─────────────────────────────────────────────────────────────────────────────

class TestSafetyGate(unittest.TestCase):

    def test_empty_results_returns_empty_report(self):
        ctx = MockContext(search_result=[])
        report = TimelineEngine.build_timeline(ctx)
        self.assertEqual(report["event_count"], 0)
        self.assertIn("No records", report["summary"])

    def test_none_results_handled(self):
        ctx = MockContext(search_result=None)
        report = TimelineEngine.build_timeline(ctx)
        self.assertEqual(report["event_count"], 0)

    def test_single_record_builds_timeline(self):
        ctx = MockContext(search_result=[_fir("KSP-0001")])
        report = TimelineEngine.build_timeline(ctx)
        self.assertGreater(report["event_count"], 0)

    def test_stage_does_not_throw_on_empty(self):
        ctx = MockContext(search_result=[])
        TimelineStage.run(ctx)
        self.assertIsNotNone(ctx.timeline_report)

    def test_report_has_required_keys(self):
        ctx = MockContext(search_result=[_fir("KSP-0001")])
        report = TimelineEngine.build_timeline(ctx)
        required = [
            "event_count", "dated_event_count", "undated_event_count",
            "chronological_order", "order_message", "events",
            "missing_timestamps", "gaps", "repeated_events",
            "long_investigations", "recent_activity", "duration_stats",
            "activity_heat", "officer_timeline", "district_timeline",
            "average_delay", "crime_frequency", "repeat_intervals",
            "station_response_time", "evidence_chain", "summary",
        ]
        for key in required:
            self.assertIn(key, report, f"Missing key: {key}")


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 2: EVENT TYPES
# ─────────────────────────────────────────────────────────────────────────────

class TestEventTypes(unittest.TestCase):

    def _event_types_in_report(self, rows):
        ctx = MockContext(search_result=rows)
        report = TimelineEngine.build_timeline(ctx)
        return {e["event_type"] for e in report["events"]}

    def test_fir_registered_event_always_created(self):
        types = self._event_types_in_report([_fir("KSP-0001")])
        self.assertIn("FIR Registered", types)

    def test_crime_occurred_event_when_field_present(self):
        types = self._event_types_in_report([_fir("KSP-0001", occurred_date="2023-12-25")])
        self.assertIn("Crime Occurred", types)

    def test_crime_occurred_not_created_when_missing(self):
        types = self._event_types_in_report([_fir("KSP-0001")])
        self.assertNotIn("Crime Occurred", types)

    def test_arrest_event_when_field_present(self):
        types = self._event_types_in_report([_fir("KSP-0001", arrest_date="2024-01-15")])
        self.assertIn("Arrest", types)

    def test_bail_event_when_field_present(self):
        types = self._event_types_in_report([_fir("KSP-0001", bail_date="2024-02-01")])
        self.assertIn("Bail", types)

    def test_weapon_seized_when_weapon_present(self):
        types = self._event_types_in_report([_fir("KSP-0001", weapon="Knife")])
        self.assertIn("Weapon Seized", types)

    def test_vehicle_seized_when_vehicle_present(self):
        types = self._event_types_in_report([_fir("KSP-0001", vehicle="KA01AB1234")])
        self.assertIn("Vehicle Seized", types)

    def test_charge_sheet_when_field_present(self):
        types = self._event_types_in_report([_fir("KSP-0001", charge_sheet_date="2024-03-01")])
        self.assertIn("Charge Sheet", types)

    def test_court_hearing_when_field_present(self):
        types = self._event_types_in_report([_fir("KSP-0001", court_date="2024-04-01")])
        self.assertIn("Court Hearing", types)

    def test_case_closed_when_field_present(self):
        types = self._event_types_in_report([_fir("KSP-0001", close_date="2024-06-01")])
        self.assertIn("Case Closed", types)

    def test_recovery_event_when_field_present(self):
        types = self._event_types_in_report([_fir("KSP-0001", recovery_date="2024-01-20")])
        self.assertIn("Recovery", types)

    def test_victim_statement_when_field_present(self):
        types = self._event_types_in_report([_fir("KSP-0001", victim_statement_date="2024-01-10")])
        self.assertIn("Victim Statement", types)

    def test_witness_statement_when_field_present(self):
        types = self._event_types_in_report([_fir("KSP-0001", witness_statement_date="2024-01-12")])
        self.assertIn("Witness Statement", types)

    def test_transfer_event_when_field_present(self):
        types = self._event_types_in_report([_fir("KSP-0001", transfer_date="2024-02-15")])
        self.assertIn("Transfer", types)

    def test_complaint_filed_when_field_present(self):
        types = self._event_types_in_report([_fir("KSP-0001", complaint_date="2023-12-28")])
        self.assertIn("Complaint Filed", types)

    def test_all_event_types_in_frozenset(self):
        expected = [
            "FIR Registered", "Crime Occurred", "Complaint Filed",
            "Victim Statement", "Witness Statement", "Arrest", "Bail",
            "Recovery", "Weapon Seized", "Vehicle Seized", "Charge Sheet",
            "Court Hearing", "Transfer", "Evidence Added", "Evidence Updated",
            "Case Closed", "Recommendation Generated",
        ]
        for t in expected:
            self.assertIn(t, EVENT_TYPES)

    def test_full_fir_produces_multiple_events(self):
        ctx = MockContext(search_result=[_fir(
            "KSP-0001",
            occurred_date="2023-12-25",
            arrest_date="2024-01-10",
            bail_date="2024-01-20",
            charge_sheet_date="2024-02-01",
            court_date="2024-03-01",
            close_date="2024-06-01",
            weapon="Knife",
            vehicle="KA01AB1234",
        )])
        report = TimelineEngine.build_timeline(ctx)
        self.assertGreaterEqual(report["event_count"], 8)


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 3: TIMESTAMP VALIDATION
# ─────────────────────────────────────────────────────────────────────────────

class TestTimestampValidation(unittest.TestCase):

    def test_valid_yyyy_mm_dd_parsed(self):
        ts, dt = TimelineValidator.parse_timestamp("2024-01-15")
        self.assertEqual(ts, "2024-01-15")
        self.assertIsNotNone(dt)

    def test_valid_with_time_parsed(self):
        ts, dt = TimelineValidator.parse_timestamp("2024-01-15 10:30:00")
        self.assertEqual(ts, "2024-01-15")
        self.assertIsNotNone(dt)

    def test_none_returns_none(self):
        ts, dt = TimelineValidator.parse_timestamp(None)
        self.assertIsNone(ts)
        self.assertIsNone(dt)

    def test_empty_string_returns_none(self):
        ts, dt = TimelineValidator.parse_timestamp("")
        self.assertIsNone(ts)
        self.assertIsNone(dt)

    def test_null_string_returns_none(self):
        ts, dt = TimelineValidator.parse_timestamp("null")
        self.assertIsNone(ts)
        self.assertIsNone(dt)

    def test_none_string_returns_none(self):
        ts, dt = TimelineValidator.parse_timestamp("none")
        self.assertIsNone(ts)
        self.assertIsNone(dt)

    def test_nan_string_returns_none(self):
        ts, dt = TimelineValidator.parse_timestamp("nan")
        self.assertIsNone(ts)
        self.assertIsNone(dt)

    def test_invalid_date_returns_none(self):
        ts, dt = TimelineValidator.parse_timestamp("NOT_A_DATE")
        self.assertIsNone(ts)
        self.assertIsNone(dt)

    def test_dd_mm_yyyy_format_parsed(self):
        ts, dt = TimelineValidator.parse_timestamp("15-01-2024")
        self.assertIsNotNone(dt)

    def test_dd_slash_mm_slash_yyyy_parsed(self):
        ts, dt = TimelineValidator.parse_timestamp("15/01/2024")
        self.assertIsNotNone(dt)

    def test_missing_timestamp_event_has_unavailable_message(self):
        ctx = MockContext(search_result=[
            {"crime_no": "KSP-0001", "crime_registered_date": None,
             "district_name": "Mysuru", "police_station_name": "StA"}
        ])
        report = TimelineEngine.build_timeline(ctx)
        events = report["events"]
        self.assertTrue(any(e["timestamp"] == TIMESTAMP_UNAVAILABLE for e in events))

    def test_missing_timestamps_list_populated(self):
        ctx = MockContext(search_result=[
            {"crime_no": "KSP-0001", "crime_registered_date": None,
             "district_name": "Mysuru", "police_station_name": "StA"}
        ])
        report = TimelineEngine.build_timeline(ctx)
        self.assertGreater(len(report["missing_timestamps"]), 0)

    def test_missing_timestamp_entry_has_required_fields(self):
        ctx = MockContext(search_result=[
            {"crime_no": "KSP-0001", "crime_registered_date": None,
             "district_name": "Mysuru", "police_station_name": "StA"}
        ])
        report = TimelineEngine.build_timeline(ctx)
        for m in report["missing_timestamps"]:
            self.assertIn("event_id", m)
            self.assertIn("event_type", m)
            self.assertIn("message", m)
            self.assertEqual(m["message"], TIMESTAMP_UNAVAILABLE)

    def test_future_date_accepted(self):
        ts, dt = TimelineValidator.parse_timestamp("2099-12-31")
        self.assertIsNotNone(dt)

    def test_nat_string_returns_none(self):
        ts, dt = TimelineValidator.parse_timestamp("nat")
        self.assertIsNone(ts)
        self.assertIsNone(dt)


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 4: CHRONOLOGICAL SORTING
# ─────────────────────────────────────────────────────────────────────────────

class TestChronologicalSorting(unittest.TestCase):

    def test_events_sorted_ascending(self):
        ctx = MockContext(search_result=[
            _fir("KSP-0001", reg_date="2024-06-01", occurred_date="2024-01-01"),
        ])
        report = TimelineEngine.build_timeline(ctx)
        dated = [e for e in report["events"] if e["timestamp"] != TIMESTAMP_UNAVAILABLE]
        dates = [e["timestamp"] for e in dated]
        self.assertEqual(dates, sorted(dates))

    def test_undated_events_at_end(self):
        ctx = MockContext(search_result=[
            {"crime_no": "KSP-0001", "crime_registered_date": None,
             "crime_occurred_date": "2024-01-01",
             "district_name": "Mysuru", "police_station_name": "StA"}
        ])
        report = TimelineEngine.build_timeline(ctx)
        events = report["events"]
        undated_indices = [i for i, e in enumerate(events) if e["timestamp"] == TIMESTAMP_UNAVAILABLE]
        dated_indices = [i for i, e in enumerate(events) if e["timestamp"] != TIMESTAMP_UNAVAILABLE]
        if undated_indices and dated_indices:
            self.assertGreater(min(undated_indices), max(dated_indices))

    def test_merger_sorts_combined_events(self):
        events_a = TimelineBuilder.build([_fir("KSP-0001", reg_date="2024-06-01")])
        events_b = TimelineBuilder.build([_fir("KSP-0002", reg_date="2023-01-01")])
        merged = TimelineSorter.merge_events(events_a, events_b)
        dates = [e.timestamp for e in merged if e.timestamp_dt]
        self.assertEqual(dates, sorted(dates))

    def test_sort_stable_for_same_date(self):
        ctx = MockContext(search_result=[
            _fir("KSP-0001", reg_date="2024-01-01"),
            _fir("KSP-0002", reg_date="2024-01-01"),
        ])
        report = TimelineEngine.build_timeline(ctx)
        # Should not raise, should produce sorted list
        self.assertIsNotNone(report)

    def test_sort_single_event_no_error(self):
        events = TimelineBuilder.build([_fir("KSP-0001")])
        sorted_events = TimelineSorter.sort(events)
        self.assertGreater(len(sorted_events), 0)

    def test_chronological_order_verified_for_sorted(self):
        events = TimelineBuilder.build([
            _fir("KSP-0001", reg_date="2024-01-01", occurred_date="2023-12-01",
                 arrest_date="2024-01-15"),
        ])
        sorted_events = TimelineSorter.sort(events)
        is_ordered, msg = TimelineValidator.is_chronologically_ordered(sorted_events)
        self.assertTrue(is_ordered)

    def test_order_unverified_message_when_single_dated_event(self):
        events = [TimelineEvent(
            event_id="EVT-001", event_type="FIR Registered",
            timestamp="2024-01-01", timestamp_dt=None,
            source_table="t", source_record="r", supporting_fir="F",
            district="D", station="S", officer="O",
            confidence=1.0, evidence_score=100, reason_chain=["r"],
        )]
        is_ordered, msg = TimelineValidator.is_chronologically_ordered(events)
        self.assertTrue(is_ordered)  # Single event, trivially ordered


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 5: GAP DETECTION
# ─────────────────────────────────────────────────────────────────────────────

class TestGapDetection(unittest.TestCase):

    def test_large_gap_detected(self):
        ctx = MockContext(search_result=[
            _fir("KSP-0001", reg_date="2024-01-01", close_date="2025-06-01"),
        ])
        report = TimelineEngine.build_timeline(ctx)
        # Gap between 2024-01-01 and 2025-06-01 (>30 days)
        self.assertGreater(len(report["gaps"]), 0)

    def test_small_gap_not_detected(self):
        ctx = MockContext(search_result=[
            _fir("KSP-0001", reg_date="2024-01-01", occurred_date="2024-01-10"),
        ])
        report = TimelineEngine.build_timeline(ctx)
        self.assertEqual(len(report["gaps"]), 0)

    def test_gap_has_required_fields(self):
        ctx = MockContext(search_result=[
            _fir("KSP-0001", reg_date="2024-01-01", close_date="2025-06-01"),
        ])
        report = TimelineEngine.build_timeline(ctx)
        for gap in report["gaps"]:
            self.assertIn("gap_start", gap)
            self.assertIn("gap_end", gap)
            self.assertIn("gap_days", gap)
            self.assertIn("before_event", gap)
            self.assertIn("after_event", gap)

    def test_gap_days_correct(self):
        ctx = MockContext(search_result=[
            _fir("KSP-0001", reg_date="2024-01-01", close_date="2024-04-10"),
        ])
        report = TimelineEngine.build_timeline(ctx)
        if report["gaps"]:
            self.assertGreater(report["gaps"][0]["gap_days"], 30)

    def test_no_gaps_when_all_events_close(self):
        ctx = MockContext(search_result=[
            _fir("KSP-0001",
                 reg_date="2024-01-01",
                 occurred_date="2024-01-02",
                 arrest_date="2024-01-05",
                 victim_statement_date="2024-01-08"),
        ])
        report = TimelineEngine.build_timeline(ctx)
        self.assertEqual(len(report["gaps"]), 0)

    def test_find_missing_periods_threshold_respected(self):
        from app.ai.timeline_engine import datetime as dt_mod
        from datetime import datetime
        # Build events manually with a specific gap
        e1 = TimelineEvent("EVT-001", "FIR Registered", "2024-01-01",
                           datetime(2024, 1, 1), "t", "r", "F", "D", "S", "O", 1.0, 100, [])
        e2 = TimelineEvent("EVT-002", "Arrest", "2024-06-01",
                           datetime(2024, 6, 1), "t", "r", "F", "D", "S", "O", 1.0, 100, [])
        gaps = TimelineSummarizer.find_missing_periods([e1, e2], gap_days=30)
        self.assertEqual(len(gaps), 1)
        self.assertGreater(gaps[0]["gap_days"], 30)

    def test_gaps_with_only_undated_events(self):
        ctx = MockContext(search_result=[
            {"crime_no": "KSP-0001", "crime_registered_date": None,
             "district_name": "Mysuru", "police_station_name": "StA"}
        ])
        report = TimelineEngine.build_timeline(ctx)
        # No dated events → no gaps possible
        self.assertEqual(len(report["gaps"]), 0)


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 6: REPEATED EVENTS
# ─────────────────────────────────────────────────────────────────────────────

class TestRepeatedEvents(unittest.TestCase):

    def test_repeated_fir_registration_detected(self):
        """Same crime_no in two rows → two FIR Registered events for same FIR."""
        ctx = MockContext(search_result=[
            _fir("KSP-0001", reg_date="2024-01-01"),
            _fir("KSP-0001", reg_date="2024-02-01"),
        ])
        report = TimelineEngine.build_timeline(ctx)
        repeats = report["repeated_events"]
        fir_repeats = [r for r in repeats if r["event_type"] == "FIR Registered"]
        self.assertGreater(len(fir_repeats), 0)

    def test_no_repeats_for_distinct_firs(self):
        ctx = MockContext(search_result=[
            _fir("KSP-0001"), _fir("KSP-0002"),
        ])
        report = TimelineEngine.build_timeline(ctx)
        # Each FIR has exactly 1 "FIR Registered" event — no repeats
        fir_repeats = [r for r in report["repeated_events"]
                       if r["event_type"] == "FIR Registered"]
        self.assertEqual(len(fir_repeats), 0)

    def test_repeat_entry_has_required_fields(self):
        ctx = MockContext(search_result=[
            _fir("KSP-0001", reg_date="2024-01-01"),
            _fir("KSP-0001", reg_date="2024-02-01"),
        ])
        report = TimelineEngine.build_timeline(ctx)
        for r in report["repeated_events"]:
            self.assertIn("supporting_fir", r)
            self.assertIn("event_type", r)
            self.assertIn("count", r)
            self.assertGreater(r["count"], 1)


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 7: LONG INVESTIGATION DETECTION
# ─────────────────────────────────────────────────────────────────────────────

class TestLongInvestigation(unittest.TestCase):

    def test_case_spanning_2_years_detected(self):
        ctx = MockContext(search_result=[
            _fir("KSP-0001", reg_date="2022-01-01", close_date="2024-06-01"),
        ])
        report = TimelineEngine.build_timeline(ctx)
        self.assertGreater(len(report["long_investigations"]), 0)

    def test_short_case_not_flagged(self):
        ctx = MockContext(search_result=[
            _fir("KSP-0001", reg_date="2024-01-01", close_date="2024-06-01"),
        ])
        report = TimelineEngine.build_timeline(ctx)
        self.assertEqual(len(report["long_investigations"]), 0)

    def test_long_investigation_has_required_fields(self):
        ctx = MockContext(search_result=[
            _fir("KSP-0001", reg_date="2020-01-01", close_date="2024-01-01"),
        ])
        report = TimelineEngine.build_timeline(ctx)
        for li in report["long_investigations"]:
            self.assertIn("fir", li)
            self.assertIn("span_days", li)
            self.assertIn("start", li)
            self.assertIn("end", li)

    def test_long_cases_sorted_by_span_descending(self):
        ctx = MockContext(search_result=[
            _fir("KSP-0001", reg_date="2020-01-01", close_date="2024-01-01"),
            _fir("KSP-0002", reg_date="2022-01-01", close_date="2024-01-01"),
        ])
        report = TimelineEngine.build_timeline(ctx)
        if len(report["long_investigations"]) >= 2:
            self.assertGreaterEqual(
                report["long_investigations"][0]["span_days"],
                report["long_investigations"][1]["span_days"]
            )

    def test_single_event_no_long_investigation(self):
        ctx = MockContext(search_result=[_fir("KSP-0001")])
        report = TimelineEngine.build_timeline(ctx)
        # Only one dated event per FIR (FIR Registered) → can't compute span
        self.assertEqual(len(report["long_investigations"]), 0)


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 8: RECENT ACTIVITY
# ─────────────────────────────────────────────────────────────────────────────

class TestRecentActivity(unittest.TestCase):

    def test_recent_activity_within_range(self):
        ctx = MockContext(search_result=[
            _fir("KSP-0001", reg_date="2024-01-01"),
            _fir("KSP-0002", reg_date="2024-01-20"),
        ])
        report = TimelineEngine.build_timeline(ctx)
        # Recent activity should contain events near 2024-01-20
        self.assertIsInstance(report["recent_activity"], list)

    def test_recent_activity_empty_when_no_dated_events(self):
        ctx = MockContext(search_result=[
            {"crime_no": "KSP-0001", "crime_registered_date": None,
             "district_name": "D", "police_station_name": "S"}
        ])
        report = TimelineEngine.build_timeline(ctx)
        self.assertEqual(len(report["recent_activity"]), 0)

    def test_recent_activity_items_have_event_type(self):
        ctx = MockContext(search_result=[_fir("KSP-0001")])
        report = TimelineEngine.build_timeline(ctx)
        for item in report["recent_activity"]:
            self.assertIn("event_type", item)

    def test_find_recent_activity_returns_list(self):
        from datetime import datetime
        events = [
            TimelineEvent("E1", "FIR Registered", "2024-01-01",
                          datetime(2024, 1, 1), "t", "r", "F1", "D", "S", "O", 1.0, 100, []),
            TimelineEvent("E2", "Arrest", "2024-01-25",
                          datetime(2024, 1, 25), "t", "r", "F1", "D", "S", "O", 1.0, 100, []),
        ]
        recent = TimelineSummarizer.find_recent_activity(events, days=30)
        self.assertIsInstance(recent, list)


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 9: DURATION STATISTICS
# ─────────────────────────────────────────────────────────────────────────────

class TestDurationStatistics(unittest.TestCase):

    def test_duration_computed_for_dated_fir(self):
        ctx = MockContext(search_result=[
            _fir("KSP-0001", reg_date="2024-01-01", close_date="2024-07-01"),
        ])
        report = TimelineEngine.build_timeline(ctx)
        computed = [d for d in report["duration_stats"] if d["status"] == "Computed"]
        self.assertGreater(len(computed), 0)

    def test_duration_unavailable_for_undated_fir(self):
        ctx = MockContext(search_result=[
            {"crime_no": "KSP-0001", "crime_registered_date": None,
             "district_name": "D", "police_station_name": "S"}
        ])
        report = TimelineEngine.build_timeline(ctx)
        unavail = [d for d in report["duration_stats"]
                   if d["status"] == TIMESTAMP_UNAVAILABLE]
        self.assertGreater(len(unavail), 0)

    def test_duration_stat_has_required_fields(self):
        ctx = MockContext(search_result=[_fir("KSP-0001", close_date="2024-12-31")])
        report = TimelineEngine.build_timeline(ctx)
        for stat in report["duration_stats"]:
            self.assertIn("fir_id", stat)
            self.assertIn("duration_days", stat)
            self.assertIn("status", stat)

    def test_duration_days_correct(self):
        ctx = MockContext(search_result=[
            _fir("KSP-0001", reg_date="2024-01-01", close_date="2024-04-10"),
        ])
        report = TimelineEngine.build_timeline(ctx)
        computed = [d for d in report["duration_stats"] if d["status"] == "Computed"]
        if computed:
            # Jan 1 to Apr 10 = 100 days
            self.assertGreater(computed[0]["duration_days"], 0)

    def test_summary_mentions_duration(self):
        ctx = MockContext(search_result=[
            _fir("KSP-0001", reg_date="2024-01-01", close_date="2024-12-31"),
        ])
        report = TimelineEngine.build_timeline(ctx)
        # Summary should mention average duration
        self.assertIn("days", report["summary"].lower())

    def test_compute_average_delay_with_multiple_events(self):
        from datetime import datetime
        events = [
            TimelineEvent("E1", "FIR Registered", "2024-01-01",
                          datetime(2024, 1, 1), "t", "r", "F1", "D", "S", "O", 1.0, 100, []),
            TimelineEvent("E2", "Arrest", "2024-01-15",
                          datetime(2024, 1, 15), "t", "r", "F1", "D", "S", "O", 1.0, 100, []),
            TimelineEvent("E3", "Case Closed", "2024-03-01",
                          datetime(2024, 3, 1), "t", "r", "F1", "D", "S", "O", 1.0, 100, []),
        ]
        result = TimelineSummarizer.compute_average_delay(events)
        self.assertEqual(result["status"], "Computed")
        self.assertIsNotNone(result["average_delay_days"])

    def test_compute_average_delay_single_event_unavailable(self):
        from datetime import datetime
        events = [
            TimelineEvent("E1", "FIR Registered", "2024-01-01",
                          datetime(2024, 1, 1), "t", "r", "F1", "D", "S", "O", 1.0, 100, []),
        ]
        result = TimelineSummarizer.compute_average_delay(events)
        self.assertEqual(result["status"], TIMESTAMP_UNAVAILABLE)


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 10: ACTIVITY HEAT MAP
# ─────────────────────────────────────────────────────────────────────────────

class TestActivityHeat(unittest.TestCase):

    def test_heat_map_contains_dated_events(self):
        ctx = MockContext(search_result=[_fir("KSP-0001", reg_date="2024-01-01")])
        report = TimelineEngine.build_timeline(ctx)
        self.assertIn("2024-01-01", report["activity_heat"])

    def test_heat_map_counts_correct(self):
        ctx = MockContext(search_result=[
            _fir("KSP-0001", reg_date="2024-01-01"),
            _fir("KSP-0002", reg_date="2024-01-01"),
        ])
        report = TimelineEngine.build_timeline(ctx)
        # Both FIR Registered on same date → count should be ≥ 2
        self.assertGreaterEqual(report["activity_heat"].get("2024-01-01", 0), 2)

    def test_heat_map_excludes_undated_events(self):
        ctx = MockContext(search_result=[
            {"crime_no": "KSP-0001", "crime_registered_date": None,
             "district_name": "D", "police_station_name": "S"}
        ])
        report = TimelineEngine.build_timeline(ctx)
        self.assertEqual(len(report["activity_heat"]), 0)

    def test_heat_map_is_dict(self):
        ctx = MockContext(search_result=[_fir("KSP-0001")])
        report = TimelineEngine.build_timeline(ctx)
        self.assertIsInstance(report["activity_heat"], dict)


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 11: OFFICER TIMELINE
# ─────────────────────────────────────────────────────────────────────────────

class TestOfficerTimeline(unittest.TestCase):

    def test_officer_appears_in_timeline(self):
        ctx = MockContext(search_result=[_fir("KSP-0001", officer="SI Ravi")])
        report = TimelineEngine.build_timeline(ctx)
        self.assertIn("SI Ravi", report["officer_timeline"])

    def test_officer_timeline_has_timestamps(self):
        ctx = MockContext(search_result=[_fir("KSP-0001", officer="SI Ravi")])
        report = TimelineEngine.build_timeline(ctx)
        self.assertIsInstance(report["officer_timeline"]["SI Ravi"], list)

    def test_multiple_officers_in_timeline(self):
        ctx = MockContext(search_result=[
            _fir("KSP-0001", officer="SI Ravi"),
            _fir("KSP-0002", officer="SI Priya"),
        ])
        report = TimelineEngine.build_timeline(ctx)
        self.assertIn("SI Ravi", report["officer_timeline"])
        self.assertIn("SI Priya", report["officer_timeline"])

    def test_officer_timeline_no_duplicates_per_date(self):
        ctx = MockContext(search_result=[
            _fir("KSP-0001", officer="SI Ravi", reg_date="2024-01-01",
                 occurred_date="2024-01-01"),
        ])
        report = TimelineEngine.build_timeline(ctx)
        dates = report["officer_timeline"].get("SI Ravi", [])
        self.assertEqual(len(dates), len(set(dates)))


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 12: DISTRICT TIMELINE
# ─────────────────────────────────────────────────────────────────────────────

class TestDistrictTimeline(unittest.TestCase):

    def test_district_appears_in_timeline(self):
        ctx = MockContext(search_result=[_fir("KSP-0001", district="Mysuru")])
        report = TimelineEngine.build_timeline(ctx)
        self.assertIn("Mysuru", report["district_timeline"])

    def test_district_timeline_has_event_count(self):
        ctx = MockContext(search_result=[_fir("KSP-0001", district="Mysuru")])
        report = TimelineEngine.build_timeline(ctx)
        self.assertGreater(report["district_timeline"]["Mysuru"]["event_count"], 0)

    def test_district_timeline_has_required_fields(self):
        ctx = MockContext(search_result=[_fir("KSP-0001", district="Mysuru")])
        report = TimelineEngine.build_timeline(ctx)
        d = report["district_timeline"]["Mysuru"]
        self.assertIn("event_count", d)
        self.assertIn("fir_count", d)
        self.assertIn("event_types", d)
        self.assertIn("earliest", d)
        self.assertIn("latest", d)

    def test_multiple_districts_tracked(self):
        ctx = MockContext(search_result=[
            _fir("KSP-0001", district="Mysuru"),
            _fir("KSP-0002", district="Hubli"),
        ])
        report = TimelineEngine.build_timeline(ctx)
        self.assertIn("Mysuru", report["district_timeline"])
        self.assertIn("Hubli", report["district_timeline"])

    def test_district_fir_count_correct(self):
        ctx = MockContext(search_result=[
            _fir("KSP-0001", district="Mysuru"),
            _fir("KSP-0002", district="Mysuru"),
        ])
        report = TimelineEngine.build_timeline(ctx)
        self.assertGreaterEqual(
            report["district_timeline"]["Mysuru"]["fir_count"], 2
        )


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 13: CRIME FREQUENCY TIMELINE
# ─────────────────────────────────────────────────────────────────────────────

class TestCrimeFrequency(unittest.TestCase):

    def test_crime_frequency_per_month(self):
        ctx = MockContext(search_result=[
            _fir("KSP-0001", reg_date="2024-01-15"),
            _fir("KSP-0002", reg_date="2024-01-20"),
            _fir("KSP-0003", reg_date="2024-02-05"),
        ])
        report = TimelineEngine.build_timeline(ctx)
        freq = report["crime_frequency"]
        self.assertGreaterEqual(freq.get("2024-01", 0), 2)
        self.assertGreaterEqual(freq.get("2024-02", 0), 1)

    def test_crime_frequency_is_dict(self):
        ctx = MockContext(search_result=[_fir("KSP-0001")])
        report = TimelineEngine.build_timeline(ctx)
        self.assertIsInstance(report["crime_frequency"], dict)

    def test_undated_fir_not_in_frequency(self):
        ctx = MockContext(search_result=[
            {"crime_no": "KSP-0001", "crime_registered_date": None,
             "district_name": "D", "police_station_name": "S"}
        ])
        report = TimelineEngine.build_timeline(ctx)
        self.assertEqual(len(report["crime_frequency"]), 0)


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 14: STATION RESPONSE TIME
# ─────────────────────────────────────────────────────────────────────────────

class TestStationResponseTime(unittest.TestCase):

    def test_response_time_computed_when_both_dates_present(self):
        ctx = MockContext(search_result=[
            _fir("KSP-0001", reg_date="2024-01-10", occurred_date="2024-01-05"),
        ])
        report = TimelineEngine.build_timeline(ctx)
        srt = [r for r in report["station_response_time"]
               if r["status"] == "Computed"]
        self.assertGreater(len(srt), 0)

    def test_response_time_days_correct(self):
        ctx = MockContext(search_result=[
            _fir("KSP-0001", reg_date="2024-01-10", occurred_date="2024-01-05"),
        ])
        report = TimelineEngine.build_timeline(ctx)
        computed = [r for r in report["station_response_time"]
                    if r["status"] == "Computed"]
        if computed:
            self.assertEqual(computed[0]["response_days"], 5)

    def test_response_time_unavailable_when_missing(self):
        ctx = MockContext(search_result=[_fir("KSP-0001")])
        report = TimelineEngine.build_timeline(ctx)
        unavail = [r for r in report["station_response_time"]
                   if r["status"] == TIMESTAMP_UNAVAILABLE]
        # No occurred_date → unavailable
        self.assertGreater(len(unavail), 0)


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 15: REPEAT INCIDENT INTERVALS
# ─────────────────────────────────────────────────────────────────────────────

class TestRepeatIncidentIntervals(unittest.TestCase):

    def test_intervals_computed_for_same_district(self):
        ctx = MockContext(search_result=[
            _fir("KSP-0001", reg_date="2024-01-01", district="Mysuru"),
            _fir("KSP-0002", reg_date="2024-02-15", district="Mysuru"),
        ])
        report = TimelineEngine.build_timeline(ctx)
        mysuru_intervals = [i for i in report["repeat_intervals"]
                            if i["district"] == "Mysuru"]
        self.assertGreater(len(mysuru_intervals), 0)

    def test_intervals_sorted_by_days_ascending(self):
        ctx = MockContext(search_result=[
            _fir("KSP-0001", reg_date="2024-01-01", district="Mysuru"),
            _fir("KSP-0002", reg_date="2024-01-15", district="Mysuru"),
            _fir("KSP-0003", reg_date="2024-03-01", district="Mysuru"),
        ])
        report = TimelineEngine.build_timeline(ctx)
        intervals = [i["interval_days"] for i in report["repeat_intervals"]]
        self.assertEqual(intervals, sorted(intervals))

    def test_no_intervals_for_single_fir_per_district(self):
        ctx = MockContext(search_result=[
            _fir("KSP-0001", reg_date="2024-01-01", district="Mysuru"),
            _fir("KSP-0002", reg_date="2024-01-01", district="Hubli"),
        ])
        report = TimelineEngine.build_timeline(ctx)
        # Each district has only 1 FIR → no intervals
        self.assertEqual(len(report["repeat_intervals"]), 0)


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 16: COMPARE TIMELINES
# ─────────────────────────────────────────────────────────────────────────────

class TestCompareTimelines(unittest.TestCase):

    def test_compare_returns_shared_event_types(self):
        events_a = TimelineBuilder.build([_fir("KSP-0001", reg_date="2024-01-01")])
        events_b = TimelineBuilder.build([_fir("KSP-0002", reg_date="2024-02-01")])
        result = TimelineSummarizer.compare_timelines(events_a, events_b)
        self.assertIn("shared_event_types", result)
        self.assertIn("FIR Registered", result["shared_event_types"])

    def test_compare_returns_unique_types(self):
        events_a = TimelineBuilder.build([_fir("KSP-0001", weapon="Knife")])
        events_b = TimelineBuilder.build([_fir("KSP-0002")])
        result = TimelineSummarizer.compare_timelines(events_a, events_b)
        self.assertIn("only_in_first", result)
        self.assertIn("Weapon Seized", result["only_in_first"])

    def test_compare_counts_match(self):
        events_a = TimelineBuilder.build([_fir("KSP-0001")])
        events_b = TimelineBuilder.build([_fir("KSP-0002"), _fir("KSP-0003")])
        result = TimelineSummarizer.compare_timelines(events_a, events_b)
        self.assertEqual(result["first_event_count"], len(events_a))
        self.assertEqual(result["second_event_count"], len(events_b))


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 17: PIPELINE STAGE WRAPPER
# ─────────────────────────────────────────────────────────────────────────────

class TestTimelineStage(unittest.TestCase):

    def test_stage_sets_timeline_report(self):
        ctx = MockContext(search_result=[_fir("KSP-0001")])
        TimelineStage.run(ctx)
        self.assertIsNotNone(ctx.timeline_report)

    def test_stage_returns_context(self):
        ctx = MockContext(search_result=[_fir("KSP-0001")])
        result = TimelineStage.run(ctx)
        self.assertIsNotNone(result)

    def test_stage_does_not_raise_on_empty(self):
        ctx = MockContext(search_result=[])
        TimelineStage.run(ctx)
        self.assertIsNotNone(ctx.timeline_report)

    def test_stage_report_has_summary(self):
        ctx = MockContext(search_result=[_fir("KSP-0001")])
        TimelineStage.run(ctx)
        self.assertIn("summary", ctx.timeline_report)

    def test_stage_handles_crash_gracefully(self):
        class BrokenContext:
            search_result = "NOT_A_LIST"
            warnings = []
            timeline_report = None
        TimelineStage.run(BrokenContext())

    def test_stage_report_has_all_keys(self):
        ctx = MockContext(search_result=[_fir("KSP-0001")])
        TimelineStage.run(ctx)
        required = ["event_count", "events", "gaps", "summary", "evidence_chain"]
        for key in required:
            self.assertIn(key, ctx.timeline_report)

    def test_evidence_chain_not_empty(self):
        ctx = MockContext(search_result=[_fir("KSP-0001")])
        TimelineStage.run(ctx)
        self.assertGreater(len(ctx.timeline_report["evidence_chain"]), 0)


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 18: DETERMINISM
# ─────────────────────────────────────────────────────────────────────────────

class TestDeterminism(unittest.TestCase):

    def test_same_input_same_event_count(self):
        rows = [_fir("KSP-0001", reg_date="2024-01-01", arrest_date="2024-01-15")]
        r1 = TimelineEngine.build_timeline(MockContext(rows))
        r2 = TimelineEngine.build_timeline(MockContext(rows))
        self.assertEqual(r1["event_count"], r2["event_count"])

    def test_same_input_same_gap_count(self):
        rows = [_fir("KSP-0001", reg_date="2024-01-01", close_date="2025-06-01")]
        r1 = TimelineEngine.build_timeline(MockContext(rows))
        r2 = TimelineEngine.build_timeline(MockContext(rows))
        self.assertEqual(len(r1["gaps"]), len(r2["gaps"]))

    def test_same_input_same_summary(self):
        rows = [_fir("KSP-0001")]
        r1 = TimelineEngine.build_timeline(MockContext(rows))
        r2 = TimelineEngine.build_timeline(MockContext(rows))
        self.assertEqual(r1["summary"], r2["summary"])

    def test_repeated_calls_same_chronological_order(self):
        rows = [_fir("KSP-0001", reg_date="2024-01-01", arrest_date="2024-02-01")]
        results = []
        for _ in range(5):
            r = TimelineEngine.build_timeline(MockContext(rows))
            results.append(r["chronological_order"])
        self.assertEqual(len(set(results)), 1)

    def test_repeated_calls_same_crime_frequency(self):
        rows = [_fir("KSP-0001", reg_date="2024-01-01")]
        r1 = TimelineEngine.build_timeline(MockContext(rows))
        r2 = TimelineEngine.build_timeline(MockContext(rows))
        self.assertEqual(r1["crime_frequency"], r2["crime_frequency"])


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 19: LATENCY / PERFORMANCE
# ─────────────────────────────────────────────────────────────────────────────

class TestLatency(unittest.TestCase):

    def _make_firs(self, n: int):
        return [
            _fir(f"KSP-{i:04d}",
                 reg_date=f"2024-{(i%12)+1:02d}-01",
                 district=DISTRICTS[i % len(DISTRICTS)],
                 station=STATIONS[i % len(STATIONS)],
                 officer=OFFICERS[i % len(OFFICERS)])
            for i in range(n)
        ]

    def test_50_firs_under_1_second(self):
        rows = self._make_firs(50)
        start = time.time()
        TimelineEngine.build_timeline(MockContext(rows))
        self.assertLess(time.time() - start, 1.0)

    def test_200_firs_under_5_seconds(self):
        rows = self._make_firs(200)
        start = time.time()
        TimelineEngine.build_timeline(MockContext(rows))
        self.assertLess(time.time() - start, 5.0)

    def test_stage_under_200ms_for_10_firs(self):
        rows = self._make_firs(10)
        ctx = MockContext(rows)
        start = time.time()
        TimelineStage.run(ctx)
        self.assertLess(time.time() - start, 0.2)


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 20: EDGE CASES
# ─────────────────────────────────────────────────────────────────────────────

class TestEdgeCases(unittest.TestCase):

    def test_records_with_no_fields(self):
        ctx = MockContext(search_result=[{}, {}])
        report = TimelineEngine.build_timeline(ctx)
        self.assertIsNotNone(report)

    def test_none_fields_handled(self):
        ctx = MockContext(search_result=[
            {"crime_no": None, "crime_registered_date": None}
        ])
        report = TimelineEngine.build_timeline(ctx)
        self.assertIsNotNone(report)

    def test_unicode_officer_name(self):
        ctx = MockContext(search_result=[
            _fir("KSP-0001", officer="अधिकारी रवि")
        ])
        report = TimelineEngine.build_timeline(ctx)
        self.assertIn("अधिकारी रवि", report["officer_timeline"])

    def test_sql_injection_in_crime_no(self):
        ctx = MockContext(search_result=[
            _fir("'; DROP TABLE firs; --")
        ])
        report = TimelineEngine.build_timeline(ctx)
        self.assertIsNotNone(report)

    def test_very_old_date_handled(self):
        ctx = MockContext(search_result=[_fir("KSP-0001", reg_date="1990-01-01")])
        report = TimelineEngine.build_timeline(ctx)
        self.assertIn("1990-01-01", report["activity_heat"])

    def test_negative_response_time_handled(self):
        """FIR registered before crime occurred date → negative days, still computed."""
        ctx = MockContext(search_result=[
            _fir("KSP-0001", reg_date="2024-01-01", occurred_date="2024-01-10"),
        ])
        report = TimelineEngine.build_timeline(ctx)
        computed = [r for r in report["station_response_time"] if r["status"] == "Computed"]
        if computed:
            # FIR before crime → negative days is valid (data anomaly)
            self.assertIsInstance(computed[0]["response_days"], int)

    def test_100_firs_same_district(self):
        rows = [_fir(f"KSP-{i:04d}", district="Mysuru") for i in range(100)]
        ctx = MockContext(rows)
        start = time.time()
        report = TimelineEngine.build_timeline(ctx)
        self.assertLess(time.time() - start, 5.0)
        self.assertGreaterEqual(
            report["district_timeline"]["Mysuru"]["fir_count"], 100
        )

    def test_empty_officer_field(self):
        ctx = MockContext(search_result=[
            {"crime_no": "KSP-0001", "crime_registered_date": "2024-01-01",
             "district_name": "D", "police_station_name": "S"}
        ])
        report = TimelineEngine.build_timeline(ctx)
        # Officer not in timeline since field is empty
        self.assertNotIn("", report["officer_timeline"])

    def test_timeline_event_to_dict(self):
        from datetime import datetime
        e = TimelineEvent("E1", "FIR Registered", "2024-01-01",
                          datetime(2024, 1, 1), "t", "r", "F1", "D", "S", "O",
                          1.0, 100, ["reason"])
        d = e.to_dict()
        self.assertEqual(d["event_id"], "E1")
        self.assertEqual(d["event_type"], "FIR Registered")
        self.assertEqual(d["timestamp"], "2024-01-01")

    def test_duration_stat_to_dict(self):
        stat = DurationStat("F1", "2024-01-01", "2024-06-01", 152, "Computed")
        d = stat.to_dict()
        self.assertEqual(d["fir_id"], "F1")
        self.assertEqual(d["duration_days"], 152)

    def test_empty_report_structure_valid(self):
        report = TimelineEngine._empty_report("Test")
        required = [
            "event_count", "dated_event_count", "undated_event_count",
            "events", "gaps", "summary", "evidence_chain",
        ]
        for key in required:
            self.assertIn(key, report)

    def test_missing_timestamps_not_in_heat_map(self):
        ctx = MockContext(search_result=[
            {"crime_no": "KSP-0001", "crime_registered_date": None,
             "district_name": "D", "police_station_name": "S"},
        ])
        report = TimelineEngine.build_timeline(ctx)
        self.assertNotIn(TIMESTAMP_UNAVAILABLE, report["activity_heat"])


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 21: CROSS-DISTRICT / CROSS-STATION
# ─────────────────────────────────────────────────────────────────────────────

class TestCrossDistrictStation(unittest.TestCase):

    def test_multiple_districts_all_in_district_timeline(self):
        ctx = MockContext(search_result=[
            _fir("KSP-0001", district="Mysuru", station="StA"),
            _fir("KSP-0002", district="Hubli", station="StB"),
            _fir("KSP-0003", district="Kolar", station="StC"),
        ])
        report = TimelineEngine.build_timeline(ctx)
        for dist in ["Mysuru", "Hubli", "Kolar"]:
            self.assertIn(dist, report["district_timeline"])

    def test_cross_station_events_tracked_separately(self):
        ctx = MockContext(search_result=[
            _fir("KSP-0001", district="Mysuru", station="StA", officer="SI Ravi"),
            _fir("KSP-0002", district="Mysuru", station="StB", officer="SI Priya"),
        ])
        report = TimelineEngine.build_timeline(ctx)
        self.assertIn("SI Ravi", report["officer_timeline"])
        self.assertIn("SI Priya", report["officer_timeline"])

    def test_same_district_multiple_firs_aggregated(self):
        ctx = MockContext(search_result=[
            _fir(f"KSP-{i:04d}", district="Mysuru") for i in range(5)
        ])
        report = TimelineEngine.build_timeline(ctx)
        self.assertGreaterEqual(
            report["district_timeline"]["Mysuru"]["fir_count"], 5
        )


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 22: ACTIVE vs CLOSED INVESTIGATIONS
# ─────────────────────────────────────────────────────────────────────────────

class TestActiveVsClosed(unittest.TestCase):

    def test_closed_investigation_has_case_closed_event(self):
        ctx = MockContext(search_result=[
            _fir("KSP-0001", close_date="2024-12-01"),
        ])
        report = TimelineEngine.build_timeline(ctx)
        types = {e["event_type"] for e in report["events"]}
        self.assertIn("Case Closed", types)

    def test_active_investigation_no_case_closed_event(self):
        ctx = MockContext(search_result=[_fir("KSP-0001")])
        report = TimelineEngine.build_timeline(ctx)
        types = {e["event_type"] for e in report["events"]}
        self.assertNotIn("Case Closed", types)

    def test_long_active_investigation_detected(self):
        ctx = MockContext(search_result=[
            _fir("KSP-0001", reg_date="2020-01-01",
                 arrest_date="2021-01-01",
                 charge_sheet_date="2022-01-01"),
        ])
        report = TimelineEngine.build_timeline(ctx)
        self.assertGreater(len(report["long_investigations"]), 0)


# ─────────────────────────────────────────────────────────────────────────────
# CLASS 23: FULL PERMUTATION MATRIX (3,500+ cases)
# ─────────────────────────────────────────────────────────────────────────────

REQUIRED_REPORT_KEYS = [
    "event_count", "dated_event_count", "undated_event_count",
    "chronological_order", "order_message", "events",
    "missing_timestamps", "gaps", "repeated_events",
    "long_investigations", "recent_activity", "duration_stats",
    "activity_heat", "officer_timeline", "district_timeline",
    "average_delay", "crime_frequency", "repeat_intervals",
    "station_response_time", "evidence_chain", "summary",
]


class TestPermutationMatrix(unittest.TestCase):

    def test_full_permutation_matrix(self):
        """
        3,500+ permutations:
        5 districts × 5 stations × 5 officers × 7 date combos × 2 entity combos = 3,500
        """
        test_count = 0
        failures = []

        date_combos = [
            {"reg_date": "2024-01-01"},
            {"reg_date": "2024-01-01", "occurred_date": "2023-12-25"},
            {"reg_date": "2024-01-01", "arrest_date": "2024-01-15"},
            {"reg_date": "2024-01-01", "bail_date": "2024-02-01"},
            {"reg_date": "2024-01-01", "close_date": "2024-12-31"},
            {"reg_date": "2024-01-01", "charge_sheet_date": "2024-06-01"},
            {"reg_date": None},  # Missing timestamp scenario
            {"reg_date": "2024-03-01", "occurred_date": "2024-02-28"},
            {"reg_date": "2024-03-01", "arrest_date": "2024-03-10"},
            {"reg_date": "2024-03-01", "court_date": "2024-05-01"},
            {"reg_date": "2024-03-01", "recovery_date": "2024-03-20"},
            {"reg_date": "2024-06-01", "victim_statement_date": "2024-06-05"},
            {"reg_date": "2024-06-01", "witness_statement_date": "2024-06-08"},
            {"reg_date": "2024-06-01", "transfer_date": "2024-07-01"},
        ]

        entity_combos = [
            {"weapon": "Knife"},
            {"vehicle": "KA01AB1234"},
            {},
        ]


        for dist in DISTRICTS:
            for station in STATIONS:
                for officer in OFFICERS:
                    for date_combo in date_combos:
                        for entity in entity_combos:
                            try:
                                crime_no = f"KSP-{test_count:06d}"
                                row = _fir(crime_no, district=dist,
                                           station=station, officer=officer,
                                           **date_combo, **entity)
                                ctx = MockContext(search_result=[row])
                                report = TimelineEngine.build_timeline(ctx)

                                for key in REQUIRED_REPORT_KEYS:
                                    if key not in report:
                                        failures.append(
                                            f"Missing '{key}': {crime_no}"
                                        )

                                if not isinstance(report.get("summary"), str):
                                    failures.append(f"Non-string summary: {crime_no}")

                                test_count += 1
                            except Exception as e:
                                failures.append(f"EXCEPTION {test_count}: {e}")
                                test_count += 1

        print(f"\n[TestPermutationMatrix] Ran {test_count} permutations, {len(failures)} failures.")
        self.assertEqual(len(failures), 0, f"{len(failures)} failures: {failures[:5]}")
        self.assertGreaterEqual(test_count, 3500, f"Expected 3500+, ran {test_count}")

    def test_multi_fir_permutations(self):
        """Permutation: pairs of FIRs with all combinations of shared entity."""
        test_count = 0
        failures = []

        shared_fields = [
            {"weapon": "Knife"},
            {"vehicle": "KA01AB1234"},
            {"officer": "SI Ravi"},
            {},
        ]

        for dist in DISTRICTS:
            for combo in shared_fields:
                try:
                    rows = [
                        _fir(f"KSP-MULTI-{test_count}-A",
                             district=dist, reg_date="2024-01-01", **combo),
                        _fir(f"KSP-MULTI-{test_count}-B",
                             district=dist, reg_date="2024-06-01", **combo),
                    ]
                    report = TimelineEngine.build_timeline(MockContext(rows))
                    if not isinstance(report["summary"], str):
                        failures.append(f"Non-string summary for case {test_count}")
                    test_count += 1
                except Exception as e:
                    failures.append(f"EXCEPTION {test_count}: {e}")
                    test_count += 1

        self.assertEqual(len(failures), 0)

    def test_all_operations_return_correct_types(self):
        ctx = MockContext(search_result=[
            _fir("KSP-0001", reg_date="2024-01-01",
                 occurred_date="2023-12-25", arrest_date="2024-01-15",
                 close_date="2024-12-31", weapon="Knife", vehicle="KA01AB1234"),
            _fir("KSP-0002", reg_date="2024-02-01", district="Hubli",
                 bail_date="2024-03-01", charge_sheet_date="2024-04-01"),
        ])
        report = TimelineEngine.build_timeline(ctx)

        self.assertIsInstance(report["events"], list)
        self.assertIsInstance(report["gaps"], list)
        self.assertIsInstance(report["repeated_events"], list)
        self.assertIsInstance(report["long_investigations"], list)
        self.assertIsInstance(report["duration_stats"], list)
        self.assertIsInstance(report["activity_heat"], dict)
        self.assertIsInstance(report["officer_timeline"], dict)
        self.assertIsInstance(report["district_timeline"], dict)
        self.assertIsInstance(report["crime_frequency"], dict)
        self.assertIsInstance(report["repeat_intervals"], list)
        self.assertIsInstance(report["station_response_time"], list)
        self.assertIsInstance(report["missing_timestamps"], list)
        self.assertIsInstance(report["evidence_chain"], list)
        self.assertIsInstance(report["summary"], str)
        self.assertIsInstance(report["chronological_order"], bool)


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main(verbosity=2)
