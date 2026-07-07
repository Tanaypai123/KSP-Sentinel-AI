"""
Analytical and Caching Test Suite for KSP Sentinel AI.
Verifies caching mechanisms, trend analytics formulas, hotspot ranking,
FIR case summaries, explainability payloads, and the global dashboard service.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.orm import Session
from app.database.connection import SessionLocal
from app.core.cache import global_cache, AnalyticalCache
from app.ai.insights import IntelligenceEngine
from app.services.analytics import AnalyticsService
from app.ai.intent_classifier import Intent
from app.ai.query_parser import parse_query


def run_analytics_tests():
    print("=" * 80)
    print("Executing KSP Sentinel AI Analytics Unit Tests")
    print("=" * 80)

    # Use active SessionLocal for database checks
    db: Session = SessionLocal()
    
    passed_tests = 0
    failed_tests = 0

    def assert_true(cond, name):
        nonlocal passed_tests, failed_tests
        if cond:
            print(f"✅ PASS: {name}")
            passed_tests += 1
        else:
            print(f"❌ FAIL: {name}")
            failed_tests += 1

    # -------------------------------------------------------------
    # Test 1: In-Memory Cache TTL and Eviction
    # -------------------------------------------------------------
    try:
        cache = AnalyticalCache(ttl_seconds=1)
        cache.set("test_key", {"val": 123})
        
        # Immediate get
        assert_true(cache.get("test_key") == {"val": 123}, "Cache immediate read matches")
        
        # Wait for TTL expiration
        import time
        time.sleep(1.1)
        assert_true(cache.get("test_key") is None, "Cache expires after TTL timeout")
    except Exception as e:
        assert_true(False, f"Caching test exception: {e}")

    # -------------------------------------------------------------
    # Test 2: Trend Analytics Formulas
    # -------------------------------------------------------------
    try:
        # Declining trend check
        monthly_data_declining = [
            {"month": "2026-01", "count": 20},
            {"month": "2026-02", "count": 15},
            {"month": "2026-03", "count": 10}
        ]
        trend_declining = IntelligenceEngine.calculate_trend_analytics(monthly_data_declining)
        assert_true(trend_declining["growth_percentage"] == -50.0, "Trend growth rate calculation correct")
        assert_true(trend_declining["declining_trend"] is True, "Trend correctly flags declining direction")
        assert_true(trend_declining["stable_trend"] is False, "Trend correctly flags stable as False")
        assert_true(trend_declining["highest_month"] == "2026-01", "Highest month matches peak")
        assert_true(trend_declining["lowest_month"] == "2026-03", "Lowest month matches base")

        # Stable trend check
        monthly_data_stable = [
            {"month": "2026-01", "count": 100},
            {"month": "2026-02", "count": 102},
            {"month": "2026-03", "count": 101}
        ]
        trend_stable = IntelligenceEngine.calculate_trend_analytics(monthly_data_stable)
        assert_true(trend_stable["stable_trend"] is True, "Trend correctly flags stable direction")
        assert_true(trend_stable["declining_trend"] is False, "Trend correctly flags declining as False")
    except Exception as e:
        assert_true(False, f"Trend analytics test exception: {e}")

    # -------------------------------------------------------------
    # Test 3: Hotspot Rank and Risk Level Assignments
    # -------------------------------------------------------------
    try:
        raw_hotspots = [
            {"latitude": 12.0, "longitude": 76.0, "location": "Station A", "count": 3},
            {"latitude": 12.1, "longitude": 76.1, "location": "Station B", "count": 25},
            {"latitude": 12.2, "longitude": 76.2, "location": "Station C", "count": 8}
        ]
        hotspots = IntelligenceEngine.calculate_hotspot_intelligence(raw_hotspots)
        
        # Station B must rank 1
        assert_true(hotspots[0]["location"] == "Station B", "Hotspots ranked correctly: Rank 1 is highest count")
        assert_true(hotspots[0]["ranking"] == 1, "Hotspot rank index equals 1")
        assert_true(hotspots[0]["risk_level"] == "CRITICAL", "High count mapped to CRITICAL risk level")
        
        # Station C must rank 2
        assert_true(hotspots[1]["location"] == "Station C", "Rank 2 matches second highest count")
        assert_true(hotspots[1]["risk_level"] == "MEDIUM", "Count 8 mapped to MEDIUM risk level")
        
        # Station A must rank 3
        assert_true(hotspots[2]["location"] == "Station A", "Rank 3 matches lowest count")
        assert_true(hotspots[2]["risk_level"] == "LOW", "Count 3 mapped to LOW risk level")
    except Exception as e:
        assert_true(False, f"Hotspot intelligence test exception: {e}")

    # -------------------------------------------------------------
    # Test 4: Dynamic Insights & Recommendations
    # -------------------------------------------------------------
    try:
        entities = {"crime_head": "theft", "district": "Mysuru"}
        insights = IntelligenceEngine.generate_insights(db, "SEARCH_CASES", entities)
        recs = IntelligenceEngine.generate_recommendations("SEARCH_CASES", entities)
        
        assert_true(len(insights) > 0, "Insights list is populated with database metrics")
        assert_true(any("theft" in ins.lower() for ins in insights), "Insights incorporate contextual crime tags")
        assert_true(len(recs) == 4, "Generates exactly 4 follow-up suggestions")
        assert_true("hotspots" in recs[0].lower(), "First recommendation maps logically to hotspots")
    except Exception as e:
        assert_true(False, f"Insights and recommendations test exception: {e}")

    # -------------------------------------------------------------
    # Test 5: Explainability Object Formatting
    # -------------------------------------------------------------
    try:
        entities = {"crime_head": "theft", "district": "Mysuru"}
        explanation = IntelligenceEngine.generate_explanation("SEARCH_CASES", entities)
        
        assert_true(explanation["intent"] == "SEARCH_CASES", "Explanation intent matches query")
        assert_true("district" in explanation["entities"], "Explanation lists extracted entities")
        assert_true("theft" in explanation["reasoning"].lower(), "Explanation reasoning parses crime parameters")
        assert_true("district=Mysuru" in explanation["filters"], "Explanation lists human-readable filters")
    except Exception as e:
        assert_true(False, f"Explainability test exception: {e}")

    # -------------------------------------------------------------
    # Test 6: Global Analytics Service Queries
    # -------------------------------------------------------------
    try:
        top_crimes = AnalyticsService.get_top_crimes(db)
        top_districts = AnalyticsService.get_top_districts(db)
        top_stations = AnalyticsService.get_top_stations(db)
        monthly_counts = AnalyticsService.get_monthly_counts(db)
        status_dist = AnalyticsService.get_status_distribution(db)
        gender_dist = AnalyticsService.get_gender_distribution(db)
        age_dist = AnalyticsService.get_age_distribution(db)

        assert_true(isinstance(top_crimes, list), "get_top_crimes returns list")
        assert_true(isinstance(top_districts, list), "get_top_districts returns list")
        assert_true(isinstance(top_stations, list), "get_top_stations returns list")
        assert_true(isinstance(monthly_counts, list), "get_monthly_counts returns list")
        assert_true(isinstance(status_dist, list), "get_status_distribution returns list")
        assert_true(isinstance(gender_dist, list), "get_gender_distribution returns list")
        assert_true(isinstance(age_dist, list), "get_age_distribution returns list")
    except Exception as e:
        assert_true(False, f"Global Analytics Service test exception: {e}")

    db.close()

    print("=" * 80)
    print(f"Analytics Test Summary: Passed={passed_tests} | Failed={failed_tests}")
    print("=" * 80)

    if failed_tests > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    run_analytics_tests()
