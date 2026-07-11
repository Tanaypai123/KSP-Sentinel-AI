import os
import json

def generate_reports(current_run, comparison, history):
    benchmark_dir = os.path.dirname(__file__)
    md_report_path = os.path.join(benchmark_dir, "benchmark_report.md")
    html_dashboard_path = os.path.join(benchmark_dir, "benchmark_dashboard.html")

    metrics = current_run["metrics"]
    ts = current_run["timestamp"]

    # 1. Generate Markdown Report
    md_content = f"""# AI Performance & Quality Scorecard

* **Generated At:** {ts}
* **Total Conversations Evaluated:** {metrics['total_turns']}

---

## 🎯 Accuracy & Robustness Scorecard

| Metric | Target | Current Score | Status |
| :--- | :--- | :--- | :--- |
| **Intent Accuracy** | 90%+ | **{metrics['intent_accuracy']:.2f}%** | {"✅ Pass" if metrics['intent_accuracy'] >= 90.0 else "⚠️ Review"} |
| **Entity Accuracy** | 85%+ | **{metrics['entity_accuracy']:.2f}%** | {"✅ Pass" if metrics['entity_accuracy'] >= 85.0 else "⚠️ Review"} |
| **Conversation Accuracy** | 85%+ | **{metrics['conversation_accuracy']:.2f}%** | {"✅ Pass" if metrics['conversation_accuracy'] >= 85.0 else "⚠️ Review"} |
| **Reference Resolution Accuracy** | 85%+ | **{metrics['reference_resolution_accuracy']:.2f}%** | {"✅ Pass" if metrics['reference_resolution_accuracy'] >= 85.0 else "⚠️ Review"} |
| **Topic Shift Accuracy** | 85%+ | **{metrics['topic_shift_accuracy']:.2f}%** | {"✅ Pass" if metrics['topic_shift_accuracy'] >= 85.0 else "⚠️ Review"} |
| **Clarification Accuracy** | 90%+ | **{metrics['clarification_accuracy']:.2f}%** | {"✅ Pass" if metrics['clarification_accuracy'] >= 90.0 else "⚠️ Review"} |
| **Reasoning Accuracy** | 85%+ | **{metrics['reasoning_accuracy']:.2f}%** | {"✅ Pass" if metrics['reasoning_accuracy'] >= 85.0 else "⚠️ Review"} |
| **Confidence Accuracy** | 90%+ | **{metrics['confidence_accuracy']:.2f}%** | {"✅ Pass" if metrics['confidence_accuracy'] >= 90.0 else "⚠️ Review"} |
| **Hallucination Rate** | < 2% | **{metrics['hallucination_rate']:.2f}%** | {"✅ Pass" if metrics['hallucination_rate'] < 2.0 else "❌ High"} |
| **Pipeline Failures** | < 1% | **{metrics['failure_rate']:.2f}%** | {"✅ Pass" if metrics['failure_rate'] < 1.0 else "❌ Critical"} |
| **Exception Count** | 0 | **{metrics['exception_count']}** | {"✅ Pass" if metrics['exception_count'] == 0 else "❌ FAILED"} |

---

## ⚡ Performance & Latency Bounds

* **Average Execution Latency:** **{metrics['avg_latency_ms']:.2f} ms**
* **P95 Execution Latency:** **{metrics['p95_latency_ms']:.2f} ms**
* **P99 Execution Latency:** **{metrics['p99_latency_ms']:.2f} ms**

---

## 🔄 Regression Summary
"""

    if not comparison:
        md_content += "\n> [!NOTE]\n> This is the initial benchmark baseline. No previous history is available for comparison.\n"
    else:
        md_content += "\n| Metric | Previous Run | Current Run | Difference | Status |\n| :--- | :--- | :--- | :--- | :--- |\n"
        has_regression = False
        for k, v in comparison.items():
            diff_str = f"+{v['diff']:.2f}" if v['diff'] > 0 else f"{v['diff']:.2f}"
            status_icon = "🟢 Improved" if v['status'] == "Improved" else ("🔴 REGRESSED" if v['status'] == "Regressed" else "⚪ Unchanged")
            if v['status'] == "Regressed":
                has_regression = True
            md_content += f"| **{k}** | {v['previous']:.2f} | {v['current']:.2f} | {diff_str} | {status_icon} |\n"
        
        if has_regression:
            md_content += "\n> [!WARNING]\n> **REGRESSION DETECTED!** One or more quality metrics show degraded performance compared to the previous run. Review traces before code merge.\n"
        else:
            md_content += "\n> [!TIP]\n> **QUALITY GATE PASSED:** No regressions detected compared to the previous evaluation baseline.\n"

    with open(md_report_path, "w") as f:
        f.write(md_content)

    # 2. Generate HTML Dashboard (Self-contained, Dark Mode Theme)
    history_labels = [h["timestamp"][:16].replace("T", " ") for h in history[-10:]]
    history_intent_acc = [h["metrics"]["intent_accuracy"] for h in history[-10:]]
    history_entity_acc = [h["metrics"]["entity_accuracy"] for h in history[-10:]]
    history_conv_acc = [h["metrics"]["conversation_accuracy"] for h in history[-10:]]
    history_avg_lat = [h["metrics"]["avg_latency_ms"] for h in history[-10:]]
    history_hallucination = [h["metrics"]["hallucination_rate"] for h in history[-10:]]

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sentinel AI — Quality Evaluation Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            background-color: #0d1117;
            color: #c9d1d9;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 24px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{
            color: #58a6ff;
            border-bottom: 1px solid #21262d;
            padding-bottom: 12px;
            margin-bottom: 24px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 32px;
        }}
        .card {{
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 16px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .card-title {{
            font-size: 13px;
            color: #8b949e;
            margin-bottom: 6px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .card-value {{
            font-size: 28px;
            font-weight: bold;
            color: #f0f6fc;
        }}
        .card-value.pass {{ color: #3fb950; }}
        .card-value.fail {{ color: #f85149; }}
        .card-value.warn {{ color: #d29922; }}
        .chart-container {{
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 32px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Sentinel AI — Quality Evaluation Dashboard</h1>
        <p style="color: #8b949e; margin-top: -12px; margin-bottom: 24px;">Latest Run Timestamp: {ts}</p>
        
        <div class="grid">
            <div class="card">
                <div class="card-title">Intent Accuracy</div>
                <div class="card-value pass">{metrics['intent_accuracy']:.2f}%</div>
            </div>
            <div class="card">
                <div class="card-title">Entity Accuracy</div>
                <div class="card-value pass">{metrics['entity_accuracy']:.2f}%</div>
            </div>
            <div class="card">
                <div class="card-title">Conversation Accuracy</div>
                <div class="card-value pass">{metrics['conversation_accuracy']:.2f}%</div>
            </div>
            <div class="card">
                <div class="card-title">Average Latency</div>
                <div class="card-value warn">{metrics['avg_latency_ms']:.1f} ms</div>
            </div>
            <div class="card">
                <div class="card-title">Hallucination Rate</div>
                <div class="card-value pass">{metrics['hallucination_rate']:.2f}%</div>
            </div>
        </div>

        <div class="chart-container">
            <h3 style="margin-top: 0; color: #f0f6fc;">Accuracy Trends</h3>
            <canvas id="accuracyChart" height="100"></canvas>
        </div>

        <div class="chart-container">
            <h3 style="margin-top: 0; color: #f0f6fc;">Latency & Hallucination Trends</h3>
            <canvas id="latencyChart" height="100"></canvas>
        </div>
    </div>

    <script>
        const labels = {json.dumps(history_labels)};
        
        new Chart(document.getElementById('accuracyChart'), {{
            type: 'line',
            data: {{
                labels: labels,
                datasets: [
                    {{
                        label: 'Intent Accuracy %',
                        data: {json.dumps(history_intent_acc)},
                        borderColor: '#58a6ff',
                        backgroundColor: 'rgba(88, 166, 255, 0.1)',
                        tension: 0.2,
                        fill: true
                    }},
                    {{
                        label: 'Entity Accuracy %',
                        data: {json.dumps(history_entity_acc)},
                        borderColor: '#3fb950',
                        backgroundColor: 'rgba(63, 185, 80, 0.1)',
                        tension: 0.2,
                        fill: true
                    }},
                    {{
                        label: 'Conversation Accuracy %',
                        data: {json.dumps(history_conv_acc)},
                        borderColor: '#d29922',
                        backgroundColor: 'rgba(210, 153, 34, 0.1)',
                        tension: 0.2,
                        fill: true
                    }}
                ]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ labels: {{ color: '#c9d1d9' }} }}
                }},
                scales: {{
                    y: {{ grid: {{ color: '#30363d' }}, ticks: {{ color: '#c9d1d9' }} }},
                    x: {{ grid: {{ color: '#30363d' }}, ticks: {{ color: '#c9d1d9' }} }}
                }}
            }}
        }});

        new Chart(document.getElementById('latencyChart'), {{
            type: 'line',
            data: {{
                labels: labels,
                datasets: [
                    {{
                        label: 'Avg Latency (ms)',
                        data: {json.dumps(history_avg_lat)},
                        borderColor: '#a371f7',
                        tension: 0.2,
                        yAxisID: 'y'
                    }},
                    {{
                        label: 'Hallucination Rate %',
                        data: {json.dumps(history_hallucination)},
                        borderColor: '#f85149',
                        tension: 0.2,
                        yAxisID: 'y1'
                    }}
                ]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ labels: {{ color: '#c9d1d9' }} }}
                }},
                scales: {{
                    y: {{ 
                        type: 'linear', 
                        position: 'left',
                        grid: {{ color: '#30363d' }}, 
                        ticks: {{ color: '#c9d1d9' }} 
                    }},
                    y1: {{ 
                        type: 'linear', 
                        position: 'right',
                        grid: {{ drawOnChartArea: false }}, 
                        ticks: {{ color: '#c9d1d9' }} 
                    }},
                    x: {{ grid: {{ color: '#30363d' }}, ticks: {{ color: '#c9d1d9' }} }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""

    with open(html_dashboard_path, "w") as f:
        f.write(html_content)

    print(f"Generated benchmark_report.md and benchmark_dashboard.html successfully.")
