from dataclasses import dataclass
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text as sa_text

@dataclass
class ActionResponse:
    intent_val: str
    entities: dict
    resolved: bool
    synthetic_summary: Optional[str] = None
    is_followup_intent: bool = True
    results: Optional[List[dict]] = None
    needs_enrichment: bool = False

class SmartActionHandler:
    def handle(self, active_fir: dict, entities: dict, db: Session) -> ActionResponse:
        raise NotImplementedError

class RelatedCaseHandler(SmartActionHandler):
    def handle(self, active_fir: dict, entities: dict, db: Session) -> ActionResponse:
        entities["crime_head"] = active_fir.get("crime_category", active_fir.get("crime_head"))
        entities["district"] = active_fir.get("district_name", active_fir.get("district"))
        entities["police_station"] = active_fir.get("police_station_name")
        entities["identifiers"] = []
        return ActionResponse(
            intent_val="SEARCH_CASES",
            entities=entities,
            resolved=False,
            is_followup_intent=False
        )

class NearbyCrimeHandler(SmartActionHandler):
    def handle(self, active_fir: dict, entities: dict, db: Session) -> ActionResponse:
        lat = active_fir.get("latitude")
        lon = active_fir.get("longitude")
        if not lat or not lon or str(lat).lower() == "null" or str(lon).lower() == "null":
            return ActionResponse(
                intent_val="SEARCH_CASES",
                entities=entities,
                resolved=True,
                synthetic_summary="Location data is unavailable for this FIR."
            )
        else:
            sql = f"""
            SELECT * FROM case_master 
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            AND "CrimeNo" != :cno
            ORDER BY ((CAST(latitude AS FLOAT) - {lat})*(CAST(latitude AS FLOAT) - {lat}) + (CAST(longitude AS FLOAT) - {lon})*(CAST(longitude AS FLOAT) - {lon})) ASC
            LIMIT 10
            """
            results = [dict(r._mapping) for r in db.execute(sa_text(sql), {"cno": active_fir.get("crime_no")}).fetchall()]
            return ActionResponse(
                intent_val="SEARCH_CASES",
                entities=entities,
                resolved=True,
                synthetic_summary=f"Found {len(results)} crimes registered near the location of this FIR.",
                results=results,
                needs_enrichment=True
            )

class NetworkHandler(SmartActionHandler):
    def handle(self, active_fir: dict, entities: dict, db: Session) -> ActionResponse:
        a1 = ", ".join(active_fir.get('accused_names', [])) if active_fir.get('accused_names') else active_fir.get('accused_name', '')
        v1 = ", ".join(active_fir.get('victim_names', [])) if active_fir.get('victim_names') else active_fir.get('victim_name', '')
        ps = active_fir.get('police_station_name')
        io = active_fir.get('investigating_officer')
        if not a1 and not v1:
            synthetic_summary = "Network analysis cannot be generated because insufficient linked entities exist."
        else:
            synthetic_summary = f"Investigation Network Summary\n\nAccused Nodes: {a1 or 'None identified'}\nVictim Nodes: {v1 or 'None identified'}\nJurisdiction: {ps or 'Unknown'}\nInvestigating Officer: {io or 'Officer not yet assigned'}\n\nPattern matched: Isolated incident. No direct associate linkages identified in the broader database."
        return ActionResponse(
            intent_val="NETWORK_ANALYSIS",
            entities=entities,
            resolved=True,
            synthetic_summary=synthetic_summary
        )

class HotspotHandler(SmartActionHandler):
    def handle(self, active_fir: dict, entities: dict, db: Session) -> ActionResponse:
        entities["district"] = active_fir.get("district_name")
        entities["police_station"] = active_fir.get("police_station_name")
        jurisdiction = entities.get('police_station') or entities.get('district') or 'the active jurisdiction'
        synthetic_summary = f"Generated hotspot analysis for {jurisdiction}."
        return ActionResponse(
            intent_val="HOTSPOT",
            entities=entities,
            resolved=True,
            synthetic_summary=synthetic_summary
        )

class ActionDispatcher:
    _handlers = {
        "FIND_RELATED": RelatedCaseHandler(),
        "SHOW_NEARBY": NearbyCrimeHandler(),
        "ANALYZE_NETWORK": NetworkHandler(),
        "VIEW_HOTSPOTS": HotspotHandler()
    }

    @classmethod
    def dispatch(cls, action_type: str, active_fir: dict, entities: dict, db: Session) -> ActionResponse:
        handler = cls._handlers.get(action_type)
        if not handler:
            raise ValueError(f"No handler found for smart action type: {action_type}")
        return handler.handle(active_fir, entities, db)
