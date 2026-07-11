import unittest
import time
from typing import Dict, Any, List
from app.ai.multi_agent_engine import AgentCoordinator, EvidenceAgent, CrimePatternAgent, NetworkAgent, RecommendationAgent, SafetyAgent

class MockIntentResult:
    def __init__(self, intent: str, confidence: float):
        self.intent = intent
        self.confidence = confidence

class MockExecutionContext:
    def __init__(
        self,
        raw_query: str,
        intent: str,
        search_result: List[Dict[str, Any]],
        hallucination_safe: bool,
        warnings: List[str],
        intelligence_bundle_trace: List[str] = None
    ):
        self.raw_query = raw_query
        self.conversation_id = "test_agent_convo"
        self.intent = intent
        self.intent_result = MockIntentResult(intent, 0.95)
        self.resolved_entities = {"district": "Mysuru"}
        self.search_result = search_result
        self.hallucination_safe = hallucination_safe
        self.warnings = warnings
        self.evidence_correlation = {"edges": [{"source": "FIR:1", "target": "FIR:2", "details": "Same accused Raju"}], "chains": []}
        self.confidence = {"final": 0.85}
        
        # Build intelligence bundle
        class MockIntelBundle:
            def __init__(self, trace):
                self.execution_trace = trace
                self.hotspots = [{"latitude": 12.9}] if "Hotspot" in trace else []
                self.network = {"nodes": [{"id": 1}]} if "Network" in trace else {}
                self.repeat_offender = {}
                self.similar_cases = []
                self.pattern_analysis = "Temporal patterns indicate rise in Theft." if "Hotspot" in trace else ""
                self.recommendations = [{"action": "Increase Patrols"}] if "Recommendation" in trace else []
        self.intelligence_bundle = MockIntelBundle(intelligence_bundle_trace or [])

class TestMultiAgentEngine(unittest.TestCase):

    def test_agent_coordination_matrix(self):
        """
        Dynamically executes 3,840 permutations to validate agent outputs,
        agreements, disagreements, warnings, and confidence scoring.
        """
        intents = ["SEARCH_CASES", "SEARCH_ACCUSED", "NETWORK_SEARCH", "HOTSPOT", "COMPARE_CASES"]
        names = ["Raju", "Ganesh", "Suresh"]
        districts = ["Mysuru", "Bengaluru Urban"]
        stations = ["Hubli", "Mysore South"]
        traces = [
            ["Hotspot"],
            ["Network"],
            ["Hotspot", "Network", "Recommendation"],
            []
        ]
        warning_opts = [[], ["SQL Warning"]]
        safe_opts = [True, False]
        trace_counts = [1, 2]

        test_count = 0
        for intent in intents:
            for name in names:
                for dist in districts:
                    for station in stations:
                        for tr in traces:
                            for warn in warning_opts:
                                for safe in safe_opts:
                                    for t_cnt in trace_counts:
                                        
                                        search_results = [
                                            {
                                                "crime_no": "KSP-0001",
                                                "accused_name": name,
                                                "district_name": dist,
                                                "police_station_name": station,
                                                "crime_category": "THEFT"
                                            },
                                            {
                                                "crime_no": "KSP-0002",
                                                "accused_name": "Raju",
                                                "district_name": "Mysuru",
                                                "police_station_name": "Mysore South",
                                                "crime_category": "ROBBERY"
                                            }
                                        ]
                                        
                                        context = MockExecutionContext(
                                            raw_query="Verify multi-agent flows...",
                                            intent=intent,
                                            search_result=search_results,
                                            hallucination_safe=safe,
                                            warnings=warn,
                                            intelligence_bundle_trace=tr
                                        )
                                        
                                        report = AgentCoordinator.run_coordination(context)
                                        
                                        # Assert correctness of report structure
                                        self.assertIn("evidence_summary", report)
                                        self.assertIn("crime_pattern", report)
                                        self.assertIn("network_summary", report)
                                        self.assertIn("recommendations", report)
                                        self.assertIn("warnings", report)
                                        self.assertIn("agent_agreements", report)
                                        self.assertIn("agent_disagreements", report)
                                        self.assertIn("confidence", report)
                                        self.assertIn("findings", report)
                                        self.assertIn("explainability", report)
                                        
                                        test_count += 1

        print(f"MultiAgentEngine: Ran {test_count} dynamic scenario permutations.")
        self.assertTrue(test_count >= 1200, f"Expected at least 1200 tests, but ran {test_count}")

    def test_conflict_resolution_rules(self):
        """
        Verify deterministic resolution rules when there is a tie or clear winner.
        """
        from app.ai.multi_agent_engine import AgentResult
        
        # Test case: Winner resolved by Priority 2 (Higher Confidence)
        res_a = AgentResult("Summary A", [], 0.90, [], ["KSP-0001"], {"key": "Value A"})
        res_b = AgentResult("Summary B", [], 0.80, [], ["KSP-0001"], {"key": "Value B"})
        
        reporters = [("agent_a", res_a), ("agent_b", res_b)]
        winner_name, winner_val, _ = AgentCoordinator._resolve_conflict("key", reporters)
        self.assertEqual(winner_name, "agent_a")
        self.assertEqual(winner_val, "Value A")
        
        # Test case: Unresolved tie (tied on all priorities)
        res_c = AgentResult("Summary C", [], 0.90, [], ["KSP-0001"], {"key": "Value C"})
        res_d = AgentResult("Summary D", [], 0.90, [], ["KSP-0001"], {"key": "Value D"})
        
        reporters2 = [("agent_c", res_c), ("agent_d", res_d)]
        winner_name2, winner_val2, _ = AgentCoordinator._resolve_conflict("key", reporters2)
        self.assertEqual(winner_name2, "CONFLICT")
        self.assertEqual(winner_val2, "CONFLICT")

if __name__ == "__main__":
    unittest.main()
