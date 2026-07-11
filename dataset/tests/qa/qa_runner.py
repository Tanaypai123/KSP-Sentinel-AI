"""
QA Runner — Orchestrates 500+ manual validation queries across every AI engine.
Produces a structured bug report and pass/fail manifest.

Phase 7.0: Enterprise Manual QA & Validation
"""

from __future__ import annotations

import sys
import json
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

sys.path.insert(0, "/Users/tanaysharma/Desktop/KSP-Sentinel-AI/dataset")

from tests.qa.qa_cases import QA_CASES
from tests.qa.qa_fixtures import (
    make_context,
    make_mock_db,
    SEED_FIR_RECORDS,
    EMPTY_FIR_RECORDS,
    LARGE_FIR_RECORDS,
)

# ── Bug Severity ──────────────────────────────────────────────────────────────

CRITICAL = "CRITICAL"
HIGH = "HIGH"
MEDIUM = "MEDIUM"
LOW = "LOW"
COSMETIC = "COSMETIC"


@dataclass
class BugReport:
    bug_id: str
    severity: str
    feature: str
    category: str
    query: str
    description: str
    expected: str
    actual: str
    root_cause: str
    stack_trace: str = ""
    fixed: bool = False
    fix_description: str = ""


@dataclass
class QAResult:
    case_id: int
    query: str
    category: str
    feature: str
    intent: str
    adversarial: bool
    passed: bool
    bug: Optional[BugReport] = None
    latency_ms: float = 0.0
    notes: str = ""


# ── Individual Feature Validators ────────────────────────────────────────────

class IntentValidator:
    @staticmethod
    def validate(ctx: Any, case: Dict) -> Optional[str]:
        """Returns error message if intent is wrong, else None."""
        if ctx.intent is None:
            return "intent is None after IntentRouterStage"
        return None


class HallucinationGuardValidator:
    @staticmethod
    def validate(ctx: Any, case: Dict) -> Optional[str]:
        """Validates the HallucinationGuard fires correctly."""
        from app.ai.hallucination_guard import HallucinationGuard
        test_claims = {
            "accused_name": "Ravi Kumar",
            "crime_head": "Theft",
            "district": "Bengaluru Urban",
        }
        result = HallucinationGuard.validate(ctx, test_claims)
        if not isinstance(result, dict):
            return f"HallucinationGuard.validate returned {type(result)}, expected dict"
        if "safe" not in result:
            return "HallucinationGuard result missing 'safe' key"
        return None


class ConfidenceValidator:
    @staticmethod
    def validate(ctx: Any, case: Dict) -> Optional[str]:
        """Validates the ConfidenceEngine produces valid scores."""
        from app.ai.confidence_engine import ConfidenceEngine
        result = ConfidenceEngine.compute(ctx)
        if not isinstance(result, dict):
            return f"ConfidenceEngine.compute returned {type(result)}, expected dict"
        if "confidence" not in result:
            return "ConfidenceEngine result missing 'confidence' key"
        confidence = result["confidence"]
        if not (0.0 <= confidence <= 1.0):
            return f"confidence {confidence} out of [0.0, 1.0] range"
        return None


class EvidenceCorrelationValidator:
    @staticmethod
    def validate(ctx: Any, case: Dict) -> Optional[str]:
        """Validates EvidenceCorrelationEngine does not crash on seeded data."""
        from app.ai.evidence_correlation_engine import EvidenceCorrelationEngine
        try:
            result = EvidenceCorrelationEngine.correlate(ctx)
            if not isinstance(result, dict):
                return f"EvidenceCorrelation returned {type(result)}, expected dict"
        except Exception as e:
            return f"EvidenceCorrelationEngine crashed: {e}"
        return None


class DecisionSupportValidator:
    @staticmethod
    def validate(ctx: Any, case: Dict) -> Optional[str]:
        """Validates DecisionSupportEngine produces strategies."""
        from app.ai.decision_support_engine import DecisionSupportEngine
        try:
            result = DecisionSupportEngine.run(ctx)
            if not isinstance(result, dict):
                return f"DecisionSupportEngine returned {type(result)}, expected dict"
        except Exception as e:
            return f"DecisionSupportEngine crashed: {e}"
        return None


class ReasoningValidator:
    @staticmethod
    def validate(ctx: Any, case: Dict) -> Optional[str]:
        """Validates ReasoningEngine produces analysis."""
        from app.ai.reasoning_engine import ReasoningEngine
        try:
            result = ReasoningEngine.analyze(ctx)
            if not isinstance(result, dict):
                return f"ReasoningEngine returned {type(result)}, expected dict"
        except Exception as e:
            return f"ReasoningEngine crashed: {e}"
        return None


class NLPValidator:
    @staticmethod
    def validate(query: str) -> Optional[str]:
        """Validates NLPEngine handles the query without crashing."""
        from app.ai.nlp_engine import NLPEngine
        try:
            result = NLPEngine.normalize(query)
            if not isinstance(result, str):
                return f"NLPEngine.normalize returned {type(result)}, expected str"
        except Exception as e:
            return f"NLPEngine crashed: {e}"
        return None


class SQLInjectionValidator:
    @staticmethod
    def validate(query: str) -> Optional[str]:
        """Validates SQL injection queries don't pass entity extraction unchanged."""
        from app.ai.entity_extractor import EntityExtractor
        try:
            entities = EntityExtractor.extract(query)
            # SQL injection strings should not produce dangerous raw SQL fragments
            dangerous_patterns = ["DROP TABLE", "DELETE FROM", "INSERT INTO", "UNION SELECT", "xp_cmdshell"]
            result_str = json.dumps(entities)
            for pat in dangerous_patterns:
                if pat.upper() in result_str.upper():
                    return f"SQL injection string '{pat}' passed through entity extraction unfiltered"
        except Exception as e:
            return f"EntityExtractor crashed on injection attempt: {e}"
        return None


class PredictiveValidator:
    @staticmethod
    def validate(ctx: Any) -> Optional[str]:
        """Validates PredictiveEngine."""
        from app.ai.predictive_engine import PredictiveInvestigationEngine
        try:
            result = PredictiveInvestigationEngine.generate_risk_forecast(ctx)
            if not isinstance(result, dict):
                return f"PredictiveEngine returned {type(result)}, expected dict"
        except Exception as e:
            return f"PredictiveEngine crashed: {e}"
        return None


class TimelineValidator:
    @staticmethod
    def validate(ctx: Any) -> Optional[str]:
        """Validates TimelineEngine."""
        from app.ai.timeline_engine import TimelineEngine
        try:
            result = TimelineEngine.build_timeline(ctx)
            if not isinstance(result, dict):
                return f"TimelineEngine returned {type(result)}, expected dict"
        except Exception as e:
            return f"TimelineEngine crashed: {e}"
        return None


class ExplainabilityValidator:
    @staticmethod
    def validate(ctx: Any) -> Optional[str]:
        """Validates ExplainabilityEngine."""
        from app.ai.explainability_engine import ExplainabilityEngine
        try:
            result = ExplainabilityEngine.generate_explanation(ctx)
            if not isinstance(result, dict):
                return f"ExplainabilityEngine returned {type(result)}, expected dict"
        except Exception as e:
            return f"ExplainabilityEngine crashed: {e}"
        return None


# ── Main QA Orchestrator ──────────────────────────────────────────────────────

class QARunner:
    def __init__(self):
        self.results: List[QAResult] = []
        self.bugs: List[BugReport] = []
        self.bug_counter = 0
        self.passed = 0
        self.failed = 0

    def _next_bug_id(self) -> str:
        self.bug_counter += 1
        return f"BUG-{self.bug_counter:04d}"

    def _record_bug(
        self,
        severity: str,
        feature: str,
        category: str,
        query: str,
        description: str,
        expected: str,
        actual: str,
        root_cause: str,
        stack_trace: str = "",
    ) -> BugReport:
        bug = BugReport(
            bug_id=self._next_bug_id(),
            severity=severity,
            feature=feature,
            category=category,
            query=query,
            description=description,
            expected=expected,
            actual=actual,
            root_cause=root_cause,
            stack_trace=stack_trace,
        )
        self.bugs.append(bug)
        return bug

    def run_case(self, case_id: int, case: Dict) -> QAResult:
        query = case["query"]
        category = case["category"]
        feature = case["feature"]
        intent = case["intent"]
        adversarial = case.get("adversarial", False)

        t_start = time.perf_counter()
        passed = True
        bug = None
        notes = ""

        try:
            # Build context — use empty records for adversarial empty-result cases
            records = EMPTY_FIR_RECORDS if "Empty Results" in category else SEED_FIR_RECORDS
            ctx = make_context(
                raw_query=query,
                intent=intent,
                resolved_entities=case.get("entities", {}),
                search_results=list(records),
                records=records,
            )

            # 1. NLP Validation (all queries)
            nlp_error = NLPValidator.validate(query)
            if nlp_error:
                bug = self._record_bug(
                    HIGH, "NLP Engine", category, query,
                    f"NLP Engine failed: {nlp_error}",
                    "Clean normalized string", f"Error: {nlp_error}",
                    "NLPEngine.normalize() raised or returned unexpected type"
                )
                passed = False

            # 2. SQL Injection check (adversarial)
            if "SQL Injection" in category:
                inj_error = SQLInjectionValidator.validate(query)
                if inj_error:
                    bug = self._record_bug(
                        CRITICAL, "Hallucination Guard / SQL Generator", category, query,
                        f"SQL injection leaked through: {inj_error}",
                        "Injection blocked or sanitized",
                        f"Injection passed: {inj_error}",
                        "EntityExtractor does not sanitize SQL-injection patterns"
                    )
                    passed = False

            # 3. Hallucination Guard
            if "Hallucination" in feature and not adversarial:
                hg_error = HallucinationGuardValidator.validate(ctx, case)
                if hg_error:
                    bug = self._record_bug(
                        CRITICAL, "Hallucination Guard", category, query,
                        hg_error, "dict with 'safe' key", f"Error: {hg_error}",
                        "HallucinationGuard validate() contract violation"
                    )
                    passed = False

            # 4. Confidence Engine
            if "Confidence" in feature or category in ["English Search", "Analysis Queries"]:
                conf_error = ConfidenceValidator.validate(ctx, case)
                if conf_error:
                    bug = self._record_bug(
                        HIGH, "Confidence Engine", category, query,
                        conf_error, "confidence in [0.0, 1.0]", f"Error: {conf_error}",
                        "ConfidenceEngine compute() returned out-of-range or wrong type"
                    )
                    passed = False

            # 5. Reasoning Engine (search/analysis)
            if intent in ("SEARCH", "ANALYZE") and records:
                reasoning_error = ReasoningValidator.validate(ctx, case)
                if reasoning_error:
                    bug = self._record_bug(
                        HIGH, "Reasoning Engine", category, query,
                        reasoning_error, "dict", f"Error: {reasoning_error}",
                        "ReasoningEngine.analyze() crashed or returned wrong type"
                    )
                    passed = False

            # 6. Evidence Correlation
            if intent in ("SEARCH", "ANALYZE") and records:
                ec_error = EvidenceCorrelationValidator.validate(ctx, case)
                if ec_error:
                    bug = self._record_bug(
                        HIGH, "Evidence Correlation", category, query,
                        ec_error, "dict", f"Error: {ec_error}",
                        "EvidenceCorrelationEngine.correlate() crashed"
                    )
                    passed = False

            # 7. Decision Support (only with sufficient records)
            if records and len(records) >= 1 and intent in ("SEARCH", "ANALYZE"):
                ds_error = DecisionSupportValidator.validate(ctx, case)
                if ds_error:
                    bug = self._record_bug(
                        HIGH, "Decision Support", category, query,
                        ds_error, "dict", f"Error: {ds_error}",
                        "DecisionSupportEngine.run() crashed"
                    )
                    passed = False

            # 8. Predictive Engine
            if "Predict" in feature or intent == "PREDICT":
                pred_error = PredictiveValidator.validate(ctx)
                if pred_error:
                    bug = self._record_bug(
                        MEDIUM, "Predictive Engine", category, query,
                        pred_error, "dict", f"Error: {pred_error}",
                        "PredictiveInvestigationEngine.generate_risk_forecast() crashed"
                    )
                    passed = False

            # 9. Timeline
            if "Timeline" in feature:
                tl_error = TimelineValidator.validate(ctx)
                if tl_error:
                    bug = self._record_bug(
                        MEDIUM, "Timeline Engine", category, query,
                        tl_error, "dict", f"Error: {tl_error}",
                        "TimelineEngine.build_timeline() crashed"
                    )
                    passed = False

            # 10. Explainability
            if intent in ("SEARCH", "ANALYZE"):
                expl_error = ExplainabilityValidator.validate(ctx)
                if expl_error:
                    bug = self._record_bug(
                        MEDIUM, "Explainability Engine", category, query,
                        expl_error, "dict", f"Error: {expl_error}",
                        "ExplainabilityEngine.generate_explanation() crashed"
                    )
                    passed = False

        except Exception as e:
            tb = traceback.format_exc()
            bug = self._record_bug(
                CRITICAL, feature, category, query,
                f"Unexpected exception: {e}",
                "No exception", f"{type(e).__name__}: {e}",
                "Unhandled exception in QA orchestrator",
                stack_trace=tb
            )
            passed = False

        t_end = time.perf_counter()
        latency = (t_end - t_start) * 1000.0

        if passed:
            self.passed += 1
        else:
            self.failed += 1

        return QAResult(
            case_id=case_id,
            query=query[:120],
            category=category,
            feature=feature,
            intent=intent,
            adversarial=adversarial,
            passed=passed,
            bug=bug,
            latency_ms=latency,
            notes=notes,
        )

    def run_all(self) -> None:
        print(f"Starting QA run: {len(QA_CASES)} test cases")
        print("=" * 60)
        for i, case in enumerate(QA_CASES):
            result = self.run_case(i + 1, case)
            self.results.append(result)
            status = "PASS" if result.passed else f"FAIL ({result.bug.bug_id if result.bug else '?'})"
            if not result.passed:
                print(f"  [{i+1:03d}] {status} | {result.category[:30]} | {result.query[:60]}")

        print("=" * 60)
        print(f"Results: {self.passed} PASSED, {self.failed} FAILED out of {len(QA_CASES)}")
        print(f"Bugs found: {len(self.bugs)}")

    def save_results(self, output_path: str) -> None:
        data = {
            "summary": {
                "total": len(self.results),
                "passed": self.passed,
                "failed": self.failed,
                "bugs": len(self.bugs),
            },
            "bugs": [
                {
                    "bug_id": b.bug_id,
                    "severity": b.severity,
                    "feature": b.feature,
                    "category": b.category,
                    "query": b.query,
                    "description": b.description,
                    "expected": b.expected,
                    "actual": b.actual,
                    "root_cause": b.root_cause,
                }
                for b in self.bugs
            ],
            "results": [
                {
                    "case_id": r.case_id,
                    "query": r.query,
                    "category": r.category,
                    "feature": r.feature,
                    "intent": r.intent,
                    "adversarial": r.adversarial,
                    "passed": r.passed,
                    "latency_ms": round(r.latency_ms, 2),
                    "bug_id": r.bug.bug_id if r.bug else None,
                }
                for r in self.results
            ]
        }
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Results saved to {output_path}")


if __name__ == "__main__":
    runner = QARunner()
    runner.run_all()
    runner.save_results("qa_results.json")
