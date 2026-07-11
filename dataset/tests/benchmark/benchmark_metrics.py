import math
from typing import Dict, Any, List

class BenchmarkMetrics:
    @staticmethod
    def calculate_scores(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        total_turns = 0
        intent_matches = 0
        entity_matches = 0
        conversation_matches = 0
        reference_resolution_matches = 0
        topic_shift_matches = 0
        clarification_matches = 0
        reasoning_matches = 0
        confidence_matches = 0
        hallucination_count = 0
        failures = 0
        crashes = 0
        latencies = []
        
        # Track turn subsets for topic shifts and reference resolutions
        topic_shift_turns = 0
        reference_resolution_turns = 0

        for item in results:
            turns_data = item.get("turns", [])
            conv_id = item.get("conversation_id", "")
            
            for idx, turn in enumerate(turns_data):
                total_turns += 1
                latencies.append(turn.get("latency_ms", 0.0))

                # 1. Intent Accuracy
                if turn.get("intent_match", False):
                    intent_matches += 1

                # 2. Entity Accuracy
                exp_ent = turn.get("expected_entities", {})
                pred_ent = turn.get("predicted_entities", {})
                ent_match = True
                for k, v in exp_ent.items():
                    if pred_ent.get(k) != v:
                        ent_match = False
                        break
                if ent_match:
                    entity_matches += 1

                # 3. Conversation Accuracy (Verify predicted state is saved in ConversationState)
                state = turn.get("state", {})
                state_match = True
                if turn.get("intent_match", False):
                    # Saved state intent should match predicted intent
                    if state.get("last_intent") != turn.get("predicted_intent"):
                        state_match = False
                else:
                    state_match = False
                if state_match:
                    conversation_matches += 1

                # 4. Reference Resolution Accuracy (Check pronoun/ordinal resolution turns)
                exp_ctx = turn.get("expected_context", {})
                if exp_ctx:
                    reference_resolution_turns += 1
                    ref_resolved = True
                    for k, v in exp_ctx.items():
                        if k == "active_fir" and not state.get("active_fir"):
                            ref_resolved = False
                        elif k == "active_accused" and not state.get("active_accused"):
                            ref_resolved = False
                        elif k == "active_district" and not state.get("active_district"):
                            ref_resolved = False
                    if ref_resolved:
                        reference_resolution_matches += 1

                # 5. Topic Shift Accuracy
                if "topic_shift" in conv_id and idx > 0:
                    topic_shift_turns += 1
                    # In a topic shift, expected entities from the new turn should match, and old keys should be cleared
                    if ent_match and state.get("last_intent") == turn.get("predicted_intent"):
                        topic_shift_matches += 1

                # 6. Clarification Accuracy
                if turn.get("expected_clarification", False) == turn.get("predicted_clarification", False):
                    clarification_matches += 1

                # 7. Reasoning Accuracy
                if turn.get("expected_reasoning_presence", False) == turn.get("predicted_reasoning", False):
                    reasoning_matches += 1

                # 8. Confidence Accuracy
                conf = turn.get("confidence", 0.0)
                conf_range = turn.get("expected_confidence_range", [0.0, 1.0])
                if conf_range[0] <= conf <= conf_range[1]:
                    confidence_matches += 1

                # 9. Hallucination Rate
                sql = turn.get("sql_route") or ""
                if sql and "WHERE" in sql.upper():
                    q_low = turn.get("query", "").lower()
                    import re
                    sql_literals = re.findall(r"'(.*?)'", sql)
                    has_hallucination = False
                    for lit in sql_literals:
                        if lit in ["Mysuru", "Dharwad", "Bengaluru Urban", "Mandya", "Belagavi", "Tumakuru", "Shivamogga", "Kodagu"] and lit.lower() not in q_low:
                            state_dist = state.get("active_district") or {}
                            state_dist_name = state_dist.get("district_name") if isinstance(state_dist, dict) else ""
                            if state_dist_name != lit:
                                has_hallucination = True
                                break
                    if has_hallucination:
                        hallucination_count += 1

                # 10. Pipeline Failures and Crash Rate
                if turn.get("failed", False):
                    failures += 1
                if turn.get("crashed", False):
                    crashes += 1

        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        sorted_latencies = sorted(latencies) if latencies else [0.0]
        
        def pct(p):
            idx = math.ceil((len(sorted_latencies) * p) / 100) - 1
            return sorted_latencies[max(0, min(idx, len(sorted_latencies) - 1))]

        return {
            "total_turns": total_turns,
            "intent_accuracy": (intent_matches / total_turns * 100) if total_turns else 100.0,
            "entity_accuracy": (entity_matches / total_turns * 100) if total_turns else 100.0,
            "conversation_accuracy": (conversation_matches / total_turns * 100) if total_turns else 100.0,
            "reference_resolution_accuracy": (reference_resolution_matches / reference_resolution_turns * 100) if reference_resolution_turns else 100.0,
            "topic_shift_accuracy": (topic_shift_matches / topic_shift_turns * 100) if topic_shift_turns else 100.0,
            "clarification_accuracy": (clarification_matches / total_turns * 100) if total_turns else 100.0,
            "reasoning_accuracy": (reasoning_matches / total_turns * 100) if total_turns else 100.0,
            "confidence_accuracy": (confidence_matches / total_turns * 100) if total_turns else 100.0,
            "hallucination_rate": (hallucination_count / total_turns * 100) if total_turns else 0.0,
            "failure_rate": (failures / total_turns * 100) if total_turns else 0.0,
            "crash_rate": (crashes / total_turns * 100) if total_turns else 0.0,
            "exception_count": crashes,
            "avg_latency_ms": avg_latency,
            "p95_latency_ms": pct(95),
            "p99_latency_ms": pct(99)
        }
