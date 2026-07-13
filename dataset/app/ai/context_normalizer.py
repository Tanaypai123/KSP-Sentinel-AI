from dataclasses import dataclass, field
from typing import Any, List, Optional
from sqlalchemy import text
from app.database.connection import SessionLocal

@dataclass
class NormalizedEvidence:
    has_weapon: bool = False
    has_vehicle: bool = False
    has_witness: bool = False
    has_phone: bool = False
    has_financial_trail: bool = False

@dataclass
class NormalizedTimeline:
    registered_date: Optional[str] = None
    incident_from_date: Optional[str] = None
    arrest_date: Optional[str] = None
    chargesheet_date: Optional[str] = None
    has_gaps: bool = False

@dataclass
class CrimeClassification:
    crime_category: str = ""
    crime_head: str = ""
    crime_sub_head: str = ""

@dataclass
class NormalizedCase:
    fir_number: str
    status: str = "Unknown"
    classification: CrimeClassification = field(default_factory=CrimeClassification)
    evidence: NormalizedEvidence = field(default_factory=NormalizedEvidence)
    timeline: NormalizedTimeline = field(default_factory=NormalizedTimeline)
    accused_names: List[str] = field(default_factory=list)
    victim_names: List[str] = field(default_factory=list)

class ContextNormalizerStage:
    """
    Pipeline stage that converts raw database dictionaries into structured NormalizedCase
    objects, explicitly resolving relationships (like CrimeHead) that execute_query drops.
    """

    @staticmethod
    def run(context: Any) -> Any:
        db = getattr(context, "db", None)
        raw_results = getattr(context, "search_result", []) or []
        
        normalized_cases = []
        
        for raw in raw_results:
            fir_no = raw.get("crime_no") or raw.get("fir_number") or raw.get("case_no")
            if not fir_no:
                continue
                
            case = NormalizedCase(fir_number=fir_no)
            case.status = str(raw.get("case_status", raw.get("status_name", "Pending")))
            
            # Use auxiliary DB query to fetch the proper CrimeHead / Classification
            # because raw execute() often ignores related columns.
            cid = raw.get("case_master_id")
            if db and cid:
                # 1. Classification
                sql = text('''
                    SELECT ch."CrimeGroupName", csh."CrimeHeadName"
                    FROM case_master cm
                    LEFT JOIN crime_head ch ON cm."CrimeMajorHeadID" = ch."CrimeHeadID"
                    LEFT JOIN crime_sub_head csh ON cm."CrimeMinorHeadID" = csh."CrimeSubHeadID"
                    WHERE cm."CaseMasterID" = :cid
                ''')
                try:
                    res = db.execute(sql, {"cid": cid}).first()
                    if res:
                        group_name = res[0] or ""
                        head_name = res[1] or ""
                        case.classification.crime_category = group_name
                        case.classification.crime_head = head_name
                except Exception:
                    db.rollback()
                    
                # 2. Timeline (Dates)
                case.timeline.registered_date = str(raw.get("crime_registered_date")) if raw.get("crime_registered_date") else None
                case.timeline.incident_from_date = str(raw.get("incident_from_date")) if raw.get("incident_from_date") else None
                
                # Check for arrests
                arrest_sql = text('SELECT "ArrestDate" FROM arrest_surrender WHERE "CaseMasterID" = :cid LIMIT 1')
                try:
                    arrest = db.execute(arrest_sql, {"cid": cid}).first()
                    if arrest and arrest[0]:
                        case.timeline.arrest_date = str(arrest[0])
                except Exception:
                    db.rollback()

                # Check for charge sheets
                cs_sql = text('SELECT "ChargesheetDate" FROM chargesheet_details WHERE "CaseMasterID" = :cid LIMIT 1')
                try:
                    cs = db.execute(cs_sql, {"cid": cid}).first()
                    if cs and cs[0]:
                        case.timeline.chargesheet_date = str(cs[0])
                except Exception:
                    db.rollback()
                
                # 3. Evidence flags
                # Weapons / Tools
                weap_sql = text('SELECT COUNT(*) FROM property WHERE "CaseMasterID" = :cid AND ("PropertyCategory" ILIKE \'%weapon%\' OR "PropertyType" ILIKE \'%weapon%\')')
                try:
                    if db.execute(weap_sql, {"cid": cid}).scalar() > 0:
                        case.evidence.has_weapon = True
                except Exception:
                    db.rollback()
                
                # Vehicles
                veh_sql = text('SELECT COUNT(*) FROM vehicle WHERE "CaseMasterID" = :cid')
                try:
                    if db.execute(veh_sql, {"cid": cid}).scalar() > 0:
                        case.evidence.has_vehicle = True
                except Exception:
                    db.rollback()
                
                # Phones/Financial (check accused or victim details, or generic property)
                prop_sql = text('SELECT "PropertyType" FROM property WHERE "CaseMasterID" = :cid')
                try:
                    props = db.execute(prop_sql, {"cid": cid}).fetchall()
                    for p in props:
                        ptype = str(p[0]).lower() if p[0] else ""
                        if "phone" in ptype or "mobile" in ptype:
                            case.evidence.has_phone = True
                        if "cash" in ptype or "account" in ptype or "bank" in ptype:
                            case.evidence.has_financial_trail = True
                except Exception:
                    db.rollback()
                    
                # Witnesses (check Knowledge Graph or timeline fallback, for now we mock based on accused count)
                acc = raw.get("accused_names", [])
                case.accused_names = acc
                case.victim_names = raw.get("victim_names", [])
                if len(case.accused_names) > 0 and len(case.victim_names) > 0:
                    case.evidence.has_witness = True
            
            # Fallback if crime_head is still missing (use NLP structured extraction if available)
            if not case.classification.crime_head:
                nlp_type = getattr(context, "resolved_entities", {}).get("structured_crime_type")
                if nlp_type:
                    case.classification.crime_head = str(nlp_type).replace("_", " ").title()
                else:
                    nlp_head = getattr(context, "resolved_entities", {}).get("crime_head")
                    if nlp_head:
                        case.classification.crime_head = str(nlp_head).replace("_", " ").title()

            normalized_cases.append(case)
            
        context.normalized_cases = normalized_cases
        return context
