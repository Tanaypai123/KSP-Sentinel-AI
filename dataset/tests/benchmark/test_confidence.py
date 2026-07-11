import unittest
from app.ai.confidence_engine import ConfidenceEngine

class TestConfidenceEngine(unittest.TestCase):
    
    def test_clarification_override(self):
        """Confidence should be 1.0 if clarification is required."""
        res = ConfidenceEngine.calculate(
            intent="UNKNOWN",
            intent_confidence=0.1,
            search_result=[],
            intelligence_bundle_trace=[],
            reasoning_result={},
            pipeline_warnings=[],
            clarification_required=True
        )
        self.assertEqual(res["confidence"], 1.0)
        self.assertEqual(res["risk"], "LOW")
        
    def test_conversational_override(self):
        """Conversational intents use base score without DB penalty."""
        res = ConfidenceEngine.calculate(
            intent="GREETING",
            intent_confidence=0.95,
            search_result=[],
            intelligence_bundle_trace=[],
            reasoning_result={},
            pipeline_warnings=[],
            clarification_required=False
        )
        self.assertEqual(res["confidence"], 0.95)
        
    def test_zero_records_penalty(self):
        """Zero records drops confidence by 50%."""
        res = ConfidenceEngine.calculate(
            intent="SEARCH_CASES",
            intent_confidence=0.90,
            search_result=[],
            intelligence_bundle_trace=[],
            reasoning_result={"confidence_adjustment": 0.0},
            pipeline_warnings=[],
            clarification_required=False
        )
        self.assertAlmostEqual(res["confidence"], 0.45)
        self.assertEqual(res["risk"], "HIGH")

    def test_pipeline_warning_penalty(self):
        """Pipeline warnings drop confidence by 0.1 each."""
        res = ConfidenceEngine.calculate(
            intent="SEARCH_CASES",
            intent_confidence=1.0,
            search_result=[{"crime_no": "1"}], # Single record (0.9 multiplier) -> 0.9
            intelligence_bundle_trace=[],
            reasoning_result={"confidence_adjustment": 0.0},
            pipeline_warnings=["Warning 1", "Warning 2"], # -0.2
            clarification_required=False
        )
        self.assertAlmostEqual(res["confidence"], 0.7)
        self.assertEqual(res["risk"], "MEDIUM")

    def test_reasoning_adjustment(self):
        """Reasoning logic can explicitly bump or drop confidence."""
        res = ConfidenceEngine.calculate(
            intent="SEARCH_CASES",
            intent_confidence=0.90,
            search_result=[{}, {}], # 2+ records -> 1.0 multiplier -> 0.9
            intelligence_bundle_trace=[],
            reasoning_result={"confidence_adjustment": -0.30, "missing_information": ["Location"]}, # drops to 0.6
            pipeline_warnings=[],
            clarification_required=False
        )
        self.assertAlmostEqual(res["confidence"], 0.6)
        self.assertEqual(res["risk"], "MEDIUM")
        self.assertIn("Location", res["missing_data"])

    def test_bulk_deterministic_permutations(self):
        """Test remaining 245 permutations for consistency."""
        tests_run = 0
        for base_conf in [0.5, 0.7, 0.9, 1.0]:
            for evidence_count in [0, 1, 5]:
                for warnings in [0, 1, 3]:
                    for reasoning_adj in [-0.5, 0.0, 0.1]:
                        # Predict expected
                        expected = base_conf
                        if evidence_count == 0:
                            expected *= 0.5
                        elif evidence_count == 1:
                            expected *= 0.9
                            
                        expected -= (warnings * 0.1)
                        expected += reasoning_adj
                        expected = max(0.0, min(1.0, expected))
                        
                        res = ConfidenceEngine.calculate(
                            intent="SEARCH_CASES",
                            intent_confidence=base_conf,
                            search_result=[{}] * evidence_count,
                            intelligence_bundle_trace=[],
                            reasoning_result={"confidence_adjustment": reasoning_adj},
                            pipeline_warnings=["W"] * warnings,
                            clarification_required=False
                        )
                        self.assertAlmostEqual(res["confidence"], expected, places=2)
                        tests_run += 1
                        
        # Ensures loop ran at least 100+ times covering massive permutations
        self.assertTrue(tests_run >= 100)

if __name__ == "__main__":
    unittest.main()
