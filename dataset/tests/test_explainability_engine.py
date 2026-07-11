import unittest
import time
from typing import Dict, Any, List
from app.ai.explainability_engine import ExplainabilityEngine

class MockIntentResult:
    def __init__(self, intent: str, confidence: float, is_multi_intent: bool = False, is_conversational: bool = False, clarification_required: bool = False):
        self.intent = intent
        self.confidence = confidence
        self.is_multi_intent = is_multi_intent
        self.is_conversational = is_conversational
        self.clarification_required = clarification_required

class MockExecutionContext:
    def __init__(
        self,
        raw_query: str,
        intent: str,
        resolved_entities: Dict[str, Any],
        search_result: List[Dict[str, Any]],
        confidence_metrics: Dict[str, Any],
        reasoning_result: Dict[str, Any],
        hallucination_safe: bool,
        hallucination_violations: List[Dict[str, str]],
        intelligence_bundle_trace: List[str] = None
    ):
        self.raw_query = raw_query
        self.conversation_id = "test_conversation"
        self.intent = intent
        self.intent_result = MockIntentResult(intent, 0.90)
        self.resolved_entities = resolved_entities
        self.search_result = search_result
        self.confidence_metrics = confidence_metrics
        self.reasoning_result = reasoning_result
        self.hallucination_safe = hallucination_safe
        self.hallucination_violations = hallucination_violations
        
        # Build intelligence bundle
        class MockIntelBundle:
            def __init__(self, trace):
                self.execution_trace = trace
                self.hotspots = [{"latitude": 12.9, "longitude": 77.5}] if "Hotspot" in trace else []
                self.network = {"nodes": [{"id": 1}], "edges": [{"from": 1, "to": 2}]} if "Network" in trace else {}
                self.repeat_offender = {"results": []} if "RepeatOffender" in trace else {}
                self.similar_cases = [] if "Similarity" in trace else []
                self.pattern_analysis = "Patterns" if "Pattern" in trace else ""
                self.recommendations = [{"action": "Action", "priority": "HIGH", "reason": "Reason", "confidence": 0.9}] if "Recommendation" in trace else []

        self.intelligence_bundle = MockIntelBundle(intelligence_bundle_trace or [])
        
        self.confidence = {"final": confidence_metrics.get("confidence", 0.90)}
        self.is_followup = False
        self.start_time = time.time()
        self.select_stmt = "SELECT * FROM mock;"
        self.warnings = ["Test Warning"]
        self.plan = ["ExplainabilityEngineStage"]
        self.execution_trace = [
            {"stage": "SearchServiceStage", "latency_ms": 1.5, "decision": "Executed", "skipped": False, "executed": True},
            {"stage": "HallucinationGuardStage", "latency_ms": 0.8, "decision": "Executed", "skipped": False, "executed": True}
        ]

class TestExplainabilityEngine(unittest.TestCase):
    
    def test_explainability_matrix(self):
        """
        Dynamically run 672 mock test cases testing various intent, entity,
        safety, reasoning, and analytics engine states.
        """
        intents = ["SEARCH_CASES", "SEARCH_ACCUSED", "SEARCH_VICTIMS", "FIR_LOOKUP", "NETWORK_SEARCH", "HOTSPOT", "PREDICT_CRIME"]
        entity_sets = [
            {"crime_category": "THEFT", "district": "Mysuru"},
            {"accused_name": "Raju", "police_station": "Hubli"},
            {"victim_name": "Ganesh", "district": "Bengaluru Urban"},
            {"identifiers": ["KSP-0001"]}
        ]
        results_variants = [
            [],
            [{"crime_no": "KSP-0001", "district_name": "Mysuru", "crime_category": "THEFT"}],
            [{"crime_no": "KSP-0001"}, {"crime_no": "KSP-0002"}]
        ]
        safety_states = [
            (True, []),
            (False, [{"category": "names", "detail": "Name was not verified."}])
        ]
        analytics_traces = [
            ["Hotspot", "Pattern"],
            ["Network", "RepeatOffender"],
            ["Similarity", "Recommendation"],
            []
        ]

        test_count = 0
        for intent in intents:
            for ents in entity_sets:
                for res in results_variants:
                    for safe, violations in safety_states:
                        for trace in analytics_traces:
                            # Generate a test case context
                            context = MockExecutionContext(
                                raw_query="Mock query description here",
                                intent=intent,
                                resolved_entities=ents,
                                search_result=res,
                                confidence_metrics={"confidence": 0.85, "risk": "LOW", "explanation": ["Filters match"]},
                                reasoning_result={"reason_chain": ["Step 1", "Step 2"], "conclusion": "Approved"},
                                hallucination_safe=safe,
                                hallucination_violations=violations,
                                intelligence_bundle_trace=trace
                            )
                            
                            report = ExplainabilityEngine.generate_explanation(context)
                            
                            # Verify Schema Presence
                            self.assertIn("execution_id", report)
                            self.assertIn("conversation_id", report)
                            self.assertIn("intent", report)
                            self.assertIn("resolved_entities", report)
                            self.assertIn("query_summary", report)
                            self.assertIn("sql_summary", report)
                            self.assertIn("reasoning_summary", report)
                            self.assertIn("analytics_used", report)
                            self.assertIn("recommendation_sources", report)
                            self.assertIn("confidence_breakdown", report)
                            self.assertIn("hallucination_checks", report)
                            self.assertIn("clarification_history", report)
                            self.assertIn("pipeline_execution", report)
                            self.assertIn("warnings", report)
                            self.assertIn("limitations", report)
                            
                            # Mode verification
                            self.assertIn("officer_mode", report)
                            self.assertIn("developer_mode", report)
                            self.assertIn("audit_mode", report)
                            
                            # Mode specific fields
                            self.assertTrue(len(report["officer_mode"]["concise_explanation"]) <= 5)
                            self.assertIn("modules", report["developer_mode"])
                            self.assertEqual(report["audit_mode"]["execution_id"], report["execution_id"])
                            
                            test_count += 1

        print(f"ExplainabilityEngine: Executed {test_count} dynamic test cases successfully.")
        self.assertTrue(test_count >= 500, f"Expected at least 500 test cases, but ran {test_count}")

if __name__ == "__main__":
    unittest.main()
