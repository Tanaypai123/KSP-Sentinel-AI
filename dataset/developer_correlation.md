# Developer Evidence Correlation Reference

This document provides developer instructions and APIs for accessing the Evidence Correlation Engine.

## ⚙️ Usage API
The correlation engine is called automatically within the stage loop. It stores results directly on `context.evidence_correlation`.

```python
from app.ai.evidence_correlation_engine import EvidenceCorrelationEngine

# Correlate matches inside ExecutionContext
correlation_report = EvidenceCorrelationEngine.correlate(context)

# Access compiled graph nodes/edges
nodes = correlation_report["nodes"]
edges = correlation_report["edges"]
chains = correlation_report["chains"]
clusters = correlation_report["clusters"]
```

## 🛡️ Minimum Match Constraints
If `len(context.search_result) < 2` or if zero links exceed the threshold (`MIN_THRESHOLD = 15`), the engine returns:

```json
{
  "nodes": [],
  "edges": [],
  "chains": [],
  "clusters": [],
  "summary": "No verified evidence connecting these records."
}
```
