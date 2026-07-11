from typing import Dict, Any, List
from collections import defaultdict
from datetime import datetime

class HotspotEngine:
    @staticmethod
    def analyze_hotspots(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyzes crime density, peak hours, trends, and risk zones from a set of cases.
        """
        if not results:
            return {}

        ps_counts = defaultdict(int)
        district_counts = defaultdict(int)
        crime_counts = defaultdict(int)
        hour_counts = defaultdict(int)
        month_counts = defaultdict(int)

        for r in results:
            # Police Station
            ps = r.get("police_station_name")
            if ps: ps_counts[ps] += 1
            
            # District
            dist = r.get("district_name")
            if dist: district_counts[dist] += 1
            
            # Crime Type
            crime = r.get("crime_category") or r.get("crime_group_name")
            if crime: crime_counts[crime] += 1
            
            # Time & Date (IncidentFromDate, CrimeRegisteredDate)
            # Try to get incident date for time of day
            inc_date = r.get("incident_from_date")
            if inc_date:
                if hasattr(inc_date, "hour"):
                    hour = inc_date.hour
                    hour_counts[hour] += 1
                elif isinstance(inc_date, str):
                    try:
                        dt = datetime.fromisoformat(inc_date.replace("Z", "+00:00"))
                        hour_counts[dt.hour] += 1
                    except Exception:
                        pass
                        
            # Use CrimeRegisteredDate for monthly trends
            reg_date = r.get("crime_registered_date")
            if reg_date:
                if hasattr(reg_date, "year") and hasattr(reg_date, "month"):
                    m_key = f"{reg_date.year}-{reg_date.month:02d}"
                    month_counts[m_key] += 1
                elif isinstance(reg_date, str):
                    try:
                        dt = datetime.fromisoformat(reg_date.replace("Z", "+00:00"))
                        m_key = f"{dt.year}-{dt.month:02d}"
                        month_counts[m_key] += 1
                    except Exception:
                        pass

        total_cases = len(results)

        # Rankings
        ps_ranking = sorted(ps_counts.items(), key=lambda x: x[1], reverse=True)
        dist_ranking = sorted(district_counts.items(), key=lambda x: x[1], reverse=True)
        crime_ranking = sorted(crime_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Peak Hours
        peak_hours = []
        if hour_counts:
            sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
            peak_hours = [f"{h:02d}:00" for h, count in sorted_hours[:3]]
            
        # Trend Direction
        trend = "Stable"
        if len(month_counts) >= 2:
            sorted_months = sorted(month_counts.items(), key=lambda x: x[0])
            last_month_count = sorted_months[-1][1]
            prev_month_count = sorted_months[-2][1]
            if last_month_count > prev_month_count * 1.1:
                trend = "Increasing"
            elif last_month_count < prev_month_count * 0.9:
                trend = "Decreasing"

        # Risk Zones & Recommendations
        recommendations = []
        risk_zones = []
        
        if ps_ranking:
            top_ps, count = ps_ranking[0]
            risk_zones.append(top_ps)
            if count > total_cases * 0.3 and total_cases > 5:
                recommendations.append(f"Investigate Repeat Areas: High density ({count} cases) localized at {top_ps}.")
                
        # Night vs Day
        night_cases = sum(c for h, c in hour_counts.items() if h >= 18 or h <= 5)
        total_time_cases = sum(hour_counts.values())
        if total_time_cases > 0 and night_cases / total_time_cases > 0.5:
            recommendations.append("Deploy Surveillance: High incidence of night-time offenses detected.")
            
        if trend == "Increasing":
            recommendations.append("Increase Patrol: Recent upward trend in reported incidents requires immediate presence.")
            
        if not recommendations:
            recommendations.append("Maintain standard operational readiness.")

        return {
            "total_cases": total_cases,
            "police_station_ranking": [{"name": k, "count": v} for k, v in ps_ranking[:5]],
            "district_ranking": [{"name": k, "count": v} for k, v in dist_ranking[:5]],
            "crime_ranking": [{"name": k, "count": v} for k, v in crime_ranking[:5]],
            "peak_hours": peak_hours,
            "trend": trend,
            "risk_zones": risk_zones,
            "recommendations": recommendations
        }
