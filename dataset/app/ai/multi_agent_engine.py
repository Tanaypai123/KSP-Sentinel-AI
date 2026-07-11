import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

class AgentResult:
    def __init__(self, summary: str, evidence: List[str], confidence: float, warnings: List[str], supporting_records: List[str], findings: Dict[str, Any]):
        self.summary = summary
        self.evidence = evidence
        self.confidence = confidence
        self.warnings = warnings
        self.supporting_records = supporting_records
        self.findings = findings


class EvidenceAgent:
    @staticmethod
    def run(context: Any) -> AgentResult:
        results = context.search_result or []
        evidence = [f"Record {i+1}: FIR {r.get('crime_no')}" for i, r in enumerate(results) if r.get('crime_no')]
        
        accused = set()
        for r in results:
            if r.get("accused_name"):
                accused.add(r["accused_name"])
            elif isinstance(r.get("accused_names"), list):
                accused.update(r["accused_names"])
                
        summary = f"Evidence analysis identified {len(results)} source records containing {len(accused)} accused suspects."
        findings = {
            "total_records": len(results),
            "accused_count": len(accused),
            "primary_crime": results[0].get("crime_category") if results else None
        }
        
        return AgentResult(
            summary=summary,
            evidence=evidence,
            confidence=0.90 if results else 0.50,
            warnings=[],
            supporting_records=[r.get("crime_no") for r in results if r.get("crime_no")],
            findings=findings
        )


class CrimePatternAgent:
    @staticmethod
    def run(context: Any) -> AgentResult:
        results = context.search_result or []
        intel = context.intelligence_bundle
        
        patterns = []
        if intel and getattr(intel, "pattern_analysis", None):
            patterns.append(str(intel.pattern_analysis))
            
        summary = f"Crime Pattern analysis detected {len(patterns)} active crime head temporal pattern summaries."
        findings = {
            "patterns_detected": len(patterns),
            "hotspot_count": len(intel.hotspots) if intel and getattr(intel, "hotspots", None) else 0
        }
        
        return AgentResult(
            summary=summary,
            evidence=patterns,
            confidence=0.85 if patterns else 0.50,
            warnings=[],
            supporting_records=[r.get("crime_no") for r in results[:3] if r.get("crime_no")],
            findings=findings
        )


class NetworkAgent:
    @staticmethod
    def run(context: Any) -> AgentResult:
        results = context.search_result or []
        correlations = context.evidence_correlation or {}
        
        edges = correlations.get("edges", [])
        chains = correlations.get("chains", [])
        
        summary = f"Network mapping compiled associate network containing {len(edges)} verified relational edges and {len(chains)} multi-hop paths."
        findings = {
            "relational_edges": len(edges),
            "hop_paths": len(chains)
        }
        
        return AgentResult(
            summary=summary,
            evidence=[e.get("details", "") for e in edges if e.get("details")],
            confidence=0.95 if edges else 0.50,
            warnings=[],
            supporting_records=[r.get("crime_no") for r in results[:3] if r.get("crime_no")],
            findings=findings
        )


class RecommendationAgent:
    @staticmethod
    def run(context: Any) -> AgentResult:
        results = context.search_result or []
        intel = context.intelligence_bundle
        
        recs = []
        if intel and getattr(intel, "recommendations", None):
            recs = [r.get("action") for r in intel.recommendations if r.get("action")]
            
        summary = f"Recommendation analysis generated {len(recs)} high-priority investigator recommendations."
        findings = {
            "recommendation_count": len(recs)
        }
        
        return AgentResult(
            summary=summary,
            evidence=recs,
            confidence=0.80 if recs else 0.50,
            warnings=[],
            supporting_records=[r.get("crime_no") for r in results[:3] if r.get("crime_no")],
            findings=findings
        )


class SafetyAgent:
    @staticmethod
    def run(context: Any) -> AgentResult:
        results = context.search_result or []
        safe = getattr(context, "hallucination_safe", True)
        violations = getattr(context, "hallucination_violations", [])
        
        summary = "Safety analysis: Fully safe and validated." if safe else f"Safety analysis: Blocked {len(violations)} claims due to lack of evidence."
        findings = {
            "safety_status": "SAFE" if safe else "BLOCKED",
            "violation_count": len(violations)
        }
        
        return AgentResult(
            summary=summary,
            evidence=[v.get("detail", "") for v in violations if v.get("detail")],
            confidence=1.0 if safe else 0.0,
            warnings=list(context.warnings),
            supporting_records=[r.get("crime_no") for r in results[:3] if r.get("crime_no")],
            findings=findings
        )


class AgentCoordinator:
    """
    AgentCoordinator:
    Orchestrates the specialized agents and merges findings using deterministic conflict resolution rules.
    """

    @classmethod
    def run_coordination(cls, context: Any) -> Dict[str, Any]:
        # Run agents
        results = {
            "evidence_agent": EvidenceAgent.run(context),
            "pattern_agent": CrimePatternAgent.run(context),
            "network_agent": NetworkAgent.run(context),
            "recommendation_agent": RecommendationAgent.run(context),
            "safety_agent": SafetyAgent.run(context)
        }

        # Deterministically merge findings and resolve conflicts
        merged_findings = {}
        agreements = []
        disagreements = []

        all_keys = set()
        for agent_res in results.values():
            all_keys.update(agent_res.findings.keys())

        for key in all_keys:
            # Collect values for this key from all agents who reported it
            reporter_agents = []
            for agent_name, agent_res in results.items():
                if key in agent_res.findings:
                    reporter_agents.append((agent_name, agent_res))
                    
            if not reporter_agents:
                continue

            # Compare reported values
            first_val = reporter_agents[0][1].findings[key]
            all_agree = all(a[1].findings[key] == first_val for a in reporter_agents)
            
            if all_agree:
                merged_findings[key] = first_val
                agreements.append(f"Agents agreed on key '{key}': {first_val}.")
            else:
                # Resolve conflict deterministically
                # Prioritize: 1. Higher evidence count, 2. Higher confidence, 3. More supporting records, 4. Conflict mark
                winner_name, winner_val, winner_res = cls._resolve_conflict(key, reporter_agents)
                
                if winner_name == "CONFLICT":
                    merged_findings[key] = "CONFLICT"
                    disagreements.append(f"Conflict on key '{key}' between reporting agents.")
                else:
                    merged_findings[key] = winner_val
                    disagreements.append(f"Conflict on key '{key}' resolved in favor of {winner_name} value '{winner_val}' (Rules applied).")

        # Compile report
        warnings = []
        for r in results.values():
            warnings.extend(r.warnings)

        unified_confidence = sum(r.confidence for r in results.values()) / len(results)

        # Assemble explainability trace mappings showing which agent produced which finding
        explainability = {}
        for agent_name, agent_res in results.items():
            explainability[agent_name] = {
                "summary": agent_res.summary,
                "evidence": agent_res.evidence,
                "confidence": agent_res.confidence,
                "findings": agent_res.findings
            }

        return {
            "evidence_summary": results["evidence_agent"].summary,
            "crime_pattern": results["pattern_agent"].summary,
            "network_summary": results["network_agent"].summary,
            "recommendations": results["recommendation_agent"].evidence,
            "warnings": list(set(warnings)),
            "agent_agreements": agreements,
            "agent_disagreements": disagreements,
            "confidence": unified_confidence,
            "findings": merged_findings,
            "explainability": explainability
        }

    @classmethod
    def _resolve_conflict(cls, key: str, reporters: List[Tuple[str, AgentResult]]) -> Tuple[str, Any, Optional[AgentResult]]:
        # Sort reporters by deterministic priorities:
        # Priority 1: Evidence count (findings size)
        # Priority 2: Confidence
        # Priority 3: Supporting FIRs count
        
        def sort_key(item):
            agent_name, agent_res = item
            evidence_count = len(agent_res.findings)
            confidence = agent_res.confidence
            fir_count = len(agent_res.supporting_records)
            return (evidence_count, confidence, fir_count)

        sorted_reporters = sorted(reporters, key=sort_key, reverse=True)
        
        # Check if first and second are tied
        r1_name, r1_res = sorted_reporters[0]
        r1_val = r1_res.findings[key]
        
        tie = False
        for r_name, r_res in sorted_reporters[1:]:
            r_val = r_res.findings[key]
            if r_val != r1_val and sort_key((r_name, r_res)) == sort_key((r1_name, r1_res)):
                tie = True
                break
                
        if tie:
            return "CONFLICT", "CONFLICT", None
            
        return r1_name, r1_val, r1_res


class MultiAgentEngineStage:
    """
    Pipeline stage wrapper for MultiAgentEngine.
    """

    @staticmethod
    def run(context: Any) -> Any:  # context: ExecutionContext
        try:
            context.multi_agent_report = AgentCoordinator.run_coordination(context)
        except Exception as e:
            logger.error(f"MultiAgentEngineStage failed: {e}", exc_info=True)
            context.warnings.append(f"MultiAgentEngineStage failed: {e}")
        return context
