# KSP Sentinel AI — Enterprise Evaluation Benchmark

This directory houses the permanent, production-grade evaluation benchmark framework for the KSP Sentinel AI query engine. 
It functions as the final quality gate to certify that any code modification maintains intent classification correctness, entity mapping accuracy, context safety, and latency budgets before production deployment.

---

## 🏗️ Architecture & Modules

* **`golden_dataset.json`**: Evaluates the model against 1,000 manually structured conversations spanning 26 unique topics (e.g. spelling errors, Hinglish, follow-ups, topic shifts, clarifications, multi-intent, invalid requests, and edge cases).
* **`benchmark_metrics.py`**: Computes metrics including Intent accuracy, Entity accuracy, Context accuracy, Clarification accuracy, Reasoning match, Confidence bounds check, and Hallucination rates.
* **`benchmark_runner.py`**: Main orchestrator that resets conversation engines, runs sequential turns, traces executing pipeline stages, checks for regressions against historical runs, and saves metrics.
* **`benchmark_report_generator.py`**: Generates visual trend lines in `benchmark_dashboard.html`, saves results in `benchmark_results.json`, updates `benchmark_history.json`, and outputs the `benchmark_report.md` scorecard.

---

## 🚀 Execution Instructions

Execute the benchmark using standard Python:

```bash
PYTHONPATH=. python3 tests/benchmark/benchmark_runner.py
```

### Generated Artifacts
1. **`benchmark_report.md`**: Text-based quality scorecard comparing the current run metrics against the last baseline.
2. **`benchmark_dashboard.html`**: Interactive HTML trend dashboard displaying charts for intent, entity, latency, and hallucination rates over historical executions.
3. **`benchmark_results.json`**: Detailed raw prediction details for debugging and audit.
4. **`benchmark_history.json`**: Database containing history of all benchmark evaluation iterations.

---

## 📈 Quality Gates

A code modification is certified for production deployment *only* if:
1. **Zero regression** is identified in accuracy metrics compared to the baseline.
2. **Crash Rate** is strictly **0.00%**.
3. **Average Latency** is under the target SLA threshold.
