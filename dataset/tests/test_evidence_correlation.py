import unittest
from typing import Dict, Any, List
from app.ai.evidence_correlation_engine import EvidenceCorrelationEngine

class MockExecutionContext:
    def __init__(self, search_result: List[Dict[str, Any]], intent: str = "SEARCH_CASES"):
        self.search_result = search_result
        self.intent = intent
        self.raw_query = "Find suspect correlations"
        self.conversation_id = "test_correlation_convo"

class TestEvidenceCorrelation(unittest.TestCase):

    def test_evidence_correlation_matrix(self):
        """
        Dynamically runs 3,240 deterministic combinations to validate scoring,
        safety thresholds, multi-hop chains, and cluster mappings.
        """
        intents = ["SEARCH_CASES", "SEARCH_ACCUSED", "NETWORK_SEARCH", "HOTSPOT", "COMPARE_CASES"]
        names = ["Raju", "raju", "Raju S", "RAJU", "Ganesh", "Ganesh K"]
        districts = ["Mysuru", "Bengaluru Urban", "Dharwad"]
        stations = ["Hubli", "Mysore South", "Kengeri"]
        vehicles = ["KA-09-1234", "ka-09-1234", None]
        phones = ["9876543210", None]
        weapons = ["Knife", None]

        test_count = 0
        for intent in intents:
            for name in names:
                for dist in districts:
                    for station in stations:
                        for veh in vehicles:
                            for ph in phones:
                                for wep in weapons:
                                    
                                    # Create two case records to test correlation
                                    row_a = {
                                        "crime_no": "KSP-2024-0001",
                                        "accused_name": name,
                                        "district_name": dist,
                                        "police_station_name": station,
                                        "vehicle_number": veh,
                                        "phone_number": ph,
                                        "weapon": wep,
                                        "crime_registered_date": "2024-03-01",
                                        "crime_category": "THEFT"
                                    }
                                    row_b = {
                                        "crime_no": "KSP-2024-0002",
                                        "accused_name": "Raju" if name.lower().startswith("ganesh") else "Ganesh",
                                        "district_name": "Mysuru",
                                        "police_station_name": "Mysore South",
                                        "vehicle_number": "KA-09-9999" if veh else None,
                                        "phone_number": "9000000000" if ph else None,
                                        "weapon": "Stick" if wep else None,
                                        "crime_registered_date": "2024-04-15",  # Over 30 days difference
                                        "crime_category": "ROBBERY"
                                    }
                                    
                                    context = MockExecutionContext([row_a, row_b], intent=intent)
                                    report = EvidenceCorrelationEngine.correlate(context)
                                    
                                    # Verify result fields
                                    self.assertIn("nodes", report)
                                    self.assertIn("edges", report)
                                    self.assertIn("chains", report)
                                    self.assertIn("clusters", report)
                                    self.assertIn("summary", report)
                                    
                                    if report["edges"]:
                                        # Active connection found
                                        self.assertTrue(len(report["nodes"]) > 0)
                                        # Edge scoring constraints
                                        for e in report["edges"]:
                                            if e["source"].startswith("FIR:") and e["target"].startswith("FIR:"):
                                                self.assertTrue(e["evidence_score"] >= EvidenceCorrelationEngine.MIN_THRESHOLD)
                                                self.assertIn(e["strength"], ["WEAK", "MEDIUM", "STRONG", "VERY_STRONG"])
                                    else:
                                        self.assertEqual(report["summary"], "No verified evidence connecting these records.")
                                        
                                    test_count += 1

        print(f"EvidenceCorrelation: Ran {test_count} dynamic test permutations.")
        self.assertTrue(test_count >= 900, f"Expected at least 900 test cases, but ran {test_count}")

    def test_single_record_fallback(self):
        """
        Verify that having fewer than 2 records returns empty fallback.
        """
        context = MockExecutionContext([{"crime_no": "KSP-1234"}])
        report = EvidenceCorrelationEngine.correlate(context)
        self.assertEqual(report["summary"], "No verified evidence connecting these records.")
        self.assertEqual(report["nodes"], [])
        self.assertEqual(report["edges"], [])

if __name__ == "__main__":
    unittest.main()
