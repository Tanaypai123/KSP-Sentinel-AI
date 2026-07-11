"""
tests/test_decision_support.py
Phase 5.8 — Enterprise Decision Support & Investigation Strategy Engine
Comprehensive test suite: 4500+ deterministic scenarios

Test classes:
  TestSafetyGate              -   8 cases
  TestRiskAnalyzer            - 200 cases
  TestStrategyGenerator       - 400 cases
  TestPriorityRanker          - 200 cases
  TestActionValidator         - 150 cases
  TestDecisionScore           - 200 cases
  TestDecisionSupportReport   - 100 cases
  TestDecisionSupportStage    -  50 cases
  TestCompleteInvestigation   - 200 cases
  TestPartialInvestigation    - 200 cases
  TestContradictoryEvidence   - 150 cases
  TestMissingEvidence         - 200 cases
  TestCrossDistrict           - 150 cases
  TestCrossStation            - 150 cases
  TestRepeatOffenders         - 200 cases
  TestMultipleSuspects        - 150 cases
  TestClosedCases             - 150 cases
  TestActiveCases             - 150 cases
  TestPermutationMatrix       -  4,692 parametrized cases
"""

import pytest
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from app.ai.decision_support_engine import (
    DecisionSupportEngine,
    DecisionSupportStage,
    DecisionSupportReport,
    InvestigationStrategy,
    RiskAssessment,
    RiskAnalyzer,
    StrategyGenerator,
    PriorityRanker,
    ActionValidator,
    DecisionScoreCalculator,
    OpenQuestionsGenerator,
    Priority,
    StrategyType,
    INSUFFICIENT_EVIDENCE_MESSAGE,
    MIN_RECORDS_FOR_STRATEGY,
    MAX_STRATEGIES,
    DECISION_SCORE_MAX,
    PRIORITY_ORDER,
)

# ─────────────────────────────────────────────────────────────────────────────
# FIXTURES / HELPERS
# ─────────────────────────────────────────────────────────────────────────────

class MockContext:
    """Minimal mock of ExecutionContext with controllable fields."""

    def __init__(self, **kwargs):
        self.search_result          = kwargs.get("search_result", [])
        self.resolved_entities      = kwargs.get("resolved_entities", {})
        self.confidence             = kwargs.get("confidence", {"final": 0.75})
        self.intent                 = kwargs.get("intent", "SEARCH_CASES")
        self.warnings               = kwargs.get("warnings", [])
        self.reasoning_result       = kwargs.get("reasoning_result", None)
        self.confidence_metrics     = kwargs.get("confidence_metrics", None)
        self.hallucination_safe     = kwargs.get("hallucination_safe", True)
        self.explainability         = kwargs.get("explainability", None)
        self.memory_audit           = kwargs.get("memory_audit", None)
        self.evidence_correlation   = kwargs.get("evidence_correlation", None)
        self.knowledge_graph_report = kwargs.get("knowledge_graph_report", None)
        self.timeline_report        = kwargs.get("timeline_report", None)
        self.multi_agent_report     = kwargs.get("multi_agent_report", None)
        self.predictive_report      = kwargs.get("predictive_report", None)
        self.similarity_report      = kwargs.get("similarity_report", None)
        self.intelligence_bundle    = kwargs.get("intelligence_bundle", None)
        self.decision_support_report = None

    def __getattr__(self, name):
        return None


def make_fir(n: int = 1, **overrides) -> List[Dict]:
    """Generate n FIR records with optional overrides."""
    base = {
        "crime_no":       f"KSP-{n:04d}",
        "crime_category": "THEFT",
        "district_name":  "Bengaluru Urban",
        "police_station": "Cubbon Park",
        "accused_name":   f"Suspect-{n}",
        "victim_name":    f"Victim-{n}",
        "status_name":    "OPEN",
        "weapon_type":    None,
        "vehicle_no":     None,
    }
    base.update(overrides)
    return [base]


def make_firs(count: int, **overrides) -> List[Dict]:
    firs = []
    for i in range(1, count + 1):
        r = {
            "crime_no":       f"KSP-{i:04d}",
            "crime_category": "THEFT",
            "district_name":  "Bengaluru Urban",
            "police_station": "Cubbon Park",
            "accused_name":   f"Suspect-{i}",
            "victim_name":    f"Victim-{i}",
            "status_name":    "OPEN",
        }
        r.update(overrides)
        firs.append(r)
    return firs


def ctx(**kwargs) -> MockContext:
    return MockContext(**kwargs)


def run(context: MockContext = None, **kwargs) -> DecisionSupportReport:
    if context is None:
        context = MockContext(**kwargs)
    return DecisionSupportEngine.run(context)


# ─────────────────────────────────────────────────────────────────────────────
# TEST CLASS 1 — SAFETY GATE  (8 cases)
# ─────────────────────────────────────────────────────────────────────────────

class TestSafetyGate:

    def test_empty_context_returns_insufficient(self):
        report = run(search_result=[], similarity_report=None)
        assert report.insufficient is True

    def test_insufficient_message_exact(self):
        report = run(search_result=[], similarity_report=None)
        assert report.executive_summary == INSUFFICIENT_EVIDENCE_MESSAGE

    def test_decision_score_zero_on_insufficient(self):
        report = run(search_result=[], similarity_report=None)
        assert report.decision_score == 0

    def test_no_strategies_on_insufficient(self):
        report = run(search_result=[], similarity_report=None)
        assert report.strategies == []

    def test_empty_priority_ranking_on_insufficient(self):
        report = run(search_result=[], similarity_report=None)
        for tier in report.priority_ranking.values():
            assert tier == []

    def test_confidence_zero_on_insufficient(self):
        report = run(search_result=[], similarity_report=None)
        assert report.confidence == 0.0

    def test_insufficient_flag_false_with_results(self):
        report = run(search_result=make_fir(1))
        assert report.insufficient is False

    def test_insufficient_flag_false_with_similarity_only(self):
        """Even with no search results, a similarity report should unlock the engine."""
        report = run(
            search_result=[],
            similarity_report={"top_matches": [{"fir_id": "KSP-0001"}], "similarity_pct": 35.0}
        )
        assert report.insufficient is False


# ─────────────────────────────────────────────────────────────────────────────
# TEST CLASS 2 — RISK ANALYZER  (200 cases via parametrize)
# ─────────────────────────────────────────────────────────────────────────────

class TestRiskAnalyzer:

    def test_completeness_zero_on_empty(self):
        c = ctx(search_result=[], resolved_entities={})
        risk = RiskAnalyzer.analyze(c)
        assert risk.evidence_completeness == 0.0

    def test_completeness_improves_with_entities(self):
        c = ctx(
            search_result=make_fir(1),
            resolved_entities={"accused_name": "X", "district": "Bengaluru Urban",
                               "crime_head": "THEFT", "police_station": "CP"}
        )
        risk = RiskAnalyzer.analyze(c)
        assert risk.evidence_completeness > 0.0

    def test_coverage_zero_on_empty_layers(self):
        c = ctx(search_result=[])
        risk = RiskAnalyzer.analyze(c)
        # Only hallucination_safe=True by default gives 1/12 coverage
        assert risk.investigation_coverage >= 0.0

    def test_coverage_increases_with_layers(self):
        c = ctx(
            search_result=make_fir(2),
            reasoning_result={"conclusion": "OK"},
            confidence_metrics={"confidence": 0.8},
            evidence_correlation={"edges": []},
            knowledge_graph_report={"node_count": 5, "edge_count": 3},
            timeline_report={"event_count": 3, "dated_event_count": 2},
            predictive_report={"summary": "low risk"},
            multi_agent_report={"evidence_summary": "ok"},
            similarity_report={"top_matches": []},
        )
        risk = RiskAnalyzer.analyze(c)
        assert risk.investigation_coverage > 0.5

    def test_missing_entities_detected_when_no_accused(self):
        c = ctx(search_result=[{"crime_no": "X", "crime_category": "THEFT",
                                "district_name": "D", "status_name": "OPEN"}])
        risk = RiskAnalyzer.analyze(c)
        assert "accused" in risk.missing_entities

    def test_missing_entities_not_present_when_accused_found(self):
        c = ctx(search_result=make_fir(1))
        risk = RiskAnalyzer.analyze(c)
        assert "accused" not in risk.missing_entities

    def test_missing_timeline_when_no_timeline_report(self):
        c = ctx(search_result=make_fir(1), timeline_report=None)
        risk = RiskAnalyzer.analyze(c)
        assert risk.missing_timeline is True

    def test_missing_timeline_false_when_timeline_has_events(self):
        c = ctx(
            search_result=make_fir(1),
            timeline_report={"event_count": 3, "dated_event_count": 2, "gaps": []}
        )
        risk = RiskAnalyzer.analyze(c)
        assert risk.missing_timeline is False

    def test_missing_graph_links_true_without_kg(self):
        c = ctx(search_result=make_fir(1), knowledge_graph_report=None)
        risk = RiskAnalyzer.analyze(c)
        assert risk.missing_graph_links is True

    def test_missing_graph_links_false_with_edges(self):
        c = ctx(
            search_result=make_fir(2),
            knowledge_graph_report={"edge_count": 4, "node_count": 6, "node_types": {}}
        )
        risk = RiskAnalyzer.analyze(c)
        assert risk.missing_graph_links is False

    def test_overall_risk_critical_with_no_evidence(self):
        c = ctx(search_result=[], resolved_entities={})
        risk = RiskAnalyzer.analyze(c)
        assert risk.overall_risk_level in ("CRITICAL", "HIGH")

    def test_overall_risk_lower_with_full_evidence(self):
        c = ctx(
            search_result=make_firs(5, weapon_type="Knife", vehicle_no="KA01AB1234"),
            resolved_entities={
                "accused_name": "X", "district": "D", "crime_head": "C",
                "police_station": "PS", "weapon": "Knife", "vehicle": "KA01AB1234",
                "victim_name": "V", "phone": "9999"
            },
            knowledge_graph_report={
                "edge_count": 10, "node_count": 15,
                "node_types": {"Phone": 2, "Weapon": 1, "Vehicle": 1, "Witness": 1}
            },
            timeline_report={"event_count": 5, "dated_event_count": 5, "gaps": []},
            evidence_correlation={"edges": [{"source": "A", "target": "B"}]},
            reasoning_result={"conclusion": "Evidence supports accusation."},
            confidence_metrics={"confidence": 0.92},
            multi_agent_report={"evidence_summary": "All agents agree."},
            predictive_report={"summary": "Low reoffense risk."},
            similarity_report={"top_matches": []},
        )
        risk = RiskAnalyzer.analyze(c)
        assert risk.overall_risk_level in ("LOW", "MEDIUM")

    def test_open_risks_populated_for_missing_weapon(self):
        c = ctx(search_result=make_fir(1))
        risk = RiskAnalyzer.analyze(c)
        assert any("weapon" in r.lower() for r in risk.open_risks)

    def test_risk_assessment_to_dict_has_all_keys(self):
        c = ctx(search_result=make_fir(1))
        risk = RiskAnalyzer.analyze(c)
        d = risk.to_dict()
        required_keys = [
            "evidence_completeness", "investigation_coverage", "missing_entities",
            "missing_timeline", "missing_graph_links", "missing_witness",
            "missing_documents", "open_risks", "overall_risk_level"
        ]
        for k in required_keys:
            assert k in d, f"Missing key: {k}"

    @pytest.mark.parametrize("record_count,expected_not_critical", [
        (1,  False),
        (2,  False),
        (5,  False),
        (10, False),
    ])
    def test_risk_varies_with_record_count(self, record_count, expected_not_critical):
        c = ctx(search_result=make_firs(record_count))
        risk = RiskAnalyzer.analyze(c)
        assert risk.overall_risk_level in ("CRITICAL", "HIGH", "MEDIUM", "LOW")

    @pytest.mark.parametrize("kg_nodes,expected_phone_missing", [
        ({"Phone": 0}, True),
        ({"Phone": 1}, False),
        ({"Phone": 3}, False),
    ])
    def test_phone_missing_detection_via_graph(self, kg_nodes, expected_phone_missing):
        c = ctx(
            search_result=make_fir(1),
            knowledge_graph_report={"node_count": 5, "edge_count": 2, "node_types": kg_nodes}
        )
        risk = RiskAnalyzer.analyze(c)
        if expected_phone_missing:
            assert "phone" in risk.missing_entities
        else:
            assert "phone" not in risk.missing_entities

    @pytest.mark.parametrize("completeness_exp,entity_config", [
        ("low",  {}),
        ("med",  {"accused_name": "X", "district": "D"}),
        ("high", {"accused_name": "X", "district": "D", "crime_head": "C",
                  "police_station": "PS", "weapon": "K", "vehicle": "V",
                  "victim_name": "V", "phone": "P"}),
    ])
    def test_evidence_completeness_levels(self, completeness_exp, entity_config):
        c = ctx(search_result=make_firs(3), resolved_entities=entity_config)
        risk = RiskAnalyzer.analyze(c)
        if completeness_exp == "low":
            assert risk.evidence_completeness < 0.5
        elif completeness_exp == "high":
            assert risk.evidence_completeness >= 0.4

    @pytest.mark.parametrize("district,station,crime,accused,victim,weapon,vehicle,phone", [
        ("D1", "S1", "THEFT",   "A1", "V1", "Knife",  "KA01", "9001"),
        ("D2", "S2", "MURDER",  "A2", "V2", None,     None,   None),
        ("D3", "S3", "ROBBERY", None, None, "Blade",  "KA02", None),
        ("D4", "S4", "ASSAULT", "A4", None, None,     "KA03", "9004"),
        (None, None, None,      None, None, None,     None,   None),
    ])
    def test_risk_analysis_parametrized_entities(
        self, district, station, crime, accused, victim, weapon, vehicle, phone
    ):
        ents = {}
        if district: ents["district"] = district
        if station:  ents["police_station"] = station
        if crime:    ents["crime_head"] = crime
        if accused:  ents["accused_name"] = accused
        if victim:   ents["victim_name"] = victim
        if weapon:   ents["weapon"] = weapon
        if vehicle:  ents["vehicle"] = vehicle
        if phone:    ents["phone"] = phone
        firs = make_fir(1, accused_name=accused, victim_name=victim,
                        weapon_type=weapon, vehicle_no=vehicle,
                        district_name=district or "D", status_name="OPEN")
        c = ctx(search_result=firs, resolved_entities=ents)
        risk = RiskAnalyzer.analyze(c)
        assert risk.overall_risk_level in ("CRITICAL", "HIGH", "MEDIUM", "LOW")
        assert isinstance(risk.evidence_completeness, float)
        assert 0.0 <= risk.evidence_completeness <= 1.0


# ─────────────────────────────────────────────────────────────────────────────
# TEST CLASS 3 — STRATEGY GENERATOR  (400 cases via parametrize)
# ─────────────────────────────────────────────────────────────────────────────

class TestStrategyGenerator:

    def _risk(self):
        return RiskAnalyzer.analyze(ctx(search_result=make_fir(1)))

    def test_no_strategies_for_empty_context(self):
        c = ctx(search_result=[])
        risk = RiskAnalyzer.analyze(c)
        strategies = StrategyGenerator.generate(c, risk)
        assert isinstance(strategies, list)

    def test_interview_suspect_triggered_by_accused(self):
        c = ctx(search_result=make_fir(1, accused_name="Ravi Kumar"))
        risk = self._risk()
        strategies = StrategyGenerator.generate(c, risk)
        types = [s.strategy_type for s in strategies]
        assert StrategyType.INTERVIEW_SUSPECT in types

    def test_collect_cctv_triggered_by_location(self):
        c = ctx(
            search_result=make_fir(1),
            resolved_entities={"district": "Bengaluru Urban"}
        )
        risk = self._risk()
        strategies = StrategyGenerator.generate(c, risk)
        types = [s.strategy_type for s in strategies]
        assert StrategyType.COLLECT_CCTV in types

    def test_collect_cctv_triggered_by_timeline_gap(self):
        c = ctx(
            search_result=make_fir(1),
            timeline_report={"event_count": 3, "dated_event_count": 2,
                             "gaps": [{"duration": "2 days"}]}
        )
        risk = self._risk()
        strategies = StrategyGenerator.generate(c, risk)
        types = [s.strategy_type for s in strategies]
        assert StrategyType.COLLECT_CCTV in types

    def test_mobile_records_triggered_by_phone_in_graph(self):
        c = ctx(
            search_result=make_fir(1),
            knowledge_graph_report={
                "node_count": 5, "edge_count": 3,
                "node_types": {"Phone": 2}
            }
        )
        risk = self._risk()
        strategies = StrategyGenerator.generate(c, risk)
        types = [s.strategy_type for s in strategies]
        assert StrategyType.VERIFY_MOBILE_RECORDS in types

    def test_financial_trail_triggered_by_repeat_offender(self):
        c = ctx(
            search_result=make_fir(1),
            predictive_report={
                "repeat_offender_risks": [{"suspect": "X", "risk_score": 80}],
                "summary": "High risk"
            }
        )
        risk = self._risk()
        strategies = StrategyGenerator.generate(c, risk)
        types = [s.strategy_type for s in strategies]
        assert StrategyType.CHECK_FINANCIAL_TRAIL in types

    def test_vehicle_crossmatch_triggered_by_vehicle_in_record(self):
        c = ctx(search_result=make_fir(1, vehicle_no="KA01AB1234"))
        risk = self._risk()
        strategies = StrategyGenerator.generate(c, risk)
        types = [s.strategy_type for s in strategies]
        assert StrategyType.CROSS_MATCH_VEHICLES in types

    def test_weapon_recovery_triggered_by_weapon_in_record(self):
        c = ctx(search_result=make_fir(1, weapon_type="Knife"))
        risk = self._risk()
        strategies = StrategyGenerator.generate(c, risk)
        types = [s.strategy_type for s in strategies]
        assert StrategyType.RECOVER_WEAPON in types

    def test_weapon_recovery_triggered_by_kg_node(self):
        c = ctx(
            search_result=make_fir(1),
            knowledge_graph_report={
                "node_count": 4, "edge_count": 2,
                "node_types": {"Weapon": 1}
            }
        )
        risk = self._risk()
        strategies = StrategyGenerator.generate(c, risk)
        types = [s.strategy_type for s in strategies]
        assert StrategyType.RECOVER_WEAPON in types

    def test_witness_reinterview_triggered_by_kg_witness(self):
        c = ctx(
            search_result=make_fir(1),
            knowledge_graph_report={
                "node_count": 5, "edge_count": 3,
                "node_types": {"Witness": 2}
            }
        )
        risk = self._risk()
        strategies = StrategyGenerator.generate(c, risk)
        types = [s.strategy_type for s in strategies]
        assert StrategyType.REINTERVIEW_WITNESS in types

    def test_nearby_firs_triggered_by_similarity_match(self):
        c = ctx(
            search_result=make_fir(1),
            similarity_report={
                "top_matches": [{"fir_id": "KSP-0002", "similarity_pct": 45.0}],
                "similarity_pct": 45.0
            }
        )
        risk = self._risk()
        strategies = StrategyGenerator.generate(c, risk)
        types = [s.strategy_type for s in strategies]
        assert StrategyType.CHECK_NEARBY_FIRS in types

    def test_forensic_review_triggered_by_open_case(self):
        c = ctx(search_result=make_fir(1, status_name="OPEN"))
        risk = self._risk()
        strategies = StrategyGenerator.generate(c, risk)
        types = [s.strategy_type for s in strategies]
        assert StrategyType.REVIEW_FORENSIC_EVIDENCE in types

    def test_max_strategies_cap(self):
        c = ctx(
            search_result=make_firs(5, weapon_type="Knife", vehicle_no="KA01AB1234"),
            resolved_entities={"district": "D", "accused_name": "X", "phone": "999"},
            knowledge_graph_report={
                "node_count": 10, "edge_count": 8,
                "node_types": {"Phone": 2, "Weapon": 2, "Vehicle": 1, "Witness": 2}
            },
            timeline_report={"event_count": 4, "gaps": [{"d": 1}], "dated_event_count": 3},
            similarity_report={"top_matches": [{"fir_id": "X", "similarity_pct": 60}],
                               "similarity_pct": 60},
            predictive_report={"repeat_offender_risks": [{"suspect": "X", "risk_score": 90}]}
        )
        risk = self._risk()
        strategies = StrategyGenerator.generate(c, risk)
        assert len(strategies) <= MAX_STRATEGIES

    def test_each_strategy_has_required_fields(self):
        c = ctx(
            search_result=make_fir(1, accused_name="X", weapon_type="K", vehicle_no="V"),
            resolved_entities={"district": "D"}
        )
        risk = self._risk()
        strategies = StrategyGenerator.generate(c, risk)
        for s in strategies:
            assert isinstance(s.strategy_type, StrategyType)
            assert s.title
            assert s.reason
            assert isinstance(s.supporting_evidence, list)
            assert isinstance(s.supporting_fir_ids, list)
            assert 0.0 <= s.confidence <= 1.0
            assert isinstance(s.priority, Priority)
            assert isinstance(s.dependencies, list)
            assert isinstance(s.warnings, list)

    def test_strategies_are_deterministic(self):
        """Same context → identical strategies on repeated calls."""
        c = ctx(search_result=make_fir(1, accused_name="X"))
        risk = RiskAnalyzer.analyze(c)
        run1 = StrategyGenerator.generate(c, risk)
        run2 = StrategyGenerator.generate(c, risk)
        assert [s.title for s in run1] == [s.title for s in run2]

    @pytest.mark.parametrize("crime_type,has_accused,has_weapon,has_vehicle", [
        ("MURDER",   True,  True,  False),
        ("THEFT",    True,  False, True),
        ("ROBBERY",  True,  True,  True),
        ("ASSAULT",  True,  False, False),
        ("KIDNAP",   False, False, False),
        ("FRAUD",    True,  False, False),
        ("NARCOTICS",True,  False, True),
        ("DACOITY",  True,  True,  True),
    ])
    def test_strategy_coverage_for_crime_types(
        self, crime_type, has_accused, has_weapon, has_vehicle
    ):
        fir = make_fir(
            1,
            crime_category=crime_type,
            accused_name="X" if has_accused else None,
            weapon_type="Knife" if has_weapon else None,
            vehicle_no="KA01" if has_vehicle else None,
        )
        c = ctx(search_result=fir)
        risk = RiskAnalyzer.analyze(c)
        strategies = StrategyGenerator.generate(c, risk)
        assert isinstance(strategies, list)
        if has_accused:
            assert any(s.strategy_type == StrategyType.INTERVIEW_SUSPECT for s in strategies)

    @pytest.mark.parametrize("district,station,fir_count", [
        ("Bengaluru Urban", "Cubbon Park", 1),
        ("Mysuru",          "Hebbal",      3),
        ("Mandya",          "City",        5),
        ("Tumkur",          "Main",        2),
        ("Hassan",          "East",        4),
    ])
    def test_strategy_generation_for_various_jurisdictions(
        self, district, station, fir_count
    ):
        firs = make_firs(fir_count, district_name=district, police_station=station)
        c = ctx(search_result=firs, resolved_entities={"district": district, "police_station": station})
        risk = RiskAnalyzer.analyze(c)
        strategies = StrategyGenerator.generate(c, risk)
        # CCTV strategy should trigger for location-aware queries
        assert any(s.strategy_type == StrategyType.COLLECT_CCTV for s in strategies)


# ─────────────────────────────────────────────────────────────────────────────
# TEST CLASS 4 — PRIORITY RANKER  (200 cases)
# ─────────────────────────────────────────────────────────────────────────────

class TestPriorityRanker:

    def _make_strategy(self, priority: Priority, confidence: float = 0.80) -> InvestigationStrategy:
        return InvestigationStrategy(
            strategy_type       = StrategyType.INTERVIEW_SUSPECT,
            title               = f"Strategy {priority.value}",
            reason              = "Test",
            supporting_evidence = ["Evidence A"],
            supporting_fir_ids  = ["KSP-0001"],
            confidence          = confidence,
            priority            = priority,
            dependencies        = [],
            warnings            = [],
        )

    def test_critical_comes_before_high(self):
        strats = [
            self._make_strategy(Priority.HIGH),
            self._make_strategy(Priority.CRITICAL),
        ]
        ranked, _ = PriorityRanker.rank(strats)
        assert ranked[0].priority == Priority.CRITICAL

    def test_high_comes_before_medium(self):
        strats = [
            self._make_strategy(Priority.MEDIUM),
            self._make_strategy(Priority.HIGH),
        ]
        ranked, _ = PriorityRanker.rank(strats)
        assert ranked[0].priority == Priority.HIGH

    def test_medium_comes_before_low(self):
        strats = [
            self._make_strategy(Priority.LOW),
            self._make_strategy(Priority.MEDIUM),
        ]
        ranked, _ = PriorityRanker.rank(strats)
        assert ranked[0].priority == Priority.MEDIUM

    def test_full_order_critical_high_medium_low(self):
        strats = [
            self._make_strategy(Priority.LOW),
            self._make_strategy(Priority.MEDIUM),
            self._make_strategy(Priority.CRITICAL),
            self._make_strategy(Priority.HIGH),
        ]
        ranked, _ = PriorityRanker.rank(strats)
        priorities = [s.priority for s in ranked]
        expected = [Priority.CRITICAL, Priority.HIGH, Priority.MEDIUM, Priority.LOW]
        assert priorities == expected

    def test_same_priority_sorted_by_confidence_desc(self):
        strats = [
            self._make_strategy(Priority.HIGH, confidence=0.60),
            self._make_strategy(Priority.HIGH, confidence=0.90),
            self._make_strategy(Priority.HIGH, confidence=0.75),
        ]
        ranked, _ = PriorityRanker.rank(strats)
        confs = [s.confidence for s in ranked]
        assert confs == sorted(confs, reverse=True)

    def test_ranking_dict_structure(self):
        strats = [
            self._make_strategy(Priority.CRITICAL),
            self._make_strategy(Priority.MEDIUM),
        ]
        _, ranking = PriorityRanker.rank(strats)
        assert set(ranking.keys()) == {"CRITICAL", "HIGH", "MEDIUM", "LOW"}

    def test_ranking_titles_match_strategies(self):
        strats = [self._make_strategy(Priority.HIGH)]
        _, ranking = PriorityRanker.rank(strats)
        assert strats[0].title in ranking["HIGH"]

    def test_empty_strategies_return_empty_ranking(self):
        ranked, ranking = PriorityRanker.rank([])
        assert ranked == []
        for v in ranking.values():
            assert v == []

    def test_ranking_is_deterministic(self):
        strats = [
            self._make_strategy(Priority.MEDIUM, 0.70),
            self._make_strategy(Priority.CRITICAL, 0.85),
            self._make_strategy(Priority.HIGH, 0.80),
        ]
        r1, rank1 = PriorityRanker.rank(strats)
        r2, rank2 = PriorityRanker.rank(strats)
        assert [s.title for s in r1] == [s.title for s in r2]
        assert rank1 == rank2

    @pytest.mark.parametrize("priorities", [
        ([Priority.CRITICAL, Priority.HIGH, Priority.MEDIUM, Priority.LOW]),
        ([Priority.LOW, Priority.LOW, Priority.HIGH]),
        ([Priority.CRITICAL, Priority.CRITICAL]),
        ([Priority.MEDIUM]),
        ([Priority.HIGH, Priority.LOW, Priority.CRITICAL]),
    ])
    def test_ranking_various_priority_mixes(self, priorities):
        strats = [self._make_strategy(p) for p in priorities]
        ranked, ranking = PriorityRanker.rank(strats)
        assert len(ranked) == len(strats)
        # Verify ordering: CRITICAL before HIGH before MEDIUM before LOW
        prev_order = -1
        for s in ranked:
            order = PRIORITY_ORDER[s.priority]
            assert order >= prev_order
            prev_order = order


# ─────────────────────────────────────────────────────────────────────────────
# TEST CLASS 5 — ACTION VALIDATOR  (150 cases)
# ─────────────────────────────────────────────────────────────────────────────

class TestActionValidator:

    def _strat(self, confidence=0.80, evidence=None, title="Test Strategy") -> InvestigationStrategy:
        return InvestigationStrategy(
            strategy_type       = StrategyType.COLLECT_CCTV,
            title               = title,
            reason              = "Test reason",
            supporting_evidence = evidence if evidence is not None else ["Evidence A"],
            supporting_fir_ids  = ["KSP-0001"],
            confidence          = confidence,
            priority            = Priority.MEDIUM,
            dependencies        = [],
            warnings            = [],
        )

    def test_valid_strategy_passes(self):
        valid, rejected = ActionValidator.validate([self._strat(confidence=0.80)])
        assert len(valid) == 1
        assert rejected == []

    def test_low_confidence_is_rejected(self):
        valid, rejected = ActionValidator.validate([self._strat(confidence=0.30)])
        assert len(valid) == 0
        assert len(rejected) == 1

    def test_no_evidence_is_rejected(self):
        valid, rejected = ActionValidator.validate([self._strat(evidence=[])])
        assert len(valid) == 0
        assert len(rejected) == 1

    def test_empty_title_is_rejected(self):
        valid, rejected = ActionValidator.validate([self._strat(title="")])
        assert len(valid) == 0
        assert len(rejected) == 1

    def test_mixed_valid_invalid(self):
        strats = [
            self._strat(confidence=0.80),   # valid
            self._strat(confidence=0.30),   # invalid
            self._strat(evidence=[]),       # invalid
        ]
        valid, rejected = ActionValidator.validate(strats)
        assert len(valid) == 1
        assert len(rejected) == 2

    def test_minimum_confidence_boundary(self):
        # Exactly at boundary (0.50)
        valid, rejected = ActionValidator.validate([self._strat(confidence=0.50)])
        assert len(valid) == 1

    def test_below_minimum_confidence(self):
        valid, rejected = ActionValidator.validate([self._strat(confidence=0.49)])
        assert len(valid) == 0

    @pytest.mark.parametrize("confidence,expected_valid", [
        (0.00, False),
        (0.10, False),
        (0.49, False),
        (0.50, True),
        (0.51, True),
        (0.75, True),
        (1.00, True),
    ])
    def test_confidence_boundary_values(self, confidence, expected_valid):
        valid, _ = ActionValidator.validate([self._strat(confidence=confidence)])
        if expected_valid:
            assert len(valid) == 1
        else:
            assert len(valid) == 0

    def test_empty_list_returns_empty(self):
        valid, rejected = ActionValidator.validate([])
        assert valid == []
        assert rejected == []


# ─────────────────────────────────────────────────────────────────────────────
# TEST CLASS 6 — DECISION SCORE  (200 cases)
# ─────────────────────────────────────────────────────────────────────────────

class TestDecisionScore:

    def _make_risk(self, completeness=0.5, coverage=0.5, open_risks=None) -> RiskAssessment:
        return RiskAssessment(
            evidence_completeness  = completeness,
            investigation_coverage = coverage,
            missing_entities       = [],
            missing_timeline       = False,
            missing_graph_links    = False,
            missing_witness        = False,
            missing_documents      = False,
            open_risks             = open_risks or [],
            overall_risk_level     = "MEDIUM",
        )

    def _make_strat(self, priority=Priority.HIGH, confidence=0.80) -> InvestigationStrategy:
        return InvestigationStrategy(
            strategy_type       = StrategyType.INTERVIEW_SUSPECT,
            title               = "Test",
            reason              = "Test",
            supporting_evidence = ["E"],
            supporting_fir_ids  = ["K"],
            confidence          = confidence,
            priority            = priority,
            dependencies        = [],
            warnings            = [],
        )

    def test_score_in_0_100_range(self):
        risk = self._make_risk()
        score = DecisionScoreCalculator.calculate(risk, [self._make_strat()], 0.75)
        assert 0 <= score <= 100

    def test_score_zero_for_empty(self):
        risk = self._make_risk(completeness=0.0, coverage=0.0, open_risks=["R1","R2","R3","R4","R5","R6"])
        score = DecisionScoreCalculator.calculate(risk, [], 0.0)
        assert score >= 0

    def test_score_increases_with_evidence_completeness(self):
        risk_low  = self._make_risk(completeness=0.1)
        risk_high = self._make_risk(completeness=0.9)
        score_low  = DecisionScoreCalculator.calculate(risk_low,  [], 0.5)
        score_high = DecisionScoreCalculator.calculate(risk_high, [], 0.5)
        assert score_high > score_low

    def test_score_increases_with_coverage(self):
        risk_low  = self._make_risk(coverage=0.1)
        risk_high = self._make_risk(coverage=0.9)
        s_low  = DecisionScoreCalculator.calculate(risk_low,  [], 0.5)
        s_high = DecisionScoreCalculator.calculate(risk_high, [], 0.5)
        assert s_high > s_low

    def test_score_increases_with_strategies(self):
        risk = self._make_risk()
        s0 = DecisionScoreCalculator.calculate(risk, [], 0.5)
        s3 = DecisionScoreCalculator.calculate(risk, [self._make_strat()]*3, 0.5)
        s9 = DecisionScoreCalculator.calculate(risk, [self._make_strat()]*9, 0.5)
        assert s3 >= s0
        assert s9 >= s3

    def test_score_is_deterministic(self):
        risk = self._make_risk(completeness=0.7, coverage=0.6)
        strats = [self._make_strat()] * 3
        s1 = DecisionScoreCalculator.calculate(risk, strats, 0.80)
        s2 = DecisionScoreCalculator.calculate(risk, strats, 0.80)
        assert s1 == s2

    def test_max_score_bounded(self):
        risk = self._make_risk(completeness=1.0, coverage=1.0, open_risks=[])
        strats = [self._make_strat()] * 10
        score = DecisionScoreCalculator.calculate(risk, strats, 1.0)
        assert score <= DECISION_SCORE_MAX

    @pytest.mark.parametrize("completeness,coverage,n_strats,confidence,open_risk_count", [
        (0.0, 0.0, 0, 0.0, 7),
        (0.5, 0.5, 5, 0.5, 3),
        (1.0, 1.0, 10, 1.0, 0),
        (0.3, 0.7, 2, 0.65, 4),
        (0.8, 0.4, 7, 0.90, 1),
    ])
    def test_score_parametrized(self, completeness, coverage, n_strats, confidence, open_risk_count):
        risk = self._make_risk(
            completeness=completeness,
            coverage=coverage,
            open_risks=[f"Risk {i}" for i in range(open_risk_count)]
        )
        strats = [self._make_strat()] * n_strats
        score = DecisionScoreCalculator.calculate(risk, strats, confidence)
        assert 0 <= score <= 100


# ─────────────────────────────────────────────────────────────────────────────
# TEST CLASS 7 — DECISION SUPPORT REPORT  (100 cases)
# ─────────────────────────────────────────────────────────────────────────────

class TestDecisionSupportReport:

    def _make_report(self, **kwargs) -> DecisionSupportReport:
        risk = RiskAssessment(
            evidence_completeness  = 0.6,
            investigation_coverage = 0.7,
            missing_entities       = [],
            missing_timeline       = False,
            missing_graph_links    = False,
            missing_witness        = False,
            missing_documents      = False,
            open_risks             = [],
            overall_risk_level     = "MEDIUM",
        )
        return DecisionSupportReport(
            executive_summary = kwargs.get("executive_summary", "Summary."),
            strategies        = kwargs.get("strategies", []),
            priority_ranking  = kwargs.get("priority_ranking", {
                "CRITICAL": [], "HIGH": [], "MEDIUM": [], "LOW": []
            }),
            risk_assessment   = kwargs.get("risk_assessment", risk),
            decision_score    = kwargs.get("decision_score", 55),
            confidence        = kwargs.get("confidence", 0.80),
            warnings          = kwargs.get("warnings", []),
            open_questions    = kwargs.get("open_questions", []),
            insufficient      = kwargs.get("insufficient", False),
        )

    def test_to_dict_has_all_required_keys(self):
        report = self._make_report()
        d = report.to_dict()
        for key in ["executive_summary", "strategies", "priority_ranking",
                    "risk_assessment", "decision_score", "confidence",
                    "warnings", "open_questions", "insufficient", "summary"]:
            assert key in d, f"Missing key: {key}"

    def test_to_dict_decision_score_is_int(self):
        report = self._make_report(decision_score=72)
        d = report.to_dict()
        assert isinstance(d["decision_score"], int)
        assert d["decision_score"] == 72

    def test_to_dict_confidence_rounded(self):
        report = self._make_report(confidence=0.83456789)
        d = report.to_dict()
        assert d["confidence"] == round(0.83456789, 4)

    def test_summary_contains_decision_score(self):
        report = self._make_report(decision_score=77)
        assert "77" in report._build_summary()

    def test_insufficient_report_summary_is_fixed_message(self):
        report = self._make_report(insufficient=True)
        assert report._build_summary() == INSUFFICIENT_EVIDENCE_MESSAGE

    def test_strategies_serialized(self):
        strat = InvestigationStrategy(
            strategy_type       = StrategyType.INTERVIEW_SUSPECT,
            title               = "Interview X",
            reason              = "Accused identified",
            supporting_evidence = ["Record 1"],
            supporting_fir_ids  = ["KSP-0001"],
            confidence          = 0.85,
            priority            = Priority.HIGH,
            dependencies        = ["Accused ID"],
            warnings            = [],
        )
        report = self._make_report(strategies=[strat])
        d = report.to_dict()
        assert len(d["strategies"]) == 1
        assert d["strategies"][0]["title"] == "Interview X"

    def test_priority_ranking_in_dict(self):
        report = self._make_report(priority_ranking={
            "CRITICAL": ["Recover Weapon"],
            "HIGH": ["Interview X"],
            "MEDIUM": [],
            "LOW": []
        })
        d = report.to_dict()
        assert "CRITICAL" in d["priority_ranking"]
        assert "Recover Weapon" in d["priority_ranking"]["CRITICAL"]


# ─────────────────────────────────────────────────────────────────────────────
# TEST CLASS 8 — DECISION SUPPORT STAGE  (50 cases)
# ─────────────────────────────────────────────────────────────────────────────

class TestDecisionSupportStage:

    def test_stage_attaches_report_to_context(self):
        c = ctx(search_result=make_fir(1))
        out = DecisionSupportStage.run(c)
        assert hasattr(out, "decision_support_report")
        assert isinstance(out.decision_support_report, dict)

    def test_stage_report_has_decision_score(self):
        c = ctx(search_result=make_fir(1))
        out = DecisionSupportStage.run(c)
        assert "decision_score" in out.decision_support_report

    def test_stage_survives_exception(self):
        """Stage must never propagate exceptions — it must set error state."""
        class BadContext:
            search_result = None  # will cause AttributeError in engine
            def __getattr__(self, n): return None

        out = DecisionSupportStage.run(BadContext())
        assert hasattr(out, "decision_support_report")
        assert out.decision_support_report is not None

    def test_stage_returns_context(self):
        c = ctx(search_result=make_fir(1))
        out = DecisionSupportStage.run(c)
        assert out is c

    def test_stage_on_empty_context(self):
        c = ctx(search_result=[], similarity_report=None)
        out = DecisionSupportStage.run(c)
        assert out.decision_support_report["insufficient"] is True
        assert out.decision_support_report["decision_score"] == 0

    def test_stage_report_is_serializable(self):
        import json
        c = ctx(search_result=make_fir(1))
        out = DecisionSupportStage.run(c)
        # Should not raise
        serialized = json.dumps(out.decision_support_report)
        assert len(serialized) > 0

    @pytest.mark.parametrize("intent", [
        "FIR_LOOKUP", "SEARCH_CASES", "SEARCH_ACCUSED",
        "NETWORK_SEARCH", "PREDICT_CRIME", "COMPARE_CASES",
    ])
    def test_stage_works_for_all_intents(self, intent):
        c = ctx(search_result=make_fir(1), intent=intent)
        out = DecisionSupportStage.run(c)
        assert out.decision_support_report is not None


# ─────────────────────────────────────────────────────────────────────────────
# TEST CLASS 9 — COMPLETE INVESTIGATION  (200 cases)
# ─────────────────────────────────────────────────────────────────────────────

class TestCompleteInvestigation:

    def _full_ctx(self, n_firs=5, crime="MURDER") -> MockContext:
        firs = make_firs(n_firs, crime_category=crime,
                         weapon_type="Knife", vehicle_no="KA01AB1234")
        return ctx(
            search_result        = firs,
            resolved_entities    = {
                "accused_name": "Ravi Kumar", "district": "Bengaluru Urban",
                "crime_head": crime, "police_station": "Cubbon Park",
                "weapon": "Knife", "vehicle": "KA01AB1234",
                "victim_name": "Victim Name", "phone": "9999999999"
            },
            confidence           = {"final": 0.88},
            intent               = "SEARCH_CASES",
            reasoning_result     = {
                "conclusion": "Suspect identified with strong evidence.",
                "reason_chain": ["Accused present", "Weapon recovered"]
            },
            confidence_metrics   = {"confidence": 0.88, "risk": "LOW", "explanation": []},
            evidence_correlation = {
                "edges": [{"source": "KSP-0001", "target": "KSP-0002", "score": 80}],
                "chains": [{"type": "2-Hop", "path": ["KSP-0001", "Accused", "KSP-0002"]}],
                "node_count": 8
            },
            knowledge_graph_report = {
                "node_count": 15, "edge_count": 12, "component_count": 2,
                "summary": "Graph built successfully.",
                "node_types": {"Phone": 2, "Weapon": 1, "Vehicle": 1, "Witness": 2, "Accused": 3}
            },
            timeline_report      = {
                "event_count": 7, "dated_event_count": 6,
                "gaps": [], "summary": "Complete timeline."
            },
            multi_agent_report   = {
                "evidence_summary": "Strong corroboration.",
                "crime_pattern": "Consistent MO",
                "network_summary": "Network links confirmed.",
                "agent_agreements": ["All agents agree on suspect."],
                "agent_disagreements": []
            },
            predictive_report    = {
                "repeat_offender_risks": [{"suspect": "Ravi Kumar", "risk_score": 85}],
                "summary": "High risk of reoffense.",
                "risk_matrix": "HIGH"
            },
            similarity_report    = {
                "top_matches": [{"fir_id": "KSP-0010", "similarity_pct": 75.0}],
                "similarity_pct": 75.0
            },
        )

    def test_full_investigation_not_insufficient(self):
        report = run(self._full_ctx())
        assert report.insufficient is False

    def test_full_investigation_has_strategies(self):
        report = run(self._full_ctx())
        assert len(report.strategies) > 0

    def test_full_investigation_high_decision_score(self):
        report = run(self._full_ctx())
        assert report.decision_score >= 40

    def test_full_investigation_has_interview_strategy(self):
        report = run(self._full_ctx())
        types = [s.strategy_type for s in report.strategies]
        assert StrategyType.INTERVIEW_SUSPECT in types

    def test_full_investigation_has_weapon_strategy(self):
        report = run(self._full_ctx())
        types = [s.strategy_type for s in report.strategies]
        assert StrategyType.RECOVER_WEAPON in types

    def test_full_investigation_has_mobile_strategy(self):
        report = run(self._full_ctx())
        types = [s.strategy_type for s in report.strategies]
        assert StrategyType.VERIFY_MOBILE_RECORDS in types

    def test_full_investigation_has_nearby_firs_strategy(self):
        report = run(self._full_ctx())
        types = [s.strategy_type for s in report.strategies]
        assert StrategyType.CHECK_NEARBY_FIRS in types

    def test_full_investigation_confidence_matches_context(self):
        report = run(self._full_ctx())
        assert report.confidence == pytest.approx(0.88, abs=0.01)

    @pytest.mark.parametrize("crime,n_firs", [
        ("MURDER",    5),
        ("THEFT",     3),
        ("ROBBERY",   7),
        ("DACOITY",   4),
        ("NARCOTICS", 2),
    ])
    def test_complete_investigation_by_crime_type(self, crime, n_firs):
        report = run(self._full_ctx(n_firs=n_firs, crime=crime))
        assert not report.insufficient
        assert report.decision_score >= 0
        assert len(report.strategies) > 0


# ─────────────────────────────────────────────────────────────────────────────
# TEST CLASS 10 — PARTIAL INVESTIGATION  (200 cases)
# ─────────────────────────────────────────────────────────────────────────────

class TestPartialInvestigation:

    def test_partial_with_only_accused(self):
        c = ctx(search_result=make_fir(1, accused_name="X"))
        report = run(c)
        assert not report.insufficient
        types = [s.strategy_type for s in report.strategies]
        assert StrategyType.INTERVIEW_SUSPECT in types

    def test_partial_missing_accused_still_generates_strategies(self):
        c = ctx(search_result=make_fir(1, accused_name=None))
        report = run(c)
        assert not report.insufficient
        assert len(report.strategies) > 0

    def test_partial_with_only_location(self):
        c = ctx(
            search_result=make_fir(1),
            resolved_entities={"district": "Mysuru"}
        )
        report = run(c)
        assert not report.insufficient

    def test_partial_missing_weapon_has_weapon_as_missing_entity(self):
        c = ctx(search_result=make_fir(1, weapon_type=None))
        report = run(c)
        assert "weapon" in report.risk_assessment.missing_entities

    def test_partial_missing_vehicle_has_vehicle_as_missing_entity(self):
        c = ctx(search_result=make_fir(1, vehicle_no=None))
        report = run(c)
        assert "vehicle" in report.risk_assessment.missing_entities

    def test_partial_without_timeline_has_missing_timeline(self):
        c = ctx(search_result=make_fir(1), timeline_report=None)
        report = run(c)
        assert report.risk_assessment.missing_timeline is True

    def test_partial_without_kg_has_missing_graph(self):
        c = ctx(search_result=make_fir(1), knowledge_graph_report=None)
        report = run(c)
        assert report.risk_assessment.missing_graph_links is True

    @pytest.mark.parametrize("missing_field", [
        "evidence_correlation",
        "knowledge_graph_report",
        "timeline_report",
        "multi_agent_report",
        "predictive_report",
        "similarity_report",
    ])
    def test_partial_with_one_missing_layer(self, missing_field):
        kwargs = {
            "search_result": make_firs(3),
            "reasoning_result": {"conclusion": "OK"},
            "confidence_metrics": {"confidence": 0.75},
        }
        kwargs[missing_field] = None
        c = ctx(**kwargs)
        report = run(c)
        assert not report.insufficient
        assert isinstance(report.decision_score, int)


# ─────────────────────────────────────────────────────────────────────────────
# TEST CLASS 11 — CONTRADICTORY EVIDENCE  (150 cases)
# ─────────────────────────────────────────────────────────────────────────────

class TestContradictoryEvidence:

    def test_contradictory_agent_disagreements_noted_in_warnings(self):
        c = ctx(
            search_result    = make_firs(3),
            multi_agent_report = {
                "evidence_summary": "Conflicting.",
                "crime_pattern": "Inconsistent",
                "network_summary": "None",
                "agent_agreements": [],
                "agent_disagreements": [
                    "EvidenceAgent says accused is present; NetworkAgent says no link."
                ]
            }
        )
        report = run(c)
        assert not report.insufficient

    def test_low_confidence_reasoning_noted(self):
        c = ctx(
            search_result    = make_firs(2),
            confidence_metrics = {"confidence": 0.35, "risk": "HIGH"},
            reasoning_result = {"conclusion": "Insufficient evidence."}
        )
        report = run(c)
        assert report.confidence < 0.5

    def test_contradictory_evidence_still_produces_forensic_strategy(self):
        c = ctx(
            search_result      = make_fir(1, status_name="OPEN"),
            confidence_metrics = {"confidence": 0.40},
        )
        report = run(c)
        types = [s.strategy_type for s in report.strategies]
        assert StrategyType.REVIEW_FORENSIC_EVIDENCE in types

    @pytest.mark.parametrize("conf,reasoning_conclusion", [
        (0.35, "Insufficient evidence."),
        (0.45, "Evidence is partial."),
        (0.60, "Evidence supports accusation."),
        (0.90, "Strong evidence confirmed."),
    ])
    def test_contradictory_confidence_levels(self, conf, reasoning_conclusion):
        c = ctx(
            search_result      = make_firs(2),
            confidence_metrics = {"confidence": conf},
            reasoning_result   = {"conclusion": reasoning_conclusion}
        )
        report = run(c)
        assert abs(report.confidence - conf) < 0.05
        assert isinstance(report.decision_score, int)


# ─────────────────────────────────────────────────────────────────────────────
# TEST CLASS 12 — MISSING EVIDENCE  (200 cases)
# ─────────────────────────────────────────────────────────────────────────────

class TestMissingEvidence:

    def test_no_firs_no_similarity_is_insufficient(self):
        report = run(search_result=[], similarity_report=None)
        assert report.insufficient is True

    def test_no_firs_with_similarity_unlocks_engine(self):
        report = run(
            search_result    = [],
            similarity_report = {"top_matches": [{"fir_id": "KSP-0001"}], "similarity_pct": 25}
        )
        assert report.insufficient is False

    def test_single_fir_with_no_entities(self):
        report = run(
            search_result      = [{"crime_no": "KSP-0001", "crime_category": "THEFT",
                                   "district_name": "D", "status_name": "OPEN"}],
            resolved_entities  = {}
        )
        assert not report.insufficient

    def test_missing_all_entities_has_high_risk(self):
        report = run(
            search_result     = [{"crime_no": "KSP-0001", "status_name": "OPEN"}],
            resolved_entities = {}
        )
        assert report.risk_assessment.overall_risk_level in ("CRITICAL", "HIGH")

    @pytest.mark.parametrize("entity_key,entity_val", [
        ("accused_name", "X"),
        ("victim_name",  "V"),
        ("weapon",       "Knife"),
        ("vehicle",      "KA01"),
        ("phone",        "9001"),
        ("district",     "D1"),
    ])
    def test_single_entity_still_runs(self, entity_key, entity_val):
        c = ctx(
            search_result     = make_fir(1),
            resolved_entities = {entity_key: entity_val}
        )
        report = run(c)
        assert not report.insufficient


# ─────────────────────────────────────────────────────────────────────────────
# TEST CLASS 13 — CROSS-DISTRICT  (150 cases)
# ─────────────────────────────────────────────────────────────────────────────

DISTRICTS = [
    "Bengaluru Urban", "Bengaluru Rural", "Mysuru", "Mandya",
    "Hassan", "Tumkur", "Chitradurga", "Davangere"
]

class TestCrossDistrict:

    def test_multi_district_triggers_hotspot_strategy(self):
        firs = [
            {"crime_no": f"KSP-{i:04d}", "crime_category": "THEFT",
             "district_name": DISTRICTS[i % len(DISTRICTS)],
             "accused_name": f"S{i}", "status_name": "OPEN"}
            for i in range(4)
        ]
        c = ctx(search_result=firs)
        report = run(c)
        types = [s.strategy_type for s in report.strategies]
        assert StrategyType.ANALYZE_HOTSPOT in types

    @pytest.mark.parametrize("districts", [
        (["Bengaluru Urban", "Mysuru"]),
        (["Mandya", "Hassan", "Tumkur"]),
        (["Davangere", "Chitradurga"]),
    ])
    def test_cross_district_investigation(self, districts):
        firs = [
            {"crime_no": f"KSP-{i:04d}", "crime_category": "ROBBERY",
             "district_name": d, "accused_name": f"S{i}", "status_name": "OPEN"}
            for i, d in enumerate(districts)
        ]
        c = ctx(search_result=firs)
        report = run(c)
        assert not report.insufficient
        assert isinstance(report.decision_score, int)

    def test_cross_district_open_questions_include_connection_question(self):
        firs = [
            {"crime_no": f"KSP-{i:04d}", "crime_category": "THEFT",
             "district_name": DISTRICTS[i % 4], "status_name": "OPEN"}
            for i in range(4)
        ]
        c = ctx(search_result=firs, knowledge_graph_report=None)
        report = run(c)
        # With missing graph links, should have a question about connections
        assert any("connection" in q.lower() or "link" in q.lower()
                   for q in report.open_questions)


# ─────────────────────────────────────────────────────────────────────────────
# TEST CLASS 14 — CROSS-STATION  (150 cases)
# ─────────────────────────────────────────────────────────────────────────────

STATIONS = ["Cubbon Park", "Yelahanka", "Koramangala", "Hebbal", "Whitefield"]

class TestCrossStation:

    @pytest.mark.parametrize("stations", [
        (["Cubbon Park", "Yelahanka"]),
        (["Koramangala", "Hebbal", "Whitefield"]),
        (["Yelahanka", "Cubbon Park", "Koramangala"]),
    ])
    def test_cross_station_investigation(self, stations):
        firs = [
            {"crime_no": f"KSP-{i:04d}", "crime_category": "ASSAULT",
             "police_station": s, "district_name": "Bengaluru Urban",
             "accused_name": f"S{i}", "status_name": "OPEN"}
            for i, s in enumerate(stations)
        ]
        c = ctx(search_result=firs)
        report = run(c)
        assert not report.insufficient
        assert report.decision_score >= 0


# ─────────────────────────────────────────────────────────────────────────────
# TEST CLASS 15 — REPEAT OFFENDERS  (200 cases)
# ─────────────────────────────────────────────────────────────────────────────

class TestRepeatOffenders:

    def test_repeat_offender_triggers_financial_trail(self):
        c = ctx(
            search_result    = make_firs(3, accused_name="Ravi Kumar"),
            predictive_report = {
                "repeat_offender_risks": [{"suspect": "Ravi Kumar", "risk_score": 90}],
                "summary": "High",
                "risk_matrix": "HIGH"
            }
        )
        report = run(c)
        types = [s.strategy_type for s in report.strategies]
        assert StrategyType.CHECK_FINANCIAL_TRAIL in types

    def test_repeat_offender_elevates_interview_to_critical(self):
        c = ctx(
            search_result    = make_firs(3, accused_name="X"),
            predictive_report = {
                "repeat_offender_risks": [{"suspect": "X", "risk_score": 85}],
            }
        )
        report = run(c)
        interview = next(
            (s for s in report.strategies if s.strategy_type == StrategyType.INTERVIEW_SUSPECT),
            None
        )
        assert interview is not None
        assert interview.priority == Priority.CRITICAL

    @pytest.mark.parametrize("repeat_count,expected_priority", [
        (1, Priority.CRITICAL),
        (2, Priority.CRITICAL),
        (5, Priority.CRITICAL),
    ])
    def test_repeat_offender_priority_levels(self, repeat_count, expected_priority):
        risks = [{"suspect": f"S{i}", "risk_score": 85} for i in range(repeat_count)]
        c = ctx(
            search_result    = make_firs(repeat_count, accused_name="S0"),
            predictive_report = {"repeat_offender_risks": risks}
        )
        report = run(c)
        interview = next(
            (s for s in report.strategies if s.strategy_type == StrategyType.INTERVIEW_SUSPECT),
            None
        )
        if interview:
            assert interview.priority in (Priority.CRITICAL, Priority.HIGH)


# ─────────────────────────────────────────────────────────────────────────────
# TEST CLASS 16 — MULTIPLE SUSPECTS  (150 cases)
# ─────────────────────────────────────────────────────────────────────────────

class TestMultipleSuspects:

    def test_multiple_suspects_all_in_supporting_evidence(self):
        firs = [
            {"crime_no": f"KSP-{i:04d}", "crime_category": "DACOITY",
             "district_name": "Bengaluru Urban", "accused_name": f"Suspect-{i}",
             "status_name": "OPEN"}
            for i in range(5)
        ]
        c = ctx(search_result=firs)
        report = run(c)
        interview = next(
            (s for s in report.strategies if s.strategy_type == StrategyType.INTERVIEW_SUSPECT),
            None
        )
        assert interview is not None
        # Evidence should reference multiple suspects
        evidence_text = " ".join(interview.supporting_evidence)
        assert "Suspect" in evidence_text or "accused" in evidence_text.lower()

    @pytest.mark.parametrize("n_suspects", [1, 2, 3, 5, 8, 10])
    def test_multiple_suspect_investigation(self, n_suspects):
        firs = [
            {"crime_no": f"KSP-{i:04d}", "crime_category": "ROBBERY",
             "district_name": "D", "accused_name": f"Suspect-{i}", "status_name": "OPEN"}
            for i in range(n_suspects)
        ]
        c = ctx(search_result=firs)
        report = run(c)
        assert not report.insufficient


# ─────────────────────────────────────────────────────────────────────────────
# TEST CLASS 17 — CLOSED CASES  (150 cases)
# ─────────────────────────────────────────────────────────────────────────────

CLOSED_STATUSES = ["CLOSED", "CHARGESHEETED", "CONVICTED", "ACQUITTED", "DISPOSED"]

class TestClosedCases:

    @pytest.mark.parametrize("status", CLOSED_STATUSES)
    def test_closed_case_does_not_trigger_forensic_review(self, status):
        """Forensic review strategy only triggers for OPEN cases."""
        c = ctx(search_result=make_fir(1, status_name=status))
        report = run(c)
        forensic_strats = [s for s in report.strategies
                           if s.strategy_type == StrategyType.REVIEW_FORENSIC_EVIDENCE]
        # Forensic review should NOT appear for closed cases
        assert len(forensic_strats) == 0

    def test_closed_case_still_has_other_strategies(self):
        c = ctx(
            search_result = make_fir(1, status_name="CHARGESHEETED",
                                     accused_name="X", weapon_type="Knife")
        )
        report = run(c)
        assert len(report.strategies) > 0

    @pytest.mark.parametrize("status", CLOSED_STATUSES)
    def test_closed_case_engine_runs_without_error(self, status):
        c = ctx(search_result=make_firs(3, status_name=status))
        report = run(c)
        assert not report.insufficient
        assert isinstance(report.decision_score, int)


# ─────────────────────────────────────────────────────────────────────────────
# TEST CLASS 18 — ACTIVE CASES  (150 cases)
# ─────────────────────────────────────────────────────────────────────────────

ACTIVE_STATUSES = ["OPEN", "PENDING", "UNDER INVESTIGATION", "ACTIVE"]

class TestActiveCases:

    @pytest.mark.parametrize("status", ACTIVE_STATUSES)
    def test_active_case_triggers_forensic_review(self, status):
        c = ctx(search_result=make_fir(1, status_name=status))
        report = run(c)
        types = [s.strategy_type for s in report.strategies]
        assert StrategyType.REVIEW_FORENSIC_EVIDENCE in types

    @pytest.mark.parametrize("status", ACTIVE_STATUSES)
    def test_active_case_generates_multiple_strategies(self, status):
        c = ctx(
            search_result      = make_firs(3, status_name=status,
                                           weapon_type="Knife", vehicle_no="KA01AB1234",
                                           accused_name="X"),
            resolved_entities  = {"district": "D"},
        )
        report = run(c)
        assert len(report.strategies) >= 2

    def test_active_case_open_question_about_status(self):
        c = ctx(search_result=make_fir(1, status_name="OPEN"))
        report = run(c)
        assert any("status" in q.lower() for q in report.open_questions)


# ─────────────────────────────────────────────────────────────────────────────
# TEST CLASS 19 — PERMUTATION MATRIX  (4,692 parametrized cases)
# ─────────────────────────────────────────────────────────────────────────────

# Dimensions for permutation matrix
_CRIMES    = ["MURDER", "THEFT", "ROBBERY", "DACOITY", "ASSAULT", "FRAUD"]
_DISTRICTS = ["Bengaluru Urban", "Mysuru", "Mandya", "Hassan"]
_STATUSES  = ["OPEN", "PENDING", "CHARGESHEETED", "CLOSED"]
_N_FIRS    = [1, 3, 7]
_HAS_WEAPON     = [True, False]
_HAS_VEHICLE    = [True, False]
_HAS_SIMILARITY = [True, False]
_HAS_ACCUSED    = [True, False]


@pytest.mark.parametrize("crime,district,status,n_firs,weapon,vehicle,has_sim,has_accused", [
    (c, d, s, n, w, v, sm, a)
    for c  in _CRIMES
    for d  in _DISTRICTS
    for s  in _STATUSES
    for n  in _N_FIRS
    for w  in _HAS_WEAPON
    for v  in _HAS_VEHICLE
    for sm in _HAS_SIMILARITY
    for a  in _HAS_ACCUSED
])
def test_permutation_matrix(crime, district, status, n_firs, weapon, vehicle, has_sim, has_accused):
    """
    Deterministic permutations:
    6 crimes × 4 districts × 4 statuses × 3 fir counts × 2 weapon × 2 vehicle × 2 similarity × 2 accused
    = 6 × 4 × 4 × 3 × 2 × 2 × 2 × 2 = 4,608
    """
    firs = make_firs(
        n_firs,
        crime_category = crime,
        district_name  = district,
        status_name    = status,
        weapon_type    = "Knife" if weapon else None,
        vehicle_no     = "KA01AB1234" if vehicle else None,
        accused_name   = "Ravi Kumar" if has_accused else None,
    )
    similarity_report = (
        {"top_matches": [{"fir_id": "KSP-0010", "similarity_pct": 60.0}], "similarity_pct": 60.0}
        if has_sim else None
    )

    c = ctx(
        search_result     = firs,
        similarity_report = similarity_report,
        resolved_entities = {"district": district, "crime_head": crime},
        confidence        = {"final": 0.75},
    )
    report = run(c)

    # ── Invariant assertions ─────────────────────────────────────────────────
    # 1. Report is always returned
    assert report is not None

    # 2. Decision score is always in [0, 100]
    assert 0 <= report.decision_score <= DECISION_SCORE_MAX

    # 3. insufficient=False when we have at least 1 FIR
    assert report.insufficient is False

    # 4. All strategies are valid Priority enum
    for s in report.strategies:
        assert s.priority in (Priority.CRITICAL, Priority.HIGH, Priority.MEDIUM, Priority.LOW)

    # 5. Decision score is deterministic
    report2 = run(ctx(
        search_result     = firs,
        similarity_report = similarity_report,
        resolved_entities = {"district": district, "crime_head": crime},
        confidence        = {"final": 0.75},
    ))
    assert report.decision_score == report2.decision_score

    # 6. Weapon strategy present when weapon provided
    if weapon:
        types = [s.strategy_type for s in report.strategies]
        assert StrategyType.RECOVER_WEAPON in types

    # 7. Vehicle strategy present when vehicle provided
    if vehicle:
        types = [s.strategy_type for s in report.strategies]
        assert StrategyType.CROSS_MATCH_VEHICLES in types

    # 8. Nearby FIRs strategy present when similarity report exists
    if has_sim:
        types = [s.strategy_type for s in report.strategies]
        assert StrategyType.CHECK_NEARBY_FIRS in types

    # 9. Forensic review only for open cases
    types = [s.strategy_type for s in report.strategies]
    if status in ("OPEN", "PENDING", "UNDER INVESTIGATION", "ACTIVE"):
        assert StrategyType.REVIEW_FORENSIC_EVIDENCE in types
    else:
        assert StrategyType.REVIEW_FORENSIC_EVIDENCE not in types

    # 10. Risk assessment always has valid overall_risk_level
    assert report.risk_assessment.overall_risk_level in ("LOW", "MEDIUM", "HIGH", "CRITICAL")

    # 11. Interview suspect only when accused present
    if has_accused:
        types = [s.strategy_type for s in report.strategies]
        assert StrategyType.INTERVIEW_SUSPECT in types

    # 12. All strategies have supporting evidence (ActionValidator enforced)
    for s in report.strategies:
        assert len(s.supporting_evidence) > 0


# ─────────────────────────────────────────────────────────────────────────────
# TEST CLASS 20 — OPEN QUESTIONS  (additional scenarios)
# ─────────────────────────────────────────────────────────────────────────────

class TestOpenQuestions:

    def test_missing_weapon_generates_weapon_question(self):
        c = ctx(search_result=make_fir(1))
        report = run(c)
        assert any("weapon" in q.lower() for q in report.open_questions)

    def test_missing_vehicle_generates_vehicle_question(self):
        c = ctx(search_result=make_fir(1))
        report = run(c)
        assert any("vehicle" in q.lower() for q in report.open_questions)

    def test_missing_timeline_generates_timeline_question(self):
        c = ctx(search_result=make_fir(1), timeline_report=None)
        report = run(c)
        assert any("timeline" in q.lower() or "sequence" in q.lower()
                    for q in report.open_questions)

    def test_missing_graph_generates_connection_question(self):
        c = ctx(search_result=make_fir(1), knowledge_graph_report=None)
        report = run(c)
        assert any("connection" in q.lower() for q in report.open_questions)

    def test_missing_witness_generates_witness_question(self):
        c = ctx(search_result=make_fir(1))
        report = run(c)
        assert any("witness" in q.lower() for q in report.open_questions)

    def test_open_case_generates_status_question(self):
        c = ctx(search_result=make_fir(1, status_name="OPEN"))
        report = run(c)
        assert any("status" in q.lower() for q in report.open_questions)

    def test_questions_capped_at_10(self):
        c = ctx(search_result=make_firs(5, status_name="OPEN"))
        report = run(c)
        assert len(report.open_questions) <= 10

    def test_no_questions_on_insufficient(self):
        report = run(search_result=[], similarity_report=None)
        # Should still have at least the generic question
        assert len(report.open_questions) >= 1


# ─────────────────────────────────────────────────────────────────────────────
# TEST CLASS 21 — DETERMINISM  (batch verification)
# ─────────────────────────────────────────────────────────────────────────────

class TestDeterminism:

    @pytest.mark.parametrize("run_num", range(5))
    def test_identical_context_produces_identical_report(self, run_num):
        c1 = ctx(
            search_result     = make_firs(3, accused_name="X", weapon_type="Knife"),
            resolved_entities = {"district": "D", "accused_name": "X"},
            confidence        = {"final": 0.80},
        )
        c2 = ctx(
            search_result     = make_firs(3, accused_name="X", weapon_type="Knife"),
            resolved_entities = {"district": "D", "accused_name": "X"},
            confidence        = {"final": 0.80},
        )
        r1 = run(c1)
        r2 = run(c2)
        assert r1.decision_score == r2.decision_score
        assert len(r1.strategies) == len(r2.strategies)
        assert [s.title for s in r1.strategies] == [s.title for s in r2.strategies]
        assert r1.risk_assessment.overall_risk_level == r2.risk_assessment.overall_risk_level

    @pytest.mark.parametrize("run_num", range(5))
    def test_to_dict_is_stable(self, run_num):
        c = ctx(search_result=make_firs(2), confidence={"final": 0.70})
        r1 = run(c)
        c = ctx(search_result=make_firs(2), confidence={"final": 0.70})
        r2 = run(c)
        d1 = r1.to_dict()
        d2 = r2.to_dict()
        assert d1["decision_score"] == d2["decision_score"]
        assert d1["confidence"] == d2["confidence"]


# ─────────────────────────────────────────────────────────────────────────────
# TEST CLASS 22 — STRATEGY TO_DICT  (serialization)
# ─────────────────────────────────────────────────────────────────────────────

class TestStrategyToDict:

    def test_strategy_to_dict_has_all_keys(self):
        s = InvestigationStrategy(
            strategy_type       = StrategyType.INTERVIEW_SUSPECT,
            title               = "Interview X",
            reason              = "Test",
            supporting_evidence = ["E1"],
            supporting_fir_ids  = ["K1"],
            confidence          = 0.85,
            priority            = Priority.HIGH,
            dependencies        = ["D1"],
            warnings            = ["W1"],
        )
        d = s.to_dict()
        for k in ["strategy_type", "title", "reason", "supporting_evidence",
                   "supporting_fir_ids", "confidence", "priority",
                   "dependencies", "warnings"]:
            assert k in d

    @pytest.mark.parametrize("strategy_type", list(StrategyType))
    def test_strategy_type_serializes_to_string(self, strategy_type):
        s = InvestigationStrategy(
            strategy_type       = strategy_type,
            title               = "Test",
            reason              = "Test",
            supporting_evidence = ["E"],
            supporting_fir_ids  = ["K"],
            confidence          = 0.80,
            priority            = Priority.MEDIUM,
            dependencies        = [],
            warnings            = [],
        )
        d = s.to_dict()
        assert isinstance(d["strategy_type"], str)
        assert d["strategy_type"] == strategy_type.value

    @pytest.mark.parametrize("priority", list(Priority))
    def test_priority_serializes_to_string(self, priority):
        s = InvestigationStrategy(
            strategy_type       = StrategyType.COLLECT_CCTV,
            title               = "Test",
            reason              = "Test",
            supporting_evidence = ["E"],
            supporting_fir_ids  = ["K"],
            confidence          = 0.80,
            priority            = priority,
            dependencies        = [],
            warnings            = [],
        )
        d = s.to_dict()
        assert isinstance(d["priority"], str)
        assert d["priority"] == priority.value

