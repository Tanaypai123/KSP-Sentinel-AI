import logging
from typing import Dict, Any, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import text as sa_text

from app.ai.sql_generator import generate_select
from app.ai.query_executor import execute_query
from app.ai.response_generator import ResponseGenerator
from app.ai.action_dispatcher import ActionDispatcher

logger = logging.getLogger(__name__)

class SearchService:
    """
    Unified lightweight orchestration service for Natural Language query pipelines.
    Adheres strictly to the pure orchestration principle.
    """

    @staticmethod
    def get_case_details(case_id: int, db: Session) -> Optional[Dict[str, Any]]:
        stmt = generate_select({"intent": "FIR_LOOKUP", "entities": {}})
        from app.models.case import CaseMaster
        stmt = stmt.where(CaseMaster.case_master_id == case_id)
        
        results = execute_query(db, stmt)
        if not results:
            return None
            
        SearchService._enrich_results(db, results)
        return results[0]

    @staticmethod
    def search(query: str, db: Session, conversation_id: Optional[str] = None, skip_cache: bool = False) -> Dict[str, Any]:
        """Unified lightweight orchestration pipeline using PipelineRunner."""
        from app.ai.pipeline_runner import PipelineRunner
        context = PipelineRunner.run(query, db, conversation_id=conversation_id)
        return context.response

    @staticmethod
    async def search_async(query: str, db: Session, conversation_id: Optional[str] = None, skip_cache: bool = False) -> Dict[str, Any]:
        """Asynchronous wrapper for SearchService.search running inside non-blocking threads."""
        from app.core.async_adapter import AsyncExecutionAdapter
        return await AsyncExecutionAdapter.run(SearchService.search, query, db, conversation_id=conversation_id, skip_cache=skip_cache)

    @staticmethod
    def _handle_context_flow(query: str, merged_query: dict, intent_val: str, entities: dict, intent_result, is_followup_intent: bool, state, db: Session, start_time: float):
        active_fir = state.active_fir
        active_accused = state.active_accused

        if intent_result.is_comparison:
            comp_firs = state._active_records
            if len(comp_firs) < 2:
                return ResponseGenerator.build_comparison_error(entities, comp_firs, intent_result.confidence, start_time)
            return ResponseGenerator.build_comparison(comp_firs[0], comp_firs[1], entities, comp_firs, intent_result.confidence, start_time)

        if intent_result.is_similar_search:
            entities["crime_head"] = active_fir.get("crime_category", active_fir.get("crime_head")) if active_fir else None
            entities["district"] = active_fir.get("district_name", active_fir.get("district")) if active_fir else None
            entities["identifiers"] = []
            merged_query["intent"] = "SEARCH_CASES"
            merged_query["_is_followup"] = False
            return None

        if intent_result.is_accused_followup:
            followup_res = SearchService._handle_accused_followup_context(merged_query, active_accused, intent_result)
            if followup_res is not None:
                return followup_res

        if intent_result.is_smart_action:
            if not active_fir:
                return ResponseGenerator.build_smart_action_response("UNKNOWN", "Please open an FIR before running this action.", entities, [], intent_result.confidence, start_time)
            
            action_resp = ActionDispatcher.dispatch(intent_result.smart_action_type, active_fir, entities, db)
            
            merged_query["intent"] = action_resp.intent_val
            merged_query["entities"] = action_resp.entities
            
            if action_resp.results is not None:
                if action_resp.needs_enrichment:
                    SearchService._enrich_results(db, action_resp.results)
                return ResponseGenerator.build_smart_action_response(action_resp.intent_val, action_resp.synthetic_summary, action_resp.entities, action_resp.results, intent_result.confidence, start_time)
            return None

        if active_fir:
            resolved, summary = SearchService._resolve_active_fir_entity(intent_val, active_fir, intent_result)
            if resolved:
                return ResponseGenerator.build_active_context_resolution(intent_val, summary, entities, active_fir, intent_result.confidence, start_time)

        return None

    @staticmethod
    def _handle_accused_followup_context(merged_query: dict, active_accused: dict, intent_result):
        linked = active_accused.get("linked_firs", []) if active_accused else []
        
        if intent_result.accused_followup_type == "OTHER_FIRS":
            if len(linked) >= 1:
                merged_query["entities"]["identifiers"] = linked
                merged_query["intent"] = "FIR_LOOKUP"
                merged_query["_is_followup"] = False
                return None
            else:
                name = active_accused.get("accused_name", "the selected accused").title() if active_accused else "the selected accused"
                summary = f"No FIRs found for {name}."
                merged_query["intent"] = "SEARCH_CASES"
                return ResponseGenerator.build_active_context_resolution("SEARCH_CASES", summary, merged_query["entities"], None, intent_result.confidence, 0.0)
                
        elif intent_result.accused_followup_type == "SAME_FIR":
            if len(linked) >= 1:
                merged_query["entities"]["identifiers"] = linked
                merged_query["intent"] = "FIR_LOOKUP"
                merged_query["_is_followup"] = False
                return None
            else:
                name = active_accused.get("accused_name", "the selected accused").title() if active_accused else "the selected accused"
                summary = f"No FIRs found for {name}."
                merged_query["intent"] = "SEARCH_CASES"
                return ResponseGenerator.build_active_context_resolution("SEARCH_CASES", summary, merged_query["entities"], None, intent_result.confidence, 0.0)
        return None

    @staticmethod
    def _resolve_active_fir_entity(intent_val: str, active_fir: dict, intent_result) -> Tuple[bool, Optional[str]]:
        resolved = False
        summary = None
        
        if intent_val == "SEARCH_ACCUSED":
            names = active_fir.get("accused_names", active_fir.get("accused_name", "Unknown Accused"))
            if isinstance(names, list): names = ", ".join(names)
            if not names or names.lower() in ["not available", "unknown accused", "none"]:
                summary = "Accused information is unavailable for the active FIR."
            else:
                summary = f"The active FIR identifies {names} as the primary accused."
            resolved = True
        elif intent_val == "SEARCH_VICTIMS":
            names = active_fir.get("victim_names", active_fir.get("victim_name", "Unknown Victim"))
            if isinstance(names, list): names = ", ".join(names)
            if not names or names.lower() in ["not available", "unknown victim", "none"]:
                summary = "Victim information is unavailable for the active FIR."
            else:
                summary = f"The victims associated with this FIR are {names}."
            resolved = True
        elif intent_val == "SEARCH_POLICE_STATION":
            ps = active_fir.get("police_station_name", active_fir.get("police_station", "Unknown Police Station"))
            if not ps or ps.lower() in ["not available", "none"]:
                summary = "Police Station information is unavailable."
            else:
                summary = f"This case falls under the jurisdiction of {ps}."
            resolved = True
        elif intent_val == "SEARCH_LOCATION":
            dist = active_fir.get("district_name", active_fir.get("district", "Unknown District"))
            if not dist or dist.lower() in ["not available", "none"]:
                summary = "District information is unavailable."
            else:
                summary = f"This incident occurred within the {dist} district."
            resolved = True
        elif intent_val == "SEARCH_OFFICER":
            io = active_fir.get("investigating_officer", active_fir.get("io_name", "Unknown Investigating Officer"))
            if not io or io.lower() in ["not available", "unknown investigating officer", "none", "null"]:
                summary = "Officer not yet assigned to this investigation."
            else:
                summary = f"The primary investigating officer is {io}."
            resolved = True
        elif intent_val == "AGGREGATE_COUNT":
            status = active_fir.get("status_name", active_fir.get("case_status", "Unknown Status"))
            if not status or status.lower() in ["not available", "unknown status", "none"]:
                summary = "The investigation status is currently unavailable."
            else:
                summary = f"The active FIR indicates the current investigation status is {status}."
            resolved = True
        elif intent_val == "CRIME_TREND":
            date = active_fir.get("crime_registered_date", "Unknown Date")
            if not date or date.lower() in ["not available", "unknown date", "none"]:
                summary = "Registration date is unavailable."
            else:
                summary = f"This FIR was officially registered on {date}."
            resolved = True
        elif intent_val == "FIR_LOOKUP":
            if not intent_result.is_fir_open_query:
                resolved = True
                
        return resolved, summary

    @staticmethod
    def _enrich_results(db: Session, results: list):
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
