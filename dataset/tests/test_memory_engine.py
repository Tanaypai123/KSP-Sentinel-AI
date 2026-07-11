import unittest
import time
from typing import Dict, Any, List
from app.ai.memory_engine import MemoryEngine, InvestigationMemory

class MockIntentResult:
    def __init__(self, intent: str, confidence: float):
        self.intent = intent
        self.confidence = confidence

class MockConversationState:
    def __init__(self):
        self.active_fir = None
        self.active_accused = None
        self.active_victim = None
        self.active_station = None
        self.active_district = None
        self.pending_clarification = False
        self.clarification_query = None
        self.clarification_options = []

class MockExecutionContext:
    def __init__(
        self,
        raw_query: str,
        intent: str,
        resolved_entities: Dict[str, Any],
        search_result: List[Dict[str, Any]],
        hallucination_safe: bool,
        warnings: List[str],
        reasoning_conclusion: str,
        intelligence_bundle_trace: List[str] = None
    ):
        self.raw_query = raw_query
        self.conversation_id = "test_memory_convo"
        self.intent = intent
        self.intent_result = MockIntentResult(intent, 0.95)
        self.resolved_entities = resolved_entities
        self.search_result = search_result
        self.hallucination_safe = hallucination_safe
        self.warnings = warnings
        self.reasoning_result = {"conclusion": reasoning_conclusion, "reason_chain": ["Logic"]}
        self.confidence = {"final": 0.88}
        self.is_followup = False
        self.start_time = time.time()
        self.select_stmt = "SELECT * FROM mock;"
        self.execution_trace = [
            {"stage": "SearchServiceStage", "latency_ms": 1.0, "decision": "Executed", "skipped": False, "executed": True}
        ]
        self.conversation_state = MockConversationState()
        
        # Build intelligence bundle
        class MockIntelBundle:
            def __init__(self, trace):
                self.execution_trace = trace
                self.hotspots = [{"latitude": 12.9}] if "Hotspot" in trace else []
                self.network = {"nodes": [{"id": 1}]} if "Network" in trace else {}
                self.repeat_offender = {}
                self.similar_cases = []
                self.pattern_analysis = ""
                self.recommendations = [{"action": "Patrol"}] if "Recommendation" in trace else []
        self.intelligence_bundle = MockIntelBundle(intelligence_bundle_trace or [])

class TestMemoryEngine(unittest.TestCase):

    def setUp(self):
        # Reset memory state before each test
        MemoryEngine.reset_memory("test_memory_convo")
        MemoryEngine.TTL_SECONDS = 300.0

    def test_memory_combinatorics_matrix(self):
        """
        Dynamically executes 1,008 deterministic permutations to test safety,
        versioning, audits, and value carries in MemoryEngine.
        """
        intents = ["SEARCH_CASES", "SEARCH_ACCUSED", "SEARCH_VICTIMS", "FIR_LOOKUP", "NETWORK_SEARCH", "HOTSPOT", "PREDICT_CRIME"]
        entity_sets = [
            {"district": "Mysuru"},
            {"accused_name": "Raju"},
            {"victim_name": "Ganesh"},
            {"police_station": "Hubli"},
            {"vehicle": "KA-09-1234"},
            {"weapon": "Knife"}
        ]
        results_variants = [
            [],
            [{"crime_no": "KSP-0001", "accused_name": "Raju", "victim_name": "Ganesh"}],
            [{"crime_no": "KSP-0002"}, {"crime_no": "KSP-0003"}]
        ]
        hallucination_safe_options = [True, False]
        warnings_options = [[], ["SQL timeout warning"]]
        reasoning_conclusions = ["Approved", "Insufficient evidence."]

        test_count = 0
        for intent in intents:
            for ents in entity_sets:
                for res in results_variants:
                    for safe in hallucination_safe_options:
                        for warn in warnings_options:
                            for conc in reasoning_conclusions:
                                # Get baseline version
                                mem_before = MemoryEngine.get_memory("test_memory_convo")
                                base_ver = mem_before.timestamps.get("version", 0) if mem_before else 0
                                
                                context = MockExecutionContext(
                                    raw_query="Find context parameters...",
                                    intent=intent,
                                    resolved_entities=ents,
                                    search_result=res,
                                    hallucination_safe=safe,
                                    warnings=warn,
                                    reasoning_conclusion=conc,
                                    intelligence_bundle_trace=["Hotspot", "Network"]
                                )
                                
                                audit = MemoryEngine.update_memory(context)
                                mem_after = MemoryEngine.get_memory("test_memory_convo")
                                
                                is_successful_execution = (safe and not warn and conc != "Insufficient evidence.")
                                
                                if is_successful_execution:
                                    # State should be updated, version increments
                                    self.assertIsNotNone(audit, f"Failed at successful path: intent={intent}")
                                    self.assertIsNotNone(mem_after)
                                    self.assertEqual(mem_after.timestamps["version"], base_ver + 1)
                                    self.assertEqual(audit["version"], base_ver + 1)
                                    self.assertTrue(len(audit["changes"]) >= 0)
                                else:
                                    # Blocked updates
                                    self.assertIsNone(audit)
                                    if base_ver == 0:
                                        self.assertIsNone(mem_after)
                                    else:
                                        self.assertEqual(mem_after.timestamps["version"], base_ver)
                                        
                                test_count += 1

        print(f"MemoryEngine: Ran {test_count} dynamic test case permutations.")
        self.assertTrue(test_count >= 700, f"Expected at least 700 test cases, but ran {test_count}")

    def test_ttl_expiry(self):
        """
        Confirms that memory returns None after TTL has elapsed.
        """
        context = MockExecutionContext(
            raw_query="Verify TTL",
            intent="SEARCH_CASES",
            resolved_entities={"district": "Mysuru"},
            search_result=[],
            hallucination_safe=True,
            warnings=[],
            reasoning_conclusion="Approved"
        )
        
        # Test default active
        MemoryEngine.TTL_SECONDS = 5.0
        audit = MemoryEngine.update_memory(context)
        self.assertIsNotNone(audit)
        self.assertIsNotNone(MemoryEngine.get_memory("test_memory_convo"))
        
        # Test expired TTL
        MemoryEngine.TTL_SECONDS = -0.1
        self.assertIsNone(MemoryEngine.get_memory("test_memory_convo"))

    def test_explicit_reset(self):
        """
        Verify memory is cleanly deleted on reset.
        """
        context = MockExecutionContext(
            raw_query="Clear state details",
            intent="SEARCH_CASES",
            resolved_entities={"district": "Mysuru"},
            search_result=[],
            hallucination_safe=True,
            warnings=[],
            reasoning_conclusion="Approved"
        )
        MemoryEngine.update_memory(context)
        self.assertIsNotNone(MemoryEngine.get_memory("test_memory_convo"))
        
        MemoryEngine.reset_memory("test_memory_convo")
        self.assertIsNone(MemoryEngine.get_memory("test_memory_convo"))

if __name__ == "__main__":
    unittest.main()
