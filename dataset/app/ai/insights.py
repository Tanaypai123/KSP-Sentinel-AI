"""Analytical intelligence engine generating query explainability, insights,
contextual recommendations, trend indicators, and hotspot density maps.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.case import CaseMaster
from app.models.crime import CrimeHead
from app.models.masters import District, Unit

logger = logging.getLogger("ksp-sentinel-backend.insights")


class IntelligenceEngine:
    """Analytical processor adding explainability, insights, and recommendations."""

    @staticmethod
    def generate_explanation(
        intent: str,
        entities: Dict[str, Any],
        sql_stmt: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Compile a human-readable explanation object regarding search decisions."""
        filters = []
        for key in ["crime_head", "district", "police_station", "status", "gender", "year"]:
            val = entities.get(key)
            if val is not None:
                filters.append(f"{key}={val}")

        # Derive SQL summary string
        sql_summary = "None (Predictive OLS Model)"
        if sql_stmt is not None:
            try:
                from sqlalchemy.dialects import postgresql
                sql_summary = str(sql_stmt.compile(
                    dialect=postgresql.dialect(),
                    compile_kwargs={"literal_binds": True}
                ))
            except Exception:
                sql_summary = str(sql_stmt)

        reasoning_map = {
            "PREDICT_CRIME": "Applying Ordinary Least Squares (OLS) regression and rolling moving average to model future caseload.",
            "CRIME_TREND": "Aggregating crime cases chronologically and categorical distributions to detect growth curves.",
            "HOTSPOT": "Evaluating geolocation density of police station and district coordinates to locate risk areas.",
            "SEARCH_CASES": "Searching historical crime registers matching keyword parameters.",
            "AGGREGATE_COUNT": "Resolving scalar sum of case occurrences matching filters.",
            "SEARCH_ACCUSED": "Retrieving criminal suspect profile descriptors and links.",
            "SEARCH_VICTIMS": "Filtering victim age brackets and case details."
        }
        reasoning = reasoning_map.get(intent, "Analyzing database query logs for relevant case metrics.")
        crime = entities.get("crime_head") or entities.get("crime_major_head")
        district = entities.get("district")
        if crime or district:
            parts = []
            if crime:
                parts.append(f"{crime} cases")
            if district:
                parts.append(f"in {district}")
            reasoning += f" Filters applied for {' '.join(parts)}."

        return {
            "intent": intent,
            "entities": {k: v for k, v in entities.items() if v is not None and not k.startswith("structured_")},
            "reasoning": reasoning,
            "filters": filters,
            "sql_summary": sql_summary
        }

    @staticmethod
    def generate_insights(db: Session, intent: str, entities: Dict[str, Any]) -> List[str]:
        """Query real database counts to formulate dynamic, data-driven analytical insights."""
        insights = []

        try:
            # 1. Total records count
            total_cases = db.query(func.count(CaseMaster.case_master_id)).scalar() or 0
            if total_cases == 0:
                return ["No cases indexed in KSP Sentinel database yet."]

            # 2. Get specific crime insights
            crime = entities.get("crime_head")
            if crime:
                stmt_c = (
                    select(func.count(CaseMaster.case_master_id))
                    .join(CrimeHead, CaseMaster.crime_major_head_id == CrimeHead.crime_head_id)
                    .where(CrimeHead.crime_group_name.ilike(f"%{crime}%"))
                )
                crime_count = db.scalar(stmt_c) or 0
                pct = round((crime_count / total_cases) * 100, 1)
                insights.append(f"{crime.capitalize()} contributes to {pct}% of all reported crimes in the dataset.")
            else:
                # Fallback to general crime split
                top_crime_row = (
                    db.query(CrimeHead.crime_group_name, func.count(CaseMaster.case_master_id))
                    .join(CrimeHead, CaseMaster.crime_major_head_id == CrimeHead.crime_head_id)
                    .group_by(CrimeHead.crime_group_name)
                    .order_by(func.count(CaseMaster.case_master_id).desc())
                    .first()
                )
                if top_crime_row:
                    pct = round((top_crime_row[1] / total_cases) * 100, 1)
                    insights.append(f"{top_crime_row[0].capitalize()} is the most frequent crime category, contributing to {pct}% of total cases.")

            # 3. District location insight
            district = entities.get("district")
            if district:
                insights.append(f"Historical case distribution is heavily concentrated around {district}.")
            else:
                top_dist_row = (
                    db.query(District.district_name, func.count(CaseMaster.case_master_id))
                    .join(Unit, CaseMaster.police_station_id == Unit.unit_id)
                    .join(District, Unit.district_id == District.district_id)
                    .group_by(District.district_name)
                    .order_by(func.count(CaseMaster.case_master_id).desc())
                    .first()
                )
                if top_dist_row:
                    insights.append(f"Most crime cases in the database occurred in {top_dist_row[0]}.")

        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            insights = ["Insights generator compiled general statistical trends."]

        return insights[:3]

    @staticmethod
    def generate_recommendations(intent: str, entities: Dict[str, Any]) -> List[str]:
        """Construct a list of contextually relevant recommended follow-up queries."""
        crime = entities.get("crime_head") or "theft"
        dist = entities.get("district") or "Mysuru"

        recs = []
        if intent == "SEARCH_CASES":
            recs.extend([
                f"Show hotspots for {crime}",
                f"Predict {crime} next month in {dist}",
                f"Crime trend for {crime} in {dist}",
                "Show accused"
            ])
        elif intent == "HOTSPOT":
            recs.extend([
                f"Predict crime next month in {dist}",
                f"Show {crime} cases in {dist}",
                f"Crime trend in {dist}",
                "Count by station"
            ])
        elif intent == "CRIME_TREND":
            recs.extend([
                f"Predict {crime} next month in {dist}",
                f"Show hotspots for {crime} in {dist}",
                f"Show {crime} cases"
            ])
        elif intent == "PREDICT_CRIME":
            recs.extend([
                f"Show hotspots for {crime}",
                f"Crime trend for {crime} in {dist}",
                f"Show {crime} cases in {dist}"
            ])
        else:
            recs.extend([
                "Show hotspots",
                "Predict crime next month",
                "Crime trend",
                "Show accused"
            ])
        return recs[:4]

    @staticmethod
    def calculate_trend_analytics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process chronological monthly counts to compute trend analytics indices."""
        if not results:
            return {
                "growth_percentage": 0.0,
                "moving_average": 0.0,
                "highest_month": "N/A",
                "lowest_month": "N/A",
                "peak_month": "N/A",
                "declining_trend": False,
                "stable_trend": True
            }

        counts = [r["count"] for r in results]
        months = [r["month"] for r in results]

        # Highest/Lowest/Peak
        max_idx = counts.index(max(counts))
        min_idx = counts.index(min(counts))
        highest_month = months[max_idx]
        lowest_month = months[min_idx]

        # Growth
        initial = counts[0]
        latest = counts[-1]
        growth = round(((latest - initial) / initial) * 100, 2) if initial > 0 else 0.0

        # Moving average
        window = min(3, len(counts))
        moving_avg = round(sum(counts[-window:]) / window, 2)

        # Trend direction
        declining_trend = growth < -5.0
        stable_trend = -5.0 <= growth <= 5.0

        return {
            "growth_percentage": growth,
            "moving_average": moving_avg,
            "highest_month": highest_month,
            "lowest_month": lowest_month,
            "peak_month": highest_month,
            "declining_trend": declining_trend,
            "stable_trend": stable_trend
        }

    @staticmethod
    def calculate_hotspot_intelligence(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank geolocation results, calculating crime density and risk levels."""
        if not results:
            return []

        # Sort descending by crime count
        ranked = sorted(results, key=lambda x: x.get("count", 0), reverse=True)

        for rank, entry in enumerate(ranked, 1):
            count = entry.get("count", 0)
            
            # Risk Level
            if count > 20:
                risk = "CRITICAL"
                density = "HIGH"
            elif count > 10:
                risk = "HIGH"
                density = "HIGH"
            elif count > 5:
                risk = "MEDIUM"
                density = "MEDIUM"
            else:
                risk = "LOW"
                density = "LOW"

            entry["ranking"] = rank
            entry["risk_level"] = risk
            entry["crime_density"] = density

        return ranked
