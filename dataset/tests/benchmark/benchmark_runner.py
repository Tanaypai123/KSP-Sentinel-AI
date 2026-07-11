import sys
import os
import time
import json
import traceback
import asyncio
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.services.search_service import SearchService
from app.database.connection import SessionLocal
from app.ai.conversation_engine import ConversationEngine
from tests.benchmark.benchmark_metrics import BenchmarkMetrics

def run_benchmark():
    print("=== STARTING SENTINEL AI BENCHMARK RUNNER ===")
    
    benchmark_dir = os.path.dirname(__file__)
    dataset_path = os.path.join(benchmark_dir, "golden_dataset.json")
    results_path = os.path.join(benchmark_dir, "benchmark_results.json")
    history_path = os.path.join(benchmark_dir, "benchmark_history.json")

    if not os.path.exists(dataset_path):
        print(f"Error: golden_dataset.json not found at {dataset_path}")
        sys.exit(1)

    with open(dataset_path, "r") as f:
        conversations = json.load(f)

    print(f"Loaded {len(conversations)} conversations from golden_dataset.json.")

    run_results = []
    total_latency = 0.0
    processed_turns = 0

    # Ensure clean state at start of benchmark run
    for conv in conversations:
        conv_id = conv["conversation_id"]
        ConversationEngine.reset(conv_id)

    # Sequentially run conversations (turns within a conversation must be executed in order)
    for idx, conv in enumerate(conversations):
        conv_id = conv["conversation_id"]
        turns_results = []

        for turn_idx, turn in enumerate(conv["turns"]):
            query = turn["query"]
            db = SessionLocal()
            start_time = time.time()
            
            crashed = False
            failed = False
            predicted_intent = "UNKNOWN"
            confidence = 0.0
            predicted_entities = {}
            sql_route = None
            stages_executed = []
            reasoning_triggered = False
            predicted_clarification = False
            response_data = None
            error_message = None

            try:
                # Execute through production SearchService (non-async for deterministic sequency)
                res = SearchService.search(query, db, conversation_id=conv_id)
                response_data = res
                
                if not res or not isinstance(res, dict):
                    failed = True
                else:
                    predicted_intent = res.get("intent", "UNKNOWN")
                    confidence = res.get("metadata", {}).get("confidence", 0.0)
                    predicted_entities = res.get("entities", {})
                    sql_route = res.get("metadata", {}).get("sql")
                    
                    # Capture trace details
                    stages_executed = res.get("metadata", {}).get("execution_trace", [])
                    # Check if reasoning or intelligence engine executed
                    for stage in stages_executed:
                        if "IntelligenceEngineStage" in stage.get("stage", ""):
                            reasoning_triggered = True
                        if "ClarificationCheckStage" in stage.get("stage", "") and res.get("clarification_options"):
                            predicted_clarification = True
            except Exception as e:
                crashed = True
                failed = True
                error_message = f"{e}\n{traceback.format_exc()}"
            finally:
                db.close()

            latency_ms = (time.time() - start_time) * 1000.0
            total_latency += latency_ms
            processed_turns += 1

            # Fetch final conversation state for turn analysis
            state_obj = ConversationEngine.get_state(conv_id)
            state_dict = {}
            if state_obj:
                state_dict = {
                    "conversation_id": state_obj.conversation_id,
                    "last_intent": state_obj.last_intent,
                    "last_entities": state_obj.last_entities,
                    "active_fir": bool(state_obj.active_fir),
                    "active_accused": bool(state_obj.active_accused),
                    "active_district": bool(state_obj.active_district)
                }

            # Intent match evaluation
            intent_match = (predicted_intent == turn["expected_intent"])

            turns_results.append({
                "query": query,
                "expected_intent": turn["expected_intent"],
                "predicted_intent": predicted_intent,
                "intent_match": intent_match,
                "expected_entities": turn["expected_entities"],
                "predicted_entities": predicted_entities,
                "expected_context": turn["expected_context"],
                "state": state_dict,
                "sql_route": sql_route,
                "latency_ms": latency_ms,
                "stages_executed": [s.get("stage") for s in stages_executed] if isinstance(stages_executed, list) else [],
                "predicted_reasoning": reasoning_triggered,
                "expected_reasoning_presence": turn["expected_reasoning_presence"],
                "predicted_clarification": predicted_clarification,
                "expected_clarification": turn["expected_clarification"],
                "confidence": confidence,
                "expected_confidence_range": turn["expected_confidence_range"],
                "failed": failed,
                "crashed": crashed,
                "error_message": error_message
            })

        run_results.append({
            "conversation_id": conv_id,
            "turns": turns_results
        })

        if (idx + 1) % 100 == 0:
            print(f"Processed {idx + 1} conversations...")

    # Calculate final accuracy metrics
    metrics = BenchmarkMetrics.calculate_scores(run_results)
    
    current_run_summary = {
        "timestamp": datetime.now().isoformat(),
        "metrics": metrics
    }

    # Save detailed results
    with open(results_path, "w") as f:
        json.dump(run_results, f, indent=2)

    # Handle history and regression detection
    history = []
    if os.path.exists(history_path):
        try:
            with open(history_path, "r") as f:
                history = json.load(f)
        except Exception:
            pass

    comparison = {}
    if history:
        previous_run = history[-1]
        prev_metrics = previous_run.get("metrics", {})
        
        for k, v in metrics.items():
            if k in prev_metrics:
                prev_val = prev_metrics[k]
                if isinstance(v, (int, float)):
                    diff = v - prev_val
                    if k in ["hallucination_rate", "failure_rate", "crash_rate", "avg_latency_ms", "p95_latency_ms", "p99_latency_ms"]:
                        # Lower is better
                        status = "Regressed" if diff > 0.01 else ("Improved" if diff < -0.01 else "Unchanged")
                    else:
                        # Higher is better
                        status = "Improved" if diff > 0.01 else ("Regressed" if diff < -0.01 else "Unchanged")
                    comparison[k] = {
                        "current": v,
                        "previous": prev_val,
                        "diff": diff,
                        "status": status
                    }

    # Append to history and write history file
    history.append(current_run_summary)
    with open(history_path, "w") as f:
        json.dump(history, f, indent=2)

    # Generate Reports via Report Generator
    from tests.benchmark.benchmark_report_generator import generate_reports
    generate_reports(current_run_summary, comparison, history)

    print("=== BENCHMARK COMPLETED SUCCESSFULLY ===")
    return current_run_summary

if __name__ == "__main__":
    run_benchmark()
