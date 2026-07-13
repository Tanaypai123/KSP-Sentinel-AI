import time
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

@dataclass
class InvestigationMemory:
    conversation_id: str
    active_fir: Optional[Dict[str, Any]] = None
    active_case: Optional[Dict[str, Any]] = None
    active_accused: Optional[Dict[str, Any]] = None
    active_victim: Optional[Dict[str, Any]] = None
    active_station: Optional[Dict[str, Any]] = None
    active_district: Optional[Dict[str, Any]] = None
    active_vehicle: Optional[Dict[str, Any]] = None
    active_weapon: Optional[Dict[str, Any]] = None
    active_hotspot: Optional[Dict[str, Any]] = None
    active_crime: Optional[str] = None
    active_recommendation: Optional[List[Dict[str, Any]]] = None
    last_reasoning: Optional[Dict[str, Any]] = None
    last_evidence: Optional[List[Dict[str, Any]]] = None
    last_sql_filters: Optional[Dict[str, Any]] = None
    clarification_state: Optional[Dict[str, Any]] = None
    followup_chain: List[str] = field(default_factory=list)
    entity_history: List[Dict[str, Any]] = field(default_factory=list)
    intent_history: List[str] = field(default_factory=list)
    analytics_history: List[Dict[str, Any]] = field(default_factory=list)
    execution_history: List[Dict[str, Any]] = field(default_factory=list)
    confidence_history: List[float] = field(default_factory=list)
    timestamps: Dict[str, Any] = field(default_factory=dict)


class MemoryEngine:
    """
    Enterprise Investigation Memory Engine:
    Maintains structured investigation context deterministically across pipeline runs.
    """
    _memories: Dict[str, InvestigationMemory] = {}
    _audits: Dict[str, List[Dict[str, Any]]] = {}
    
    TTL_SECONDS: float = 300.0  # Configurable session timeout threshold

    @classmethod
    def get_memory(cls, conversation_id: str) -> Optional[InvestigationMemory]:
        """
        Retrieves active investigation memory, enforcing TTL safety.
        """
        if conversation_id not in cls._memories:
            return None
            
        memory = cls._memories[conversation_id]
        last_updated = memory.timestamps.get("last_updated_time", 0.0)
        
        if time.time() - last_updated > cls.TTL_SECONDS:
            logger.info(f"MemoryEngine: Session expired for conversation_id={conversation_id}. Resetting state.")
            cls.reset_memory(conversation_id)
            return None
            
        return memory

    @classmethod
    def reset_memory(cls, conversation_id: str) -> None:
        """
        Deterministically clears the investigation memory for a given conversation.
        """
        if conversation_id in cls._memories:
            del cls._memories[conversation_id]
        if conversation_id in cls._audits:
            del cls._audits[conversation_id]
        logger.debug(f"MemoryEngine: Reset state completed for conversation_id={conversation_id}.")

    @classmethod
    def get_audit_trail(cls, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Returns full audit change logs for a given conversation.
        """
        return cls._audits.get(conversation_id, [])

    @classmethod
    def update_memory(cls, context: Any) -> Optional[Dict[str, Any]]:
        """
        Evaluates execution success gates and updates InvestigationMemory version if clean.
        """
        conversation_id = context.conversation_id or "default"
        
        # ── SAFETY GATE CHECKS ───────────────────────────────────────────────
        if not getattr(context, "hallucination_safe", True):
            logger.warning("MemoryEngine: Safety gate block - Hallucination detected. State update suppressed.")
            return None
            
        if getattr(context, "warnings", []):
            logger.warning("MemoryEngine: Safety gate block - Execution warnings detected. State update suppressed.")
            return None
            
        if context.reasoning_result and context.reasoning_result.get("conclusion") == "Insufficient evidence.":
            logger.warning("MemoryEngine: Safety gate block - Insufficient evidence conclusion. State update suppressed.")
            return None

        # Fetch or initialize memory
        memory = cls._memories.get(conversation_id)
        is_new = memory is None
        if is_new:
            memory = InvestigationMemory(conversation_id=conversation_id)
            memory.timestamps = {
                "created_time": time.time(),
                "last_updated_time": time.time(),
                "version": 0
            }
            cls._memories[conversation_id] = memory

        # Track audit details
        version = memory.timestamps.get("version", 0) + 1
        changes = []
        
        def track_change(field_name: str, new_value: Any, reason: str):
            old_value = getattr(memory, field_name)
            # Compare to avoid audit clutter if unchanged
            if old_value != new_value:
                setattr(memory, field_name, new_value)
                changes.append({
                    "field": field_name,
                    "old_value": old_value,
                    "new_value": new_value,
                    "reason": reason
                })

        resolved = context.resolved_entities or {}
        
        # 1. Update active entities
        if context.search_result:
            track_change("active_fir", context.search_result[0], "Updated active FIR record based on query search result.")
            track_change("active_case", context.search_result[0], "Updated active case details.")
        
        if resolved.get("accused_name"):
            track_change("active_accused", {"accused_name": resolved["accused_name"]}, "Updated accused based on search query.")
        elif context.search_result and context.search_result[0].get("accused_name"):
            track_change("active_accused", {"accused_name": context.search_result[0]["accused_name"]}, "Updated accused from result row.")

        if resolved.get("victim_name"):
            track_change("active_victim", {"victim_name": resolved["victim_name"]}, "Updated victim based on search query.")
        elif context.search_result and context.search_result[0].get("victim_name"):
            track_change("active_victim", {"victim_name": context.search_result[0]["victim_name"]}, "Updated victim from result row.")

        if resolved.get("police_station"):
            track_change("active_station", {"police_station": resolved["police_station"]}, "Updated active police station.")
            
        if resolved.get("district"):
            track_change("active_district", {"district": resolved["district"]}, "Updated active district.")

        if resolved.get("vehicle") or resolved.get("vehicle_number"):
            veh = resolved.get("vehicle") or resolved.get("vehicle_number")
            track_change("active_vehicle", {"vehicle": veh}, "Updated active vehicle parameter.")

        if resolved.get("weapon"):
            track_change("active_weapon", {"weapon": resolved["weapon"]}, "Updated active weapon parameter.")

        if resolved.get("crime_category") or resolved.get("crime_head"):
            crime = resolved.get("crime_category") or resolved.get("crime_head")
            track_change("active_crime", crime, "Updated active crime category.")

        # 2. Analytics Memory
        intel = context.intelligence_bundle
        if intel:
            if getattr(intel, "hotspots", None):
                track_change("active_hotspot", intel.hotspots, "Stored computed crime hotspot map.")
            if getattr(intel, "recommendations", None):
                track_change("active_recommendation", intel.recommendations, "Stored generated investigator recommendations.")
            if getattr(intel, "execution_trace", None):
                memory.analytics_history.append(list(intel.execution_trace))

        # 3. Reasoning & Evidence Memory
        track_change("last_reasoning", context.reasoning_result, "Stored latest evaluation logic chain.")
        track_change("last_evidence", context.search_result, "Stored matches of database query search result.")
        track_change("last_sql_filters", resolved, "Stored extracted entity filter attributes.")

        # 4. Clarification Memory
        if context.conversation_state:
            clar_state = {
                "pending": getattr(context.conversation_state, "pending_clarification", False),
                "query": getattr(context.conversation_state, "clarification_query", None),
                "options": getattr(context.conversation_state, "clarification_options", [])
            }
            track_change("clarification_state", clar_state, "Updated conversation clarification checkpoint.")

        # 5. History Lists
        memory.followup_chain.append(context.raw_query)
        memory.entity_history.append(resolved)
        memory.intent_history.append(context.intent or "UNKNOWN")
        memory.execution_history.append([trace["stage"] for trace in context.execution_trace])
        memory.confidence_history.append(context.confidence.get("final", 0.50))

        # Update timestamps & versioning
        memory.timestamps["last_updated_time"] = time.time()
        memory.timestamps["version"] = version

        # Compile changes summary
        change_summary = f"Memory updated to version {version}."
        if changes:
            change_summary = f"Version {version} changes: " + ", ".join([f"{c['field']} updated" for c in changes])

        audit_record = {
            "version": version,
            "timestamp": time.time(),
            "changes": changes,
            "summary": change_summary
        }

        if conversation_id not in cls._audits:
            cls._audits[conversation_id] = []
        cls._audits[conversation_id].append(audit_record)

        return audit_record


class MemoryEngineStage:
    """
    Pipeline stage wrapper for MemoryEngine.
    """

    @staticmethod
    def run(context: Any) -> Any:  # context: ExecutionContext
        try:
            # Execute memory update step
            audit = MemoryEngine.update_memory(context)
            if audit:
                context.memory_audit = audit
                # Sync back key values to ConversationState for complete backwards compatibility
                state = context.conversation_state
                mem = MemoryEngine.get_memory(context.conversation_id)
                if state and mem:
                    state.active_fir = mem.active_fir
                    state.active_accused = mem.active_accused
                    state.active_victim = mem.active_victim
                    state.active_station = mem.active_station
                    state.active_district = mem.active_district
                    # Persist the synced state to the store so future reloads see updated active_fir
                    from app.ai.conversation_engine import ConversationEngine
                    store_state = ConversationEngine.get_state(context.conversation_id)
                    store_state.active_fir = mem.active_fir
                    store_state.active_accused = mem.active_accused
                    store_state.active_victim = mem.active_victim
                    ConversationEngine.get_store().save(context.conversation_id, store_state)
        except Exception as e:
            logger.error(f"MemoryEngineStage failed: {e}", exc_info=True)
            context.warnings.append(f"MemoryEngineStage failed: {e}")
        return context
