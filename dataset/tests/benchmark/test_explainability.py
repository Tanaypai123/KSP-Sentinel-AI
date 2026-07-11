import unittest
from app.ai.explainability_engine import ExplainabilityEngine

class TestExplainabilityEngine(unittest.TestCase):

    def _call(self, intent="SEARCH_CASES", entities=None, is_followup=False,
              select_stmt=None, bundle_trace=None, reasoning=None, confidence=None):
        return ExplainabilityEngine.generate_explanation(
            intent=intent,
            resolved_entities=entities or {},
            is_followup=is_followup,
            select_stmt=select_stmt,
            intelligence_bundle_trace=bundle_trace or [],
            reasoning_result=reasoning or {},
            confidence_metrics=confidence or {}
        )

    # ── Structure tests ──────────────────────────────────────────────
    def test_all_keys_present(self):
        res = self._call()
        for key in ["detected_intent", "entities_extracted", "context_resolution",
                    "data_retrieval", "analytics_used", "reasoning_path", "confidence_explanation"]:
            self.assertIn(key, res)

    # ── Intent mapping ───────────────────────────────────────────────
    def test_intent_mapping_known(self):
        cases = {
            "FIR_LOOKUP": "Searching specific FIR records",
            "SEARCH_CASES": "Searching for general case records",
            "SEARCH_ACCUSED": "Looking up accused profiles",
            "SEARCH_VICTIMS": "Looking up victim profiles",
            "SEARCH_LOCATION": "Searching for crime locations",
            "SEARCH_POLICE_STATION": "Searching for police station details",
            "NETWORK_SEARCH": "Analyzing criminal associate networks",
            "PREDICT_CRIME": "Predicting future crime patterns",
            "COMPARE_CASES": "Comparing multiple case records",
            "AGGREGATE_COUNT": "Aggregating crime statistics",
            "CRIME_TREND": "Analyzing crime trends",
            "HOTSPOT": "Identifying crime hotspots",
            "GREETING": "Handling conversational greeting",
            "UNKNOWN": "Attempting to resolve unknown intent",
        }
        for intent, expected in cases.items():
            res = self._call(intent=intent)
            self.assertEqual(res["detected_intent"], expected, f"Failed for {intent}")

    def test_intent_mapping_unknown_intent(self):
        res = self._call(intent="CUSTOM_INTENT")
        self.assertIn("CUSTOM_INTENT", res["detected_intent"])

    # ── Entity sanitization ──────────────────────────────────────────
    def test_entities_are_cleaned(self):
        """Internal keys must be stripped from entities."""
        entities = {
            "district": "Bengaluru",
            "_dynamic_suggestions": ["a"],
            "structured_query": "...",
            "crime_type": "Theft"
        }
        res = self._call(entities=entities)
        self.assertIn("district", res["entities_extracted"])
        self.assertIn("crime_type", res["entities_extracted"])
        self.assertNotIn("_dynamic_suggestions", res["entities_extracted"])
        self.assertNotIn("structured_query", res["entities_extracted"])

    def test_entities_empty(self):
        res = self._call(entities={})
        self.assertEqual(res["entities_extracted"], "No specific entities extracted.")

    # ── No SQL exposure ──────────────────────────────────────────────
    def test_no_raw_sql_in_data_retrieval(self):
        """data_retrieval must never contain raw SQL keywords."""
        sql_keywords = ["SELECT", "FROM", "WHERE", "JOIN", "INSERT", "UPDATE", "DELETE"]
        entities = {"district": "Mysuru", "crime_type": "Robbery"}
        res = self._call(entities=entities, select_stmt=object())  # Simulate a stmt
        for kw in sql_keywords:
            self.assertNotIn(kw, res["data_retrieval"])

    def test_no_sql_without_stmt(self):
        res = self._call(select_stmt=None)
        self.assertEqual(res["data_retrieval"], "No database query executed for this intent.")

    # ── Context resolution ───────────────────────────────────────────
    def test_followup_resolution(self):
        res = self._call(is_followup=True)
        self.assertIn("conversational context", res["context_resolution"])

    def test_independent_resolution(self):
        res = self._call(is_followup=False)
        self.assertIn("independent", res["context_resolution"])

    # ── Analytics ────────────────────────────────────────────────────
    def test_analytics_populated(self):
        res = self._call(bundle_trace=["Pattern", "Hotspot"])
        self.assertEqual(len(res["analytics_used"]), 2)
        self.assertIn("Pattern", res["analytics_used"][0])

    def test_analytics_empty(self):
        res = self._call(bundle_trace=[])
        self.assertEqual(res["analytics_used"], ["No advanced analytical modules triggered."])

    # ── Reasoning path ───────────────────────────────────────────────
    def test_reasoning_path_populated(self):
        reasoning = {"reason_chain": ["Accused found.", "Repeat offender check executed."]}
        res = self._call(reasoning=reasoning)
        self.assertEqual(res["reasoning_path"], ["Accused found.", "Repeat offender check executed."])

    def test_reasoning_path_empty_chain(self):
        res = self._call(reasoning={"reason_chain": []})
        self.assertIn("Insufficient", res["reasoning_path"][0])

    def test_reasoning_path_no_result(self):
        res = self._call(reasoning={})
        self.assertIn("Insufficient", res["reasoning_path"][0])

    def test_reasoning_skipped(self):
        res = ExplainabilityEngine.generate_explanation(
            intent="SEARCH_CASES",
            resolved_entities={},
            is_followup=False,
            select_stmt=None,
            intelligence_bundle_trace=[],
            reasoning_result=None,
            confidence_metrics={}
        )
        self.assertIn("skipped", res["reasoning_path"][0])

    # ── Confidence explanation ───────────────────────────────────────
    def test_confidence_explanation_populated(self):
        conf = {"explanation": ["Base confidence 0.90", "Evidence count 5 records"]}
        res = self._call(confidence=conf)
        self.assertEqual(res["confidence_explanation"], conf["explanation"])

    def test_confidence_explanation_missing(self):
        res = self._call(confidence={})
        self.assertIn("unavailable", res["confidence_explanation"][0])

    # ── Bulk no-internal-code validation (130 permutations) ─────────
    def test_bulk_no_code_exposure(self):
        """Ensures no Python, SQL or code strings appear across many inputs."""
        banned = ["SELECT", "FROM", "WHERE", "def ", "class ", "import ", "return ", "lambda"]
        intents = ["FIR_LOOKUP", "SEARCH_CASES", "SEARCH_ACCUSED", "HOTSPOT", "PREDICT_CRIME", "NETWORK_SEARCH", "COMPARE_CASES"]
        entity_sets = [
            {"district": "Mysuru"},
            {"crime_type": "Theft", "accused_name": "Raju"},
            {},
            {"structured_data": "internal"},
            {"_private": "skip", "ps_name": "MG Road PS"},
        ]
        followups = [True, False]
        analytics = [[], ["Pattern"], ["Hotspot", "Network"]]
        count = 0
        for intent in intents:
            for ents in entity_sets:
                for followup in followups:
                    for trace in analytics:
                        res = self._call(intent=intent, entities=ents, is_followup=followup, bundle_trace=trace)
                        full_text = str(res)
                        for b in banned:
                            self.assertNotIn(b, full_text, f"Found '{b}' in explanation for intent={intent}")
                        count += 1

        self.assertGreaterEqual(count, 130)


if __name__ == "__main__":
    unittest.main()
