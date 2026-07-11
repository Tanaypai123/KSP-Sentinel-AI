import unittest
import sys
import os
from typing import Dict, Any, List

sys.path.append(os.path.abspath('.'))

from app.ai.hallucination_guard import HallucinationGuard
from app.ai.intelligence_engine import IntelligenceBundle

class TestHallucinationGuardAdversarial(unittest.TestCase):
    def setUp(self):
        self.guard = HallucinationGuard()

    def test_run_adversarial_validation_suite(self):
        """
        Generates and runs 520 adversarial and clean test scenarios to validate
        the HallucinationGuard across all 6 target categories.
        """
        scenarios = []

        # 1. CLEAN / SAFE SCENARIOS (100 cases)
        for i in range(100):
            scenarios.append({
                "name": f"clean_case_{i}",
                "query": "Show details",
                "resolved_entities": {
                    "accused_name": f"Suspect {i}",
                    "district": "Mysuru"
                },
                "search_result": [
                    {
                        "accused_name": f"Suspect {i}",
                        "district_name": "Mysuru",
                        "crime_registered_date": "2024-05-10"
                    }
                ],
                "summary": f"Suspect {i} was registered in Mysuru on 2024-05-10.",
                "intelligence_bundle": None,
                "expected_safe": True,
                "expected_violations": []
            })

        # 2. NAMES VIOLATIONS (80 cases)
        for i in range(80):
            scenarios.append({
                "name": f"names_violation_{i}",
                "query": "Show details",
                "resolved_entities": {
                    "accused_name": f"Raju {i}"
                },
                "search_result": [
                    {
                        "accused_name": f"Ganesh {i}",
                        "district_name": "Mysuru"
                    }
                ],
                "summary": f"Suspect Raju {i} was arrested.",
                "intelligence_bundle": None,
                "expected_safe": False,
                "expected_violations": ["names"]
            })

        # 3. DATES VIOLATIONS (80 cases)
        for i in range(80):
            scenarios.append({
                "name": f"dates_violation_{i}",
                "query": "Show details",
                "resolved_entities": {},
                "search_result": [
                    {
                        "crime_registered_date": "2024-05-10"
                    }
                ],
                "summary": f"The crime occurred on 2024-11-{10 + (i % 20):02d}.",
                "intelligence_bundle": None,
                "expected_safe": False,
                "expected_violations": ["dates"]
            })

        # 4. LOCATIONS VIOLATIONS (80 cases)
        for i in range(80):
            scenarios.append({
                "name": f"locations_violation_{i}",
                "query": "Show details",
                "resolved_entities": {
                    "district": f"District_{i}"
                },
                "search_result": [
                    {
                        "district_name": "Mysuru"
                    }
                ],
                "summary": f"The incident occurred in District_{i}.",
                "intelligence_bundle": None,
                "expected_safe": False,
                "expected_violations": ["locations"]
            })

        # 5. RELATIONSHIPS VIOLATIONS (80 cases)
        for i in range(80):
            scenarios.append({
                "name": f"relationships_violation_{i}",
                "query": "Show details",
                "resolved_entities": {},
                "search_result": [
                    {
                        "accused_name": "Ganesh"
                    }
                ],
                "summary": f"Ganesh is linked to associate Sham {i}.",
                "intelligence_bundle": IntelligenceBundle(),  # Empty network bundle
                "expected_safe": False,
                "expected_violations": ["relationships"]
            })

        # 6. STATISTICS VIOLATIONS (80 cases)
        for i in range(80):
            scenarios.append({
                "name": f"statistics_violation_{i}",
                "query": "Show count",
                "resolved_entities": {},
                "search_result": [
                    {"crime_no": "KSP-0001"}
                ],  # 1 record
                "summary": f"We verified {50 + i} cases in the database.",
                "intelligence_bundle": None,
                "expected_safe": False,
                "expected_violations": ["statistics"]
            })

        # 7. RECOMMENDATIONS VIOLATIONS (20 cases)
        for i in range(20):
            scenarios.append({
                "name": f"recommendations_violation_{i}",
                "query": "Show details",
                "resolved_entities": {},
                "search_result": [],  # 0 records
                "summary": "No results. Try querying: Show cases.",
                "intelligence_bundle": None,
                "expected_safe": False,
                "expected_violations": ["recommendations"]
            })

        # Run scenarios and collect results
        total_tests = len(scenarios)
        passed_tests = 0
        failed_scenarios = []

        statistics = {
            "clean": {"total": 0, "detected": 0},
            "names": {"total": 0, "detected": 0},
            "dates": {"total": 0, "detected": 0},
            "locations": {"total": 0, "detected": 0},
            "relationships": {"total": 0, "detected": 0},
            "statistics": {"total": 0, "detected": 0},
            "recommendations": {"total": 0, "detected": 0}
        }

        print(f"\n--- Running {total_tests} adversarial scenarios ---")

        for s in scenarios:
            category = "clean"
            if s["expected_violations"]:
                category = s["expected_violations"][0]
            
            statistics[category]["total"] += 1

            # Run through HallucinationGuard
            is_safe, violations = HallucinationGuard.validate(
                intent="SEARCH_CASES" if s["query"] != "Show count" else "SEARCH_CASES", # any database required intent
                search_result=s["search_result"],
                resolved_entities=s["resolved_entities"],
                response={"summary": s["summary"], "recommended_queries": ["Show details"] if "Try querying" in s["summary"] else []},
                intelligence_bundle=s["intelligence_bundle"]
            )
            res = {"is_safe": is_safe, "violations": violations}

            # Check correctness
            safe_match = (res["is_safe"] == s["expected_safe"])
            
            # Check if expected violations are documented
            v_match = True
            for ev in s["expected_violations"]:
                if not any(v["category"] == ev for v in res["violations"]):
                    v_match = False
                    break

            if safe_match and v_match:
                passed_tests += 1
                statistics[category]["detected"] += 1
            else:
                failed_scenarios.append({
                    "name": s["name"],
                    "expected_safe": s["expected_safe"],
                    "got_safe": res["is_safe"],
                    "expected_violations": s["expected_violations"],
                    "got_violations": [v["category"] for v in res["violations"]]
                })

        accuracy = (passed_tests / total_tests) * 100
        print(f"Validation Suite Execution: {passed_tests} / {total_tests} passed ({accuracy:.2f}%)")
        
        print("\nDetection Performance per Category:")
        for cat, stats in statistics.items():
            total = stats["total"]
            detected = stats["detected"]
            rate = (detected / total) * 100 if total > 0 else 100.0
            print(f"  {cat.upper():<15} | Target: {total:>3} | Detected Correctly: {detected:>3} | Success Rate: {rate:>6.2f}%")

        if failed_scenarios:
            print("\nFirst 5 failed cases detail:")
            for f in failed_scenarios[:5]:
                print(f"  Name: {f['name']}")
                print(f"    Expected Safe: {f['expected_safe']} | Got Safe: {f['got_safe']}")
                print(f"    Expected Violations: {f['expected_violations']} | Got: {f['got_violations']}")
            self.fail(f"Adversarial validation failed: {len(failed_scenarios)} scenarios failed correctness checks.")

if __name__ == "__main__":
    unittest.main()
