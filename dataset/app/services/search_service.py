import time
import logging
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session
from sqlalchemy import text as sa_text

from app.ai.pipeline import normalize_text, classify_pipeline_intent
from app.ai.query_parser import parse_query
from app.ai.conversation_memory import merge_with_last, update_state
from app.ai.sql_generator import generate_select
from app.ai.query_executor import execute_query
from app.ai.response_formatter import format_response
from app.ai.response_templates import CONVERSATIONAL_RESPONSES, get_invalid_district
from app.ai.insights import IntelligenceEngine
from app.core.cache import global_cache

logger = logging.getLogger(__name__)

_DEFAULT_SUGGESTIONS = [
    "Show theft cases in Bengaluru",
    "Predict crime trends for assault",
    "Show accused named Raju",
    "Open FIR KSP-000123"
]

class SearchService:
    @staticmethod
    def get_case_details(case_id: int, db: Session) -> Optional[Dict[str, Any]]:
        """
        Fetch a fully enriched case record for the detail page.
        This provides a complete payload matching the FIR search output.
        """
        stmt = generate_select({"intent": "FIR_LOOKUP", "entities": {}})
        # Add ID filter
        from app.models.case import CaseMaster
        stmt = stmt.where(CaseMaster.case_master_id == case_id)
        
        results = execute_query(db, stmt)
        if not results:
            return None
            
        # Enrich result
        SearchService._enrich_results(db, results)
        return results[0]

    @staticmethod
    def search(query: str, db: Session, skip_cache: bool = False) -> Dict[str, Any]:
        """
        Unified 8-step search pipeline for all textual queries.
        """
        start_time = time.time()
        
        # Step 1: Parse Entities First
        parsed_query = parse_query(query, db)
        entities = parsed_query.get("entities", {})
        
        # Step 2: Normalize and Classify Semantic Intent
        normalized_query = normalize_text(query)
        
        # Check for multiple distinct intents
        if " and " in normalized_query.lower():
            parts = normalized_query.lower().split(" and ")
            if len(parts) == 2:
                intent1, conf1 = classify_pipeline_intent(parts[0])
                intent2, conf2 = classify_pipeline_intent(parts[1])
                # If they are strong but conflicting intents (not just FIR lookup + SEARCH_CASES)
                if conf1 > 0.60 and conf2 > 0.60 and intent1 != intent2:
                    return SearchService._build_response(False, "UNKNOWN", "You have requested multiple actions. Please execute these requests one by one so I can give you the best results.", {}, [], start_time, 1.0, error="Multiple intents detected", suggestions=["Split your request into two separate queries."])

        intent, confidence = classify_pipeline_intent(normalized_query)
        intent_val = intent.value if hasattr(intent, 'value') else str(intent)
            
        # Step 3: Short-circuit Conversational Intents
        conversational_intents = ["GREETING", "GOODBYE", "THANKS", "HELP", "BOT_IDENTITY", "BOT_CAPABILITIES", "UNKNOWN"]
        if intent_val in conversational_intents:
            return SearchService._build_response(
                True if intent_val != "UNKNOWN" else False, intent_val, 
                CONVERSATIONAL_RESPONSES.get(intent_val, CONVERSATIONAL_RESPONSES["UNKNOWN"]), 
                {}, [], start_time, confidence, error="Low intent confidence" if intent_val == "UNKNOWN" else None
            )

        # Step 4: Confidence Engine Handling
        if confidence < 0.60:
            summary = f"I am not entirely sure what you want to do. Could you please clarify your request?"
            return SearchService._build_response(False, intent_val, summary, {}, [], start_time, confidence, error="Clarification required", suggestions=_DEFAULT_SUGGESTIONS)

        # Step 5: Merge with memory context
        merged_query = merge_with_last(parsed_query, query)
        merged_query["intent"] = intent_val
        entities = merged_query.get("entities", {})

        # Step 6: Invalid district check
        if not entities.get("structured_is_valid_district", True):
            raw_d = entities.get("structured_raw_district")
            suggestions = entities.get("structured_district_suggestions") or ["Mysuru", "Mandya", "Bengaluru Urban"]
            return SearchService._build_response(False, intent_val, get_invalid_district(raw_d, suggestions), entities, [], start_time, confidence, error=f"District '{raw_d}' not found", suggestions=[f"Show cases in {s}" for s in suggestions])

        # Step 7: Bypass for ML Predictor
        if intent_val == "PREDICT_CRIME":
            from app.ai.predictor import predict_crime
            prediction = predict_crime(db, merged_query)
            update_state(merged_query)
            
            explanation = {
                "intent": "PREDICT_CRIME",
                "entities": {k: v for k, v in entities.items() if v is not None and not k.startswith("structured_")},
                "reasoning": prediction.get("reasoning"),
                "filters": [f"{k}={v}" for k, v in entities.items() if v and not k.startswith("structured_")],
                "sql_summary": "None (Predictive OLS Model)",
                "algorithm": prediction.get("model_used"),
                "confidence": prediction.get("confidence"),
                "trend_direction": prediction.get("trend"),
                "risk_level": prediction.get("risk_level"),
                "historical_data_used": f"{prediction.get('data_points_used')} monthly records"
            }
            predicted_count = prediction.get("predicted_cases", 0)
            insights = IntelligenceEngine.generate_insights(db, intent_val, entities, predicted_count)
            recs = IntelligenceEngine.generate_recommendations(intent_val, entities, predicted_count)
            
            res = SearchService._build_response(True, "PREDICT_CRIME", prediction.get("reasoning"), entities, prediction.get("historical_counts", []), start_time, confidence, count=predicted_count)
            res["metadata"].update({"prediction": prediction, "rows_scanned": prediction.get("data_points_used"), "rows_returned": 1})
            res["insights"] = insights
            res["recommended_queries"] = recs
            res["explanation"] = explanation
            res["prediction"] = prediction
            return res

        # Normalize Intent for SQL Generation
        sql_intent = "SEARCH_CASES" if intent_val == "SEARCH_LOCATION" else intent_val
        merged_query["intent"] = sql_intent

        # Step 8: Build Search Plan and Execute
        select_stmt = generate_select(merged_query)
        
        # Restore original intent for response formatting
        merged_query["intent"] = intent_val
        
        if select_stmt is None:
            return SearchService._build_response(False, intent_val, "Unsupported query intent.", entities, [], start_time, confidence, error="SQL generation failed")
            
        results = execute_query(db, select_stmt)

        # Multi-Phase Fuzzy Suggestion Engine for 0 results
        if len(results) == 0 and intent_val in ["SEARCH_ACCUSED", "SEARCH_VICTIMS"]:
            # Extract the specific name we're looking for
            name_entity = None
            col_name = None
            table_name = None
            if intent_val == "SEARCH_ACCUSED" and entities.get("accused_name"):
                name_entity = entities.get("accused_name")
                col_name = "AccusedName"
                table_name = "accused"
            elif intent_val == "SEARCH_VICTIMS" and entities.get("victim_name"):
                name_entity = entities.get("victim_name")
                col_name = "VictimName"
                table_name = "victim"
                
            if name_entity:
                parts = name_entity.split()
                # Use the longest word for the fallback query
                search_word = max(parts, key=len) if parts else name_entity
                
                # Fetch candidates natively
                try:
                    prefix = search_word[:3] if len(search_word) >= 3 else search_word[:2]
                    if table_name == "accused":
                        from app.models.case import Accused
                        fuzzy_results = db.query(Accused.accused_name).filter(Accused.accused_name.ilike(f"{prefix}%")).limit(200).all()
                    else:
                        from app.models.case import Victim
                        fuzzy_results = db.query(Victim.victim_name).filter(Victim.victim_name.ilike(f"{prefix}%")).limit(200).all()
                        
                    candidates = [row[0] for row in fuzzy_results if row[0]]
                    
                    if candidates:
                        import difflib
                        # Rank locally using difflib
                        lower_name = name_entity.lower()
                        # Map lowercase back to original
                        lower_candidates = {c.lower(): c for c in candidates}
                        matches = difflib.get_close_matches(lower_name, list(lower_candidates.keys()), n=3, cutoff=0.5)
                        
                        if matches:
                            top_matches = [lower_candidates[m] for m in matches]
                            suggest_str = ", ".join(top_matches)
                            summary = f"I couldn't find an exact match for '{name_entity}'.\n\nHowever, I found similar names:\n- " + "\n- ".join(top_matches) + "\n\nWould you like to search one of these?"
                            return SearchService._build_response(False, intent_val, summary, entities, [], start_time, confidence, error="No exact match", suggestions=[f"Find {table_name} {m}" for m in top_matches])
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(f"Fuzzy match error: {e}")

        # Step 9: Rank/Filter Results
        if intent_val == "SEARCH_ACCUSED":
            seen_names = set()
            deduped = []
            for r in results:
                name = r.get("accused_name", "").lower()
                if name not in seen_names:
                    seen_names.add(name)
                    deduped.append(r)
            results = deduped

        if intent_val == "FIR_LOOKUP" and entities.get("identifiers"):
            variants = [v.lower() for v in entities["identifiers"]]
            exact = [r for r in results if str(r.get("crime_no", "")).lower() in variants or str(r.get("case_no", "")).lower() in variants or str(r.get("fir_no", "")).lower() in variants]
            if exact:
                results = exact
            if len(results) > 1:
                intent_val = "SEARCH_CASES"

            # Enrich FIR results with complete detail
            SearchService._enrich_results(db, results)

            # Smart Suggestions
            if not results:
                import re
                num_match = re.search(r'\d+', variants[0])
                if num_match:
                    target_num = int(num_match.group())
                    sample = db.execute(sa_text('SELECT "CrimeNo" FROM case_master ORDER BY "CaseMasterID" DESC LIMIT 100')).fetchall()
                    def _score_fir(crime_no: str) -> int:
                        m = re.search(r'\d+', str(crime_no))
                        if m:
                            return abs(int(m.group()) - target_num)
                        return 999999
                    sorted_sample = sorted([s[0] for s in sample], key=_score_fir)
                    entities["_dynamic_suggestions"] = sorted_sample[:5]
                else:
                    sample = db.execute(sa_text('SELECT "CrimeNo" FROM case_master ORDER BY "CaseMasterID" DESC LIMIT 5')).fetchall()
                    entities["_dynamic_suggestions"] = [s[0] for s in sample]
        
        if intent_val == "SEARCH_CASES" and not results:
            if entities.get("structured_is_valid_district") and entities.get("district"):
                d = entities.get("district")
                entities["_dynamic_suggestions"] = [
                    f"Show theft cases in {d}",
                    f"Show robbery cases in {d}",
                    f"Show latest FIRs in {d}",
                    f"Show crime trend in {d}"
                ]

        # Update Memory
        merged_query["results"] = results
        update_state(merged_query)

        # Pagination and formatting
        total_count = len(results)
        if not entities.get("limit"):
            results = results[:20]

        try:
            format_dict = format_response(intent_val, results, entities, total_count=total_count, db=db)
            summary = format_dict.get("summary", "")
        except Exception as fe:
            logger.error(f"Error formatting response: {fe}")
            summary = f"Found {len(results)} matching records."

        suggestions = entities.get("_dynamic_suggestions") or _DEFAULT_SUGGESTIONS
        res = SearchService._build_response(True, intent_val, summary, entities, results, start_time, confidence, count=total_count, suggestions=suggestions)
        
        # Post-process Insights
        res["insights"] = IntelligenceEngine.generate_insights(db, intent_val, entities, total_count)
        res["recommended_queries"] = IntelligenceEngine.generate_recommendations(intent_val, entities, total_count)
        
        # Explanation object for the frontend
        res["explanation"] = {
            "intent": intent_val,
            "entities": {k: v for k, v in entities.items() if v is not None and not k.startswith("structured_") and k != "_dynamic_suggestions"},
            "reasoning": "Analyzing database query logs for relevant case metrics.",
            "filters": [f"{k}={v}" for k, v in entities.items() if v and not k.startswith("structured_") and k != "_dynamic_suggestions"],
            "sql_summary": str(select_stmt.compile(compile_kwargs={"literal_binds": True})).replace('\n', ' ')
        }
        
        return res
        
    @staticmethod
    def _enrich_results(db: Session, results: list):
        """Fetch and inject complete relational data into case results."""
        for row in results:
            cid = row.get("case_master_id")
            if not cid:
                continue
            acc = db.execute(sa_text('SELECT "AccusedName" FROM accused WHERE "CaseMasterID" = :cid'), {"cid": cid}).fetchall()
            row["accused_names"] = [a[0] for a in acc] if acc else []
            vic = db.execute(sa_text('SELECT "VictimName" FROM victim WHERE "CaseMasterID" = :cid'), {"cid": cid}).fetchall()
            row["victim_names"] = [v[0] for v in vic] if vic else []
            sid = row.get("police_station_id")
            if sid:
                sta = db.execute(sa_text('SELECT u."UnitName", d."DistrictName" FROM unit u LEFT JOIN district d ON u."DistrictID" = d."DistrictID" WHERE u."UnitID" = :sid'), {"sid": sid}).first()
                if sta:
                    row["police_station_name"] = sta[0]
                    row["district_name"] = sta[1]
            oid = row.get("police_person_id")
            if oid:
                off = db.execute(sa_text('SELECT "FirstName" FROM employee WHERE "EmployeeID" = :oid'), {"oid": oid}).first()
                if off:
                    row["investigating_officer"] = off[0]
            chid = row.get("crime_major_head_id")
            if chid:
                ch = db.execute(sa_text('SELECT "CrimeGroupName" FROM crime_head WHERE "CrimeHeadID" = :chid'), {"chid": chid}).first()
                if ch:
                    row["crime_category"] = ch[0]
            stid = row.get("case_status_id")
            if stid:
                st = db.execute(sa_text('SELECT "CaseStatusName" FROM case_status_master WHERE "CaseStatusID" = :stid'), {"stid": stid}).first()
                if st:
                    row["status_name"] = st[0]

    @staticmethod
    def _build_response(success: bool, intent: str, summary: str, entities: dict, results: list, start_time: float, confidence: float, count: int = 0, error: str = None, suggestions: list = None) -> dict:
        duration = (time.time() - start_time) * 1000
        return {
            "success": success,
            "intent": intent,
            "summary": summary,
            "count": count,
            "entities": entities,
            "results": results,
            "metadata": {
                "query": "", # set by caller
                "query_time_ms": round(duration, 2),
                "cache_hit": False,
                "confidence": confidence,
                "suggestions": suggestions or []
            },
            "error": error,
            "insights": [],
            "recommended_queries": [],
            "explanation": {}
        }
