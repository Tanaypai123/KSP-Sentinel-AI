from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime

class RepeatOffenderEngine:
    @staticmethod
    def analyze_accused(accused_name: str, db: Session) -> Dict[str, Any]:
        """
        Analyzes the criminal history of an accused individual and computes risk metrics.
        Returns a dictionary containing metrics, Risk Level, and an Officer Summary.
        """
        # Fetch all FIRs for the accused (using fuzzy matching for aliases)
        # We join accused -> case_master -> unit (for district) -> crime_head (for category)
        query = text("""
            SELECT 
                cm."CaseMasterID",
                cm."CrimeNo",
                cm."CrimeRegisteredDate",
                u."DistrictID",
                d."DistrictName",
                ch."CrimeGroupName" as "CrimeCategory",
                a."AccusedName"
            FROM accused a
            JOIN case_master cm ON a."CaseMasterID" = cm."CaseMasterID"
            LEFT JOIN unit u ON cm."PoliceStationID" = u."UnitID"
            LEFT JOIN district d ON u."DistrictID" = d."DistrictID"
            LEFT JOIN crime_head ch ON cm."CrimeMajorHeadID" = ch."CrimeHeadID"
            WHERE a."AccusedName" ILIKE :name
               OR a."AccusedName" ILIKE :name_wild
            ORDER BY cm."CrimeRegisteredDate" ASC
        """)
        
        # Use wildcard to catch slight variations like "<Name> @ Alias"
        name_wild = f"%{accused_name}%"
        rows = db.execute(query, {"name": accused_name, "name_wild": name_wild}).fetchall()
        
        if not rows:
            return {
                "total_firs": 0,
                "active_districts": [],
                "crime_categories": [],
                "time_span_days": 0,
                "risk_level": "LOW",
                "officer_summary": "No established criminal history found.",
                "linked_firs": []
            }
            
        # Aggregate metrics
        unique_firs = {}
        districts = set()
        categories = set()
        dates = []
        
        for r in rows:
            crime_no = r.CrimeNo
            if not crime_no: continue
            
            unique_firs[crime_no] = True
            
            if r.DistrictName:
                districts.add(r.DistrictName)
            if r.CrimeCategory:
                categories.add(r.CrimeCategory)
            if r.CrimeRegisteredDate:
                # Ensure it's a date or datetime object
                try:
                    if isinstance(r.CrimeRegisteredDate, str):
                        dates.append(datetime.strptime(r.CrimeRegisteredDate.split()[0], "%Y-%m-%d"))
                    else:
                        dates.append(r.CrimeRegisteredDate)
                except Exception:
                    pass

        total_firs = len(unique_firs)
        
        # If dates are available, calculate time span and recency
        time_span_days = 0
        recency_days = 999999
        if dates:
            dates.sort()
            earliest = dates[0]
            latest = dates[-1]
            from datetime import date
            latest_dt = datetime.combine(latest, datetime.min.time()) if isinstance(latest, date) and not isinstance(latest, datetime) else latest
            earliest_dt = datetime.combine(earliest, datetime.min.time()) if isinstance(earliest, date) and not isinstance(earliest, datetime) else earliest
            time_span_days = (latest_dt - earliest_dt).days
            max_db_date = datetime(2026, 6, 30) # approximate recent date
            recency_days = (max_db_date - latest_dt).days

        # Risk Calculation
        risk_level = "LOW"
        if total_firs >= 8:
            risk_level = "CRITICAL"
        elif total_firs >= 4:
            risk_level = "HIGH"
        elif total_firs >= 2:
            risk_level = "MEDIUM"
            
        # Modifiers
        if total_firs >= 2 and recency_days < 180 and risk_level == "MEDIUM":
            risk_level = "HIGH"
            
        if len(districts) >= 3 and risk_level in ["LOW", "MEDIUM"]:
            risk_level = "HIGH"
            
        # Generate Officer Summary
        d_count = len(districts)
        d_str = "district" if d_count == 1 else "districts"
        
        span_str = ""
        if time_span_days > 0:
            if time_span_days < 30:
                span_str = f" over {time_span_days} days"
            elif time_span_days < 365:
                span_str = f" over {time_span_days // 30} months"
            else:
                span_str = f" over {round(time_span_days / 365, 1)} years"
        
        primary_crime = list(categories)[0] if categories else "various"
        if len(categories) > 1:
            primary_crime = f"{primary_crime} and others"
            
        if total_firs == 1:
            summary = f"The accused appears in 1 FIR.\n\nRisk Level\n{risk_level}\nReason\nIsolated incident."
        else:
            summary = f"The accused appears in {total_firs} FIRs across {d_count} {d_str}.\n\nRisk Level\n{risk_level}\nReason\nFrequent {primary_crime.lower()} offences{span_str}."

        return {
            "total_firs": total_firs,
            "active_districts": list(districts),
            "crime_categories": list(categories),
            "time_span_days": time_span_days,
            "recency_days": recency_days,
            "risk_level": risk_level,
            "officer_summary": summary,
            "linked_firs": list(unique_firs.keys())
        }
