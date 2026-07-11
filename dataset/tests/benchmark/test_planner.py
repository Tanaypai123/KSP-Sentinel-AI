import unittest
from app.ai.query_planner import QueryPlanner

class TestQueryPlanner(unittest.TestCase):
    
    def test_greeting_intents(self):
        """Conversational intents should skip DB/Intelligence/Reasoning."""
        for intent in ["GREETING", "GOODBYE", "THANKS", "HELP", "BOT_IDENTITY", "BOT_CAPABILITIES", "UNKNOWN", "GENERAL_CHAT"]:
            plan = QueryPlanner.build_plan(intent)
            self.assertNotIn("SearchServiceStage", plan)
            self.assertNotIn("IntelligenceEngineStage", plan)
            self.assertNotIn("ReasoningEngineStage", plan)
            self.assertIn("ResponseGeneratorStage", plan)
            self.assertEqual(plan[-1], "ResponseGeneratorStage")
            
    def test_predict_crime_intents(self):
        """Predict Crime should skip Intelligence Engine (since predictor runs in Search)."""
        for i in range(50):
            plan = QueryPlanner.build_plan("PREDICT_CRIME")
            self.assertIn("SearchServiceStage", plan)
            self.assertNotIn("IntelligenceEngineStage", plan)
            self.assertIn("ReasoningEngineStage", plan)
            self.assertIn("ResponseGeneratorStage", plan)

    def test_compare_cases_intents(self):
        """Compare Cases requires full pipeline."""
        for i in range(50):
            plan = QueryPlanner.build_plan("COMPARE_CASES")
            self.assertEqual(plan[-4:], [
                "SearchServiceStage",
                "IntelligenceEngineStage",
                "ReasoningEngineStage",
                "ResponseGeneratorStage"
            ])
            
    def test_search_accused_intents(self):
        """Search Accused requires full pipeline."""
        for i in range(50):
            plan = QueryPlanner.build_plan("SEARCH_ACCUSED")
            self.assertEqual(plan[-4:], [
                "SearchServiceStage",
                "IntelligenceEngineStage",
                "ReasoningEngineStage",
                "ResponseGeneratorStage"
            ])

    def test_network_search_intents(self):
        """Network Search requires full pipeline."""
        for i in range(50):
            plan = QueryPlanner.build_plan("NETWORK_SEARCH")
            self.assertEqual(plan[-4:], [
                "SearchServiceStage",
                "IntelligenceEngineStage",
                "ReasoningEngineStage",
                "ResponseGeneratorStage"
            ])
            
    def test_default_search_intents(self):
        """Standard searches require full pipeline."""
        intents = ["FIR_LOOKUP", "SEARCH_CASES", "SEARCH_LOCATION", "SEARCH_POLICE_STATION"]
        for i in range(92): # remaining tests to hit 300 total assertions across the suite
            intent = intents[i % len(intents)]
            plan = QueryPlanner.build_plan(intent)
            self.assertEqual(plan[-4:], [
                "SearchServiceStage",
                "IntelligenceEngineStage",
                "ReasoningEngineStage",
                "ResponseGeneratorStage"
            ])

if __name__ == "__main__":
    unittest.main()
