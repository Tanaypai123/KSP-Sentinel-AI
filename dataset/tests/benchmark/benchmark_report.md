# AI Performance & Quality Scorecard

* **Generated At:** 2026-07-11T13:06:33.830423
* **Total Conversations Evaluated:** 1400

---

## 🎯 Accuracy & Robustness Scorecard

| Metric | Target | Current Score | Status |
| :--- | :--- | :--- | :--- |
| **Intent Accuracy** | 90%+ | **92.86%** | ✅ Pass |
| **Entity Accuracy** | 85%+ | **69.00%** | ⚠️ Review |
| **Conversation Accuracy** | 85%+ | **76.21%** | ⚠️ Review |
| **Reference Resolution Accuracy** | 85%+ | **21.67%** | ⚠️ Review |
| **Topic Shift Accuracy** | 85%+ | **40.00%** | ⚠️ Review |
| **Clarification Accuracy** | 90%+ | **100.00%** | ✅ Pass |
| **Reasoning Accuracy** | 85%+ | **100.00%** | ✅ Pass |
| **Confidence Accuracy** | 90%+ | **70.36%** | ⚠️ Review |
| **Hallucination Rate** | < 2% | **0.00%** | ✅ Pass |
| **Pipeline Failures** | < 1% | **0.00%** | ✅ Pass |
| **Exception Count** | 0 | **0** | ✅ Pass |

---

## ⚡ Performance & Latency Bounds

* **Average Execution Latency:** **95.70 ms**
* **P95 Execution Latency:** **255.31 ms**
* **P99 Execution Latency:** **1601.83 ms**

---

## 🔄 Regression Summary

| Metric | Previous Run | Current Run | Difference | Status |
| :--- | :--- | :--- | :--- | :--- |
| **total_turns** | 1400.00 | 1400.00 | 0.00 | ⚪ Unchanged |
| **intent_accuracy** | 92.86 | 92.86 | 0.00 | ⚪ Unchanged |
| **entity_accuracy** | 69.00 | 69.00 | 0.00 | ⚪ Unchanged |
| **conversation_accuracy** | 76.21 | 76.21 | 0.00 | ⚪ Unchanged |
| **reference_resolution_accuracy** | 21.67 | 21.67 | 0.00 | ⚪ Unchanged |
| **topic_shift_accuracy** | 40.00 | 40.00 | 0.00 | ⚪ Unchanged |
| **clarification_accuracy** | 100.00 | 100.00 | 0.00 | ⚪ Unchanged |
| **reasoning_accuracy** | 100.00 | 100.00 | 0.00 | ⚪ Unchanged |
| **confidence_accuracy** | 70.36 | 70.36 | 0.00 | ⚪ Unchanged |
| **hallucination_rate** | 0.00 | 0.00 | 0.00 | ⚪ Unchanged |
| **failure_rate** | 0.00 | 0.00 | 0.00 | ⚪ Unchanged |
| **crash_rate** | 0.00 | 0.00 | 0.00 | ⚪ Unchanged |
| **exception_count** | 0.00 | 0.00 | 0.00 | ⚪ Unchanged |
| **avg_latency_ms** | 46.22 | 95.70 | +49.48 | 🔴 REGRESSED |
| **p95_latency_ms** | 118.98 | 255.31 | +136.33 | 🔴 REGRESSED |
| **p99_latency_ms** | 702.80 | 1601.83 | +899.03 | 🔴 REGRESSED |

> [!WARNING]
> **REGRESSION DETECTED!** One or more quality metrics show degraded performance compared to the previous run. Review traces before code merge.
