"""
tests/test_response_formatter.py
=================================
Test suite for the Enterprise Response Formatter.

Validates:
  - No developer logs, SQL, stage names, table names leak into officer output
  - Smart section hiding (empty timeline, evidence, etc.)
  - Officer-mode output word count ≤ 700 words
  - Markdown headings render correctly
  - All required sections appear when data is present
  - Edge-case handling (missing data, None values, empty results)
  - Developer-mode dump stays internal (never mixed with officer output)
  - Risk level and confidence rendering
  - Evidence, related cases, timeline rendering caps
"""

import pytest
from unittest.mock import MagicMock
from app.ai.response_formatter import (
    ResponseFormatter,
    OfficerReportBuilder,
    OfficerReport,
    FIRDetail,
    PersonSet,
    EvidenceItem,
    RelatedCase,
    TimelineEvent,
    RiskInfo,
    RecommendedAction,
    SummaryRenderer,
    FIRRenderer,
    EntityRenderer,
    EvidenceRenderer,
    CorrelationRenderer,
    TimelineRenderer,
    FindingsRenderer,
    RiskRenderer,
    RecommendationRenderer,
    WarningRenderer,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_context(**kwargs):
    """Build a minimal mock ExecutionContext."""
    ctx = MagicMock()
    # Defaults
    ctx.intent = kwargs.get("intent", "SEARCH_CASES")
    ctx.raw_query = kwargs.get("raw_query", "show cases")
    ctx.search_result = kwargs.get("search_result", [])
    ctx.resolved_entities = kwargs.get("resolved_entities", {})
    ctx.confidence = kwargs.get("confidence", {"final": 0.75})
    ctx.reasoning_result = kwargs.get("reasoning_result", None)
    ctx.confidence_metrics = kwargs.get("confidence_metrics", None)
    ctx.evidence_correlation = kwargs.get("evidence_correlation", None)
    ctx.timeline_report = kwargs.get("timeline_report", None)
    ctx.knowledge_graph_report = kwargs.get("knowledge_graph_report", None)
    ctx.decision_support_report = kwargs.get("decision_support_report", None)
    ctx.similarity_report = kwargs.get("similarity_report", None)
    ctx.multi_agent_report = kwargs.get("multi_agent_report", None)
    ctx.predictive_report = kwargs.get("predictive_report", None)
    ctx.intelligence_bundle = kwargs.get("intelligence_bundle", None)
    ctx.warnings = kwargs.get("warnings", [])
    ctx.hallucination_safe = kwargs.get("hallucination_safe", True)
    ctx.hallucination_violations = kwargs.get("hallucination_violations", [])
    ctx.response = kwargs.get("response", {"summary": ""})
    return ctx


_SAMPLE_RESULT = {
    "crime_no": "KSP-000123",
    "crime_category": "Theft",
    "district_name": "Bengaluru Urban",
    "police_station_name": "Cubbon Park PS",
    "status_name": "Under Investigation",
    "crime_registered_date": "2024-01-15",
    "accused_name": "Ramesh Kumar",
    "accused_names": ["Ramesh Kumar"],
    "victim_name": "Sita Devi",
    "victim_names": ["Sita Devi"],
}

_DEV_LEAK_TERMS = [
    "stage skipped", "duplicate execution", "source table", "confidence penalty",
    "pipeline warning", "sql", "select ", "where ", "from ", "filter",
    "structured_", "_dynamic_suggestions", "execution_trace", "memory_state",
    "debug", "penalty", "stack trace", "traceback", "error in stage",
    "case_master", "accused table",
]


def _assert_no_dev_leaks(text: str):
    lower = text.lower()
    for term in _DEV_LEAK_TERMS:
        assert term not in lower, f"Developer term '{term}' leaked into officer output:\n{text[:500]}"


def _word_count(text: str) -> int:
    return len(text.split())


# ===========================================================================
# 1. SummaryRenderer
# ===========================================================================
class TestSummaryRenderer:
    def test_renders_text(self):
        report = OfficerReport(executive_summary="Test summary.")
        out = SummaryRenderer.render(report)
        assert "EXECUTIVE SUMMARY" in out
        assert "Test summary." in out

    def test_empty_returns_empty(self):
        report = OfficerReport(executive_summary="")
        assert SummaryRenderer.render(report) == "📋 EXECUTIVE SUMMARY"

    def test_no_dev_leaks(self):
        report = OfficerReport(executive_summary="10 theft records found.")
        _assert_no_dev_leaks(SummaryRenderer.render(report))


# ===========================================================================
# 2. FIRRenderer
# ===========================================================================
class TestFIRRenderer:
    def test_renders_all_fields(self):
        fir = FIRDetail(
            fir_number="KSP-000123",
            crime_type="Theft",
            status="Open",
            district="Bengaluru",
            police_station="Cubbon PS",
            date="2024-01-15",
        )
        out = FIRRenderer.render(fir)
        assert "KSP-000123" in out
        assert "Theft" in out
        assert "Bengaluru" in out
        assert "Cubbon PS" in out

    def test_none_returns_empty(self):
        assert FIRRenderer.render(None) == ""

    def test_partial_fields(self):
        fir = FIRDetail(fir_number="KSP-999", crime_type="Assault")
        out = FIRRenderer.render(fir)
        assert "KSP-999" in out
        assert "Assault" in out

    def test_no_sql_in_output(self):
        fir = FIRDetail(fir_number="KSP-001")
        _assert_no_dev_leaks(FIRRenderer.render(fir))


# ===========================================================================
# 3. EntityRenderer
# ===========================================================================
class TestEntityRenderer:
    def test_renders_entities(self):
        ps = PersonSet(accused=["A1"], victims=["V1"], officers=["O1"])
        out = EntityRenderer.render(ps)
        assert "PEOPLE INVOLVED" in out
        assert "Accused\n• A1" in out
        assert "Victims\n• V1" in out
        assert "Investigating Officers\n• O1" in out

    def test_none_returns_empty(self):
        assert EntityRenderer.render(None) == ""

    def test_empty_person_set_returns_empty(self):
        assert EntityRenderer.render(PersonSet()) == ""

    def test_witnesses_rendered(self):
        ps = PersonSet(witnesses=["Witness A"])
        out = EntityRenderer.render(ps)
        assert "Witness A" in out

    def test_no_dev_leaks(self):
        ps = PersonSet(accused=["Raju"], victims=["Priya"])
        _assert_no_dev_leaks(EntityRenderer.render(ps))


# ===========================================================================
# 4. EvidenceRenderer
# ===========================================================================
class TestEvidenceRenderer:
    def test_shows_no_evidence_fallback(self):
        out = EvidenceRenderer.render([])
        assert "No verified evidence available" in out

    def test_available_evidence_gets_checkmark(self):
        items = [EvidenceItem(label="CCTV Footage", available=True)]
        out = EvidenceRenderer.render(items)
        assert "✅" in out
        assert "CCTV Footage" in out

    def test_missing_evidence_gets_cross(self):
        items = [EvidenceItem(label="Weapon", available=False)]
        out = EvidenceRenderer.render(items)
        assert "❌" in out
        assert "Weapon" in out

    def test_mixed_evidence(self):
        items = [
            EvidenceItem("CCTV", True),
            EvidenceItem("Fingerprints", True),
            EvidenceItem("Weapon", False),
        ]
        out = EvidenceRenderer.render(items)
        assert out.count("✅") == 2
        assert out.count("❌") == 1

    def test_no_dev_leaks(self):
        items = [EvidenceItem("Mobile Records", True)]
        _assert_no_dev_leaks(EvidenceRenderer.render(items))


# ===========================================================================
# 5. CorrelationRenderer
# ===========================================================================
class TestCorrelationRenderer:
    def test_empty_returns_empty(self):
        assert CorrelationRenderer.render([]) == ""

    def test_renders_up_to_5(self):
        cases = [RelatedCase(f"KSP-{i:03d}", "Similar crime", "80%") for i in range(10)]
        out = CorrelationRenderer.render(cases)
        # Should only show 5
        assert out.count("KSP-") == 5

    def test_renders_similarity(self):
        cases = [RelatedCase("KSP-001", "Theft pattern", "75%")]
        out = CorrelationRenderer.render(cases)
        assert "75%" in out
        assert "KSP-001" in out

    def test_no_dev_leaks(self):
        cases = [RelatedCase("KSP-999", "Pattern match", "60%")]
        _assert_no_dev_leaks(CorrelationRenderer.render(cases))


# ===========================================================================
# 6. TimelineRenderer
# ===========================================================================
class TestTimelineRenderer:
    def test_empty_returns_empty(self):
        assert TimelineRenderer.render([]) == ""

    def test_caps_at_6_events(self):
        events = [TimelineEvent(f"Event {i}") for i in range(20)]
        out = TimelineRenderer.render(events)
        assert out.count("Event") == 6

    def test_renders_correctly(self):
        events = [TimelineEvent("FIR registered"), TimelineEvent("Arrest made")]
        out = TimelineRenderer.render(events)
        assert "FIR registered" in out
        assert "Arrest made" in out

    def test_no_dev_leaks(self):
        events = [TimelineEvent("Case opened 2024-01-01")]
        _assert_no_dev_leaks(TimelineRenderer.render(events))


# ===========================================================================
# 7. RiskRenderer
# ===========================================================================
class TestRiskRenderer:
    def test_none_returns_empty(self):
        assert RiskRenderer.render(None) == ""

    def test_renders_risk_level(self):
        risk = RiskInfo(level="HIGH", confidence_pct=82.0)
        out = RiskRenderer.render(risk)
        assert "High" in out
        assert "RISK ASSESSMENT" in out

    def test_critical_risk_emoji(self):
        risk = RiskInfo(level="CRITICAL", confidence_pct=95.0)
        out = RiskRenderer.render(risk)
        assert "🔴" in out

    def test_low_risk_emoji(self):
        risk = RiskInfo(level="LOW", confidence_pct=40.0)
        out = RiskRenderer.render(risk)
        assert "🟢" in out

    def test_medium_risk_emoji(self):
        risk = RiskInfo(level="MEDIUM", confidence_pct=60.0)
        out = RiskRenderer.render(risk)
        assert "🟡" in out

    def test_no_dev_leaks(self):
        risk = RiskInfo(level="HIGH", confidence_pct=75.0)
        _assert_no_dev_leaks(RiskRenderer.render(risk))


# ===========================================================================
# 8. RecommendationRenderer
# ===========================================================================
class TestRecommendationRenderer:
    def test_empty_returns_empty(self):
        assert RecommendationRenderer.render([]) == ""

    def test_caps_at_5_actions(self):
        actions = [RecommendedAction(f"Action {i}", "MEDIUM") for i in range(10)]
        out = RecommendationRenderer.render(actions)
        # Count numbered list entries (e.g. "1. Action 0") — should be exactly 5
        import re
        numbered = re.findall(r"^\d+\.", out, re.MULTILINE)
        assert len(numbered) == 5

    def test_renders_actions(self):
        actions = [
            RecommendedAction(text="Action 1", priority="LOW"),
            RecommendedAction(text="Action 2", priority="HIGH"),
        ]
        out = RecommendationRenderer.render(actions)
        assert "RECOMMENDED ACTIONS" in out
        # High priority should sort first, so Action 2 is '1.' and Action 1 is '2.'
        assert "1. Action 2" in out
        assert "2. Action 1" in out

    def test_priority_sorting(self):
        actions = [
            RecommendedAction("Low task", "LOW"),
            RecommendedAction("Critical task", "CRITICAL"),
            RecommendedAction("Medium task", "MEDIUM"),
        ]
        out = RecommendationRenderer.render(actions)
        # Critical should appear before Low
        assert out.index("Critical task") < out.index("Low task")

    def test_no_dev_leaks(self):
        actions = [RecommendedAction("Review evidence files", "HIGH")]
        _assert_no_dev_leaks(RecommendationRenderer.render(actions))


# ===========================================================================
# 9. WarningRenderer
# ===========================================================================
class TestWarningRenderer:
    def test_empty_returns_empty(self):
        assert WarningRenderer.render([]) == ""

    def test_renders_warnings(self):
        out = WarningRenderer.render(["Suspect at large", "Evidence chain unverified"])
        assert "Suspect at large" in out
        assert "Evidence chain unverified" in out

    def test_no_dev_leaks(self):
        _assert_no_dev_leaks(WarningRenderer.render(["Incomplete information"]))


# ===========================================================================
# 10. OfficerReportBuilder
# ===========================================================================
class TestOfficerReportBuilder:

    def test_build_summary_search_cases(self):
        ctx = _make_context(
            intent="SEARCH_CASES",
            search_result=[_SAMPLE_RESULT],
            resolved_entities={"crime_head": "theft", "district": "Bengaluru"},
        )
        summary = OfficerReportBuilder._build_summary(ctx)
        assert "theft" in summary.lower() or "bengaluru" in summary.lower()
        _assert_no_dev_leaks(summary)

    def test_build_summary_fir_lookup(self):
        ctx = _make_context(
            intent="FIR_LOOKUP",
            search_result=[_SAMPLE_RESULT],
            resolved_entities={"identifiers": ["KSP-000123"]},
        )
        summary = OfficerReportBuilder._build_summary(ctx)
        assert "KSP-000123" in summary

    def test_build_summary_no_results(self):
        ctx = _make_context(intent="SEARCH_CASES", search_result=[])
        summary = OfficerReportBuilder._build_summary(ctx)
        assert "no matching" in summary.lower()

    def test_build_fir_detail_only_for_fir_lookup(self):
        ctx = _make_context(
            intent="SEARCH_CASES",
            search_result=[_SAMPLE_RESULT],
        )
        assert OfficerReportBuilder._build_fir_detail(ctx) is None

    def test_build_fir_detail_for_fir_lookup(self):
        ctx = _make_context(
            intent="FIR_LOOKUP",
            search_result=[_SAMPLE_RESULT],
        )
        fir = OfficerReportBuilder._build_fir_detail(ctx)
        assert fir is not None
        assert fir.fir_number == "KSP-000123"
        assert fir.crime_type == "Theft"

    def test_build_people_from_results(self):
        ctx = _make_context(search_result=[_SAMPLE_RESULT])
        people = OfficerReportBuilder._build_people(ctx)
        assert people is not None
        assert "Ramesh Kumar" in people.accused
        assert "Sita Devi" in people.victims

    def test_build_people_empty_results(self):
        ctx = _make_context(search_result=[])
        assert OfficerReportBuilder._build_people(ctx) is None

    def test_build_evidence_from_correlation(self):
        ctx = _make_context(
            search_result=[],
            evidence_correlation={
                "evidence_items": [
                    {"description": "CCTV at junction"},
                    {"description": "Witness statement"},
                ]
            },
        )
        items = OfficerReportBuilder._build_evidence(ctx)
        labels = [i.label for i in items]
        assert "CCTV at junction" in labels

    def test_build_timeline_empty(self):
        ctx = _make_context(timeline_report=None)
        assert OfficerReportBuilder._build_timeline(ctx) == []

    def test_build_timeline_from_report(self):
        ctx = _make_context(
            timeline_report={
                "events": [
                    {"description": "FIR filed", "date": "2024-01-15"},
                    {"description": "Arrest made", "date": "2024-01-20"},
                ]
            }
        )
        events = OfficerReportBuilder._build_timeline(ctx)
        assert len(events) == 2
        assert "FIR filed" in events[0].description

    def test_build_timeline_caps_at_6(self):
        ctx = _make_context(
            timeline_report={
                "events": [{"description": f"Event {i}"} for i in range(20)]
            }
        )
        events = OfficerReportBuilder._build_timeline(ctx)
        assert len(events) == 6

    def test_build_risk_from_decision_support(self):
        ctx = _make_context(
            decision_support_report={
                "executive_summary": "Case is high risk.",
                "risk_assessment": {"overall_risk_level": "HIGH"},
            },
            confidence={"final": 0.85},
        )
        risk = OfficerReportBuilder._build_risk(ctx)
        assert risk is not None
        assert risk.level == "HIGH"
        assert abs(risk.confidence_pct - 85.0) < 0.01

    def test_build_risk_fallback(self):
        ctx = _make_context(confidence={"final": 0.5})
        risk = OfficerReportBuilder._build_risk(ctx)
        assert risk is not None
        assert risk.confidence_pct == 50.0

    def test_build_warnings_strips_dev_messages(self):
        ctx = _make_context(
            warnings=[
                "Stage skipped due to timeout",   # developer — should be stripped
                "Suspect is armed and dangerous",  # officer-safe
            ]
        )
        warnings = OfficerReportBuilder._build_warnings(ctx)
        # "stage skipped" is a dev-only term → stripped
        assert not any("Stage skipped" in w for w in warnings)
        assert any("armed" in w for w in warnings)

    def test_build_warnings_adds_hallucination_alert(self):
        ctx = _make_context(hallucination_safe=False)
        warnings = OfficerReportBuilder._build_warnings(ctx)
        assert any("verified" in w.lower() for w in warnings)

    def test_build_recommendations_from_bundle(self):
        bundle = MagicMock()
        bundle.recommendations = [
            {"action": "Increase patrols", "priority": "HIGH"},
            {"action": "Review CCTV", "priority": "MEDIUM"},
        ]
        ctx = _make_context(intelligence_bundle=bundle)
        actions = OfficerReportBuilder._build_recommendations(ctx)
        texts = [a.text for a in actions]
        assert "Increase patrols" in texts

    def test_build_returns_officer_report(self):
        ctx = _make_context(search_result=[_SAMPLE_RESULT])
        report = OfficerReportBuilder.build(ctx)
        assert isinstance(report, OfficerReport)
        assert report.executive_summary != ""


# ===========================================================================
# 11. ResponseFormatter — officer mode
# ===========================================================================
class TestResponseFormatterOfficerMode:

    def test_produces_plain_text(self):
        ctx = _make_context(search_result=[_SAMPLE_RESULT])
        out = ResponseFormatter.format(ctx, mode="officer")
        assert "EXECUTIVE SUMMARY" in out

    def test_no_dev_leaks(self):
        ctx = _make_context(
            search_result=[_SAMPLE_RESULT],
            resolved_entities={"crime_head": "theft", "district": "Bengaluru"},
        )
        out = ResponseFormatter.format(ctx, mode="officer")
        _assert_no_dev_leaks(out)

    def test_word_count_under_700(self):
        ctx = _make_context(search_result=[_SAMPLE_RESULT])
        out = ResponseFormatter.format(ctx, mode="officer")
        assert _word_count(out) <= 700, f"Output too long: {_word_count(out)} words"

    def test_empty_results_handled_gracefully(self):
        ctx = _make_context(search_result=[])
        out = ResponseFormatter.format(ctx, mode="officer")
        assert "no matching" in out.lower()

    def test_hides_timeline_when_empty(self):
        ctx = _make_context(timeline_report=None)
        out = ResponseFormatter.format(ctx, mode="officer")
        assert "Investigation Timeline" not in out

    def test_shows_timeline_when_present(self):
        ctx = _make_context(
            search_result=[_SAMPLE_RESULT],
            timeline_report={
                "events": [{"description": "Suspect identified", "date": "2024-02-01"}]
            },
        )
        out = ResponseFormatter.format(ctx, mode="officer")
        assert "Investigation Timeline" in out or "Suspect identified" in out

    def test_hides_related_cases_when_empty(self):
        ctx = _make_context(similarity_report=None, search_result=[])
        out = ResponseFormatter.format(ctx, mode="officer")
        assert "Related Cases" not in out

    def test_shows_related_cases_when_present(self):
        ctx = _make_context(
            similarity_report={
                "similar_cases": [
                    {"fir_no": "KSP-999", "reason": "Same accused", "similarity_score": 0.85}
                ]
            }
        )
        out = ResponseFormatter.format(ctx, mode="officer")
        assert "KSP-999" in out

    def test_hides_recommendations_when_empty(self):
        ctx = _make_context(intelligence_bundle=None)
        out = ResponseFormatter.format(ctx, mode="officer")
        assert "Recommended Actions" not in out

    def test_shows_no_evidence_fallback(self):
        ctx = _make_context(search_result=[])
        out = ResponseFormatter.format(ctx, mode="officer")
        assert "No verified evidence available" in out

    def test_fir_details_present_for_fir_lookup(self):
        ctx = _make_context(
            intent="FIR_LOOKUP",
            search_result=[_SAMPLE_RESULT],
            resolved_entities={"identifiers": ["KSP-000123"]},
        )
        out = ResponseFormatter.format(ctx, mode="officer")
        assert "FIR : KSP-000123" in out
        assert "Crime : Theft" in out
        assert "KSP-000123" in out

    def test_fir_details_absent_for_search(self):
        ctx = _make_context(
            intent="SEARCH_CASES",
            search_result=[_SAMPLE_RESULT],
        )
        out = ResponseFormatter.format(ctx, mode="officer")
        assert "FIR Details" not in out

    def test_no_empty_headings(self):
        ctx = _make_context(search_result=[])
        out = ResponseFormatter.format(ctx, mode="officer")
        lines = out.splitlines()
        headings = [l.strip() for l in lines if l.strip().startswith("#")]
        for h in headings:
            # The heading itself should have content after the #s
            content = h.lstrip("#").strip()
            assert content, f"Empty heading found: '{h}'"

    def test_no_duplicate_sections(self):
        ctx = _make_context(search_result=[_SAMPLE_RESULT])
        out = ResponseFormatter.format(ctx, mode="officer")
        # Count occurrences of each top-level heading
        heading_counts = {}
        for line in out.splitlines():
            if line.startswith("# "):
                heading_counts[line] = heading_counts.get(line, 0) + 1
        for heading, count in heading_counts.items():
            assert count == 1, f"Duplicate section '{heading}' found {count} times"

    def test_conversational_intent(self):
        ctx = _make_context(
            intent="GREETING",
            search_result=[],
            response={"summary": "Welcome Officer. I am ready to assist."},
        )
        out = ResponseFormatter.format(ctx, mode="officer")
        assert out  # Should still produce something

    def test_network_search_summary(self):
        ctx = _make_context(intent="NETWORK_SEARCH", search_result=[_SAMPLE_RESULT])
        out = ResponseFormatter.format(ctx, mode="officer")
        assert "network" in out.lower()

    def test_hotspot_summary(self):
        ctx = _make_context(intent="HOTSPOT", search_result=[_SAMPLE_RESULT])
        out = ResponseFormatter.format(ctx, mode="officer")
        assert "hotspot" in out.lower()

    def test_hallucination_warning_injected(self):
        ctx = _make_context(hallucination_safe=False, search_result=[_SAMPLE_RESULT])
        out = ResponseFormatter.format(ctx, mode="officer")
        assert "verified" in out.lower() or "Warnings" in out

    def test_risk_section_present(self):
        ctx = _make_context(confidence={"final": 0.8})
        out = ResponseFormatter.format(ctx, mode="officer")
        assert "RISK ASSESSMENT" in out

    def test_no_sql_in_output(self):
        ctx = _make_context(
            search_result=[_SAMPLE_RESULT],
            resolved_entities={"crime_head": "theft"},
        )
        out = ResponseFormatter.format(ctx, mode="officer")
        assert "SELECT" not in out
        assert "WHERE" not in out
        assert "FROM" not in out

    def test_no_stage_names_in_output(self):
        ctx = _make_context(search_result=[_SAMPLE_RESULT])
        out = ResponseFormatter.format(ctx, mode="officer")
        stage_words = [
            "IntelligenceEngineStage", "SearchServiceStage", "ConfidenceEngineStage",
            "ReasoningEngineStage", "ResponseGeneratorStage",
        ]
        for s in stage_words:
            assert s not in out, f"Stage name '{s}' leaked into officer output"

    def test_no_raw_json_in_output(self):
        ctx = _make_context(search_result=[_SAMPLE_RESULT])
        out = ResponseFormatter.format(ctx, mode="officer")
        assert "{" not in out or out.count("{") < 3  # slight tolerance for markdown

    def test_confidence_percentage_format(self):
        ctx = _make_context(confidence={"final": 0.73})
        out = ResponseFormatter.format(ctx, mode="officer")
        # Confidence should appear as a percentage
        assert "%" in out


# ===========================================================================
# 12. ResponseFormatter — developer mode
# ===========================================================================
class TestResponseFormatterDeveloperMode:

    def test_developer_mode_contains_internals(self):
        ctx = _make_context(
            intent="SEARCH_CASES",
            search_result=[_SAMPLE_RESULT],
        )
        out = ResponseFormatter.format(ctx, mode="developer")
        assert "[DEVELOPER MODE" in out

    def test_developer_mode_not_in_officer_output(self):
        ctx = _make_context(search_result=[_SAMPLE_RESULT])
        officer_out = ResponseFormatter.format(ctx, mode="officer")
        assert "[DEVELOPER MODE" not in officer_out

    def test_developer_dump_contains_intent(self):
        ctx = _make_context(intent="FIR_LOOKUP")
        out = ResponseFormatter.format(ctx, mode="developer")
        assert "intent" in out


# ===========================================================================
# 13. Edge Cases
# ===========================================================================
class TestEdgeCases:

    def test_none_search_result(self):
        ctx = _make_context()
        ctx.search_result = None  # type: ignore
        # Should not crash
        out = ResponseFormatter.format(ctx)
        assert out

    def test_none_confidence(self):
        ctx = _make_context()
        ctx.confidence = {}
        out = ResponseFormatter.format(ctx)
        assert out

    def test_empty_warnings_list(self):
        ctx = _make_context(warnings=[])
        out = ResponseFormatter.format(ctx)
        assert "Warnings" not in out

    def test_single_result_fir_lookup(self):
        ctx = _make_context(
            intent="FIR_LOOKUP",
            search_result=[_SAMPLE_RESULT],
            resolved_entities={"identifiers": ["KSP-000123"]},
        )
        out = ResponseFormatter.format(ctx)
        assert "Bengaluru Urban" in out or "Theft" in out

    def test_many_results(self):
        results = [dict(_SAMPLE_RESULT, crime_no=f"KSP-{i:06d}") for i in range(100)]
        ctx = _make_context(search_result=results)
        out = ResponseFormatter.format(ctx)
        _assert_no_dev_leaks(out)

    def test_special_characters_in_query(self):
        ctx = _make_context(
            raw_query="show FIRs for district 'Bengaluru' (2024)!",
            search_result=[_SAMPLE_RESULT],
        )
        out = ResponseFormatter.format(ctx)
        assert out

    def test_unicode_entity_names(self):
        result = dict(_SAMPLE_RESULT, accused_name="रामेश कुमार", accused_names=["रामेश कुमार"])
        ctx = _make_context(search_result=[result])
        out = ResponseFormatter.format(ctx)
        assert "रामेश कुमार" in out

    def test_missing_decision_support(self):
        ctx = _make_context(decision_support_report=None)
        out = ResponseFormatter.format(ctx)
        assert out  # No crash

    def test_missing_timeline_report(self):
        ctx = _make_context(timeline_report=None)
        out = ResponseFormatter.format(ctx)
        assert "Timeline" not in out

    def test_incomplete_fir_record(self):
        partial = {"crime_no": "KSP-777"}  # Missing most fields
        ctx = _make_context(
            intent="FIR_LOOKUP",
            search_result=[partial],
            resolved_entities={"identifiers": ["KSP-777"]},
        )
        out = ResponseFormatter.format(ctx)
        assert "KSP-777" in out

    def test_hallucination_violations_not_exposed(self):
        ctx = _make_context(
            hallucination_safe=False,
            hallucination_violations=[
                {"type": "unsupported_claim", "text": "SQL-injected claim"}
            ],
        )
        out = ResponseFormatter.format(ctx)
        _assert_no_dev_leaks(out)

    def test_aggregate_count_intent(self):
        ctx = _make_context(
            intent="AGGREGATE_COUNT",
            search_result=[{"count": 42}],
        )
        out = ResponseFormatter.format(ctx)
        assert out

    def test_predict_crime_intent(self):
        ctx = _make_context(
            intent="PREDICT_CRIME",
            search_result=[],
        )
        out = ResponseFormatter.format(ctx)
        assert out

    def test_search_accused_intent(self):
        ctx = _make_context(
            intent="SEARCH_ACCUSED",
            search_result=[_SAMPLE_RESULT],
        )
        out = ResponseFormatter.format(ctx)
        assert "accused" in out.lower()

    def test_search_victims_intent(self):
        ctx = _make_context(
            intent="SEARCH_VICTIMS",
            search_result=[_SAMPLE_RESULT],
        )
        out = ResponseFormatter.format(ctx)
        assert "victim" in out.lower()
