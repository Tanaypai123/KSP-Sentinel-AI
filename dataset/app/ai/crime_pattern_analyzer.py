import datetime
from typing import List, Dict, Any
from collections import defaultdict

class CrimePatternAnalyzer:
    """
    Pure post-processing layer to analyze SQL results and generate data-backed crime patterns.
    Executes in O(n) with no nested loops or external database calls.
    """

    @staticmethod
    def build_pattern_summary(results: List[Dict[str, Any]]) -> str:
        # Require minimum records to avoid hallucinations
        if not results or len(results) < 5:
            return "No statistically significant crime pattern detected."
            
        # O(n) iteration for all aggregations
        hour_counts = defaultdict(int)
        day_counts = defaultdict(int)
        month_counts = defaultdict(int)
        station_counts = defaultdict(int)
        keyword_counts = defaultdict(int)
        
        valid_dates = 0
        total_records = len(results)
        
        # Extended stop words for keyword analysis
        stop_words = {
            "the", "a", "an", "and", "or", "but", "is", "are", "was", "were", 
            "in", "on", "at", "to", "for", "of", "with", "by", "from", "that", 
            "this", "it", "he", "she", "they", "their", "his", "her", "who",
            "which", "what", "where", "when", "why", "how", "all", "any", "both",
            "each", "few", "more", "most", "other", "some", "such", "no", "nor",
            "not", "only", "own", "same", "so", "than", "too", "very", "can",
            "will", "just", "should", "now", "about", "into", "through", "during",
            "before", "after", "above", "below", "up", "down", "out", "over", "under",
            "again", "further", "then", "once", "here", "there", "when", "where",
            "why", "how", "all", "any", "both", "each", "few", "more", "most",
            "other", "some", "such", "no", "nor", "not", "only", "own", "same",
            "so", "than", "too", "very", "can", "will", "just", "should", "now",
            "said", "also", "have", "has", "had", "been", "being", "am", "does", "did", "doing",
            "accused", "victim", "police", "station", "complainant", "case", "fir", "registered",
            "unknown", "person", "incident", "crime", "report", "reported", "about", "against", "along"
        }
        
        for record in results:
            # Time patterns
            dt_val = record.get("crime_registered_date") or record.get("incident_from_date")
            dt = None
            if dt_val:
                if isinstance(dt_val, str):
                    try:
                        if "T" in dt_val:
                            dt = datetime.datetime.fromisoformat(dt_val.replace("Z", "+00:00"))
                        elif " " in dt_val:
                            dt = datetime.datetime.strptime(dt_val, "%Y-%m-%d %H:%M:%S")
                        else:
                            dt = datetime.datetime.strptime(dt_val, "%Y-%m-%d")
                    except ValueError:
                        pass
                elif isinstance(dt_val, datetime.datetime) or isinstance(dt_val, datetime.date):
                    dt = dt_val
                    
                if dt:
                    valid_dates += 1
                    if isinstance(dt, datetime.datetime):
                        hour_counts[dt.hour] += 1
                    day_counts[dt.strftime("%A")] += 1
                    month_counts[dt.strftime("%Y-%m")] += 1
            
            # Station distribution
            station = record.get("police_station_name")
            if station:
                station_counts[station] += 1
                
            # Keyword patterns
            brief_facts = record.get("brief_facts", "")
            if brief_facts and isinstance(brief_facts, str):
                words = [w.strip(".,;:!?()[]{}\"'") for w in brief_facts.lower().split()]
                for w in words:
                    if len(w) > 3 and w not in stop_words and not w.isdigit():
                        keyword_counts[w] += 1
                        
        # Confidence score based on dataset size (Max 98% for > 100 records)
        confidence = min(98, max(30, int((total_records / 100.0) * 100)))
        if total_records < 10:
            confidence = min(40, confidence)
            
        insights = []
        
        # 1. Temporal Analysis
        if hour_counts and valid_dates >= 3:
            peak_hour = max(hour_counts.items(), key=lambda x: x[1])
            time_period = "Night" if 20 <= peak_hour[0] <= 23 or 0 <= peak_hour[0] <= 4 else "Morning" if 5 <= peak_hour[0] <= 11 else "Afternoon" if 12 <= peak_hour[0] <= 16 else "Evening"
            insights.append(f"Peak crime activity occurs during the **{time_period}** (around {peak_hour[0]}:00).")
            
        if day_counts and valid_dates >= 3:
            peak_day = max(day_counts.items(), key=lambda x: x[1])
            insights.append(f"Incidents are most frequently reported on **{peak_day[0]}s**.")
            
        if month_counts and len(month_counts) > 2:
            sorted_months = sorted(month_counts.items(), key=lambda x: x[0])
            first_half = sum(v for k, v in sorted_months[:len(sorted_months)//2])
            second_half = sum(v for k, v in sorted_months[len(sorted_months)//2:])
            if second_half > first_half * 1.5:
                insights.append("There is an **increasing temporal trend** in recent months.")
            elif first_half > second_half * 1.5:
                insights.append("There is a **decreasing temporal trend** in recent months.")
                
        # 2. Location / Station Analysis
        if station_counts:
            top_stations = sorted(station_counts.items(), key=lambda x: x[1], reverse=True)
            if top_stations[0][1] >= 2: # Meaningful cluster
                insights.append(f"Highest geographic concentration is at **{top_stations[0][0]}** ({top_stations[0][1]} cases).")
            
        # 3. Keyword / Characteristics
        if keyword_counts:
            top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
            if top_keywords and top_keywords[0][1] >= 2:
                top_3 = [k[0] for k in top_keywords[:3] if k[1] >= 2]
                if top_3:
                    insights.append(f"Recurring characteristics include terms like: {', '.join(top_3)}.")
                
        if len(insights) < 1:
            return "No statistically significant crime pattern detected."
            
        summary = "### 🔍 Crime Pattern Intelligence\n"
        for insight in insights:
            summary += f"- {insight}\n"
        summary += f"\n*(Pattern Confidence Score: {confidence}% based on {total_records} records)*"
        
        return summary
