# Developer Multi-Agent Framework Reference

This document provides developer guidelines and APIs for accessing the Multi-Agent framework.

## ⚙️ Usage API
The multi-agent coordinator executes inside the pipeline Stage wrapper, storing output directly on `context.multi_agent_report`.

```python
from app.ai.multi_agent_engine import AgentCoordinator

# Run coordination across ExecutionContext
report = AgentCoordinator.run_coordination(context)

# Access compiled report sections
evidence = report["evidence_summary"]
patterns = report["crime_pattern"]
recommendations = report["recommendations"]
agreements = report["agent_agreements"]
disagreements = report["agent_disagreements"]
explainability = report["explainability"]
```

## 🛠️ Testing Mock Contexts
To mock agent behaviors:

```python
from app.ai.multi_agent_engine import EvidenceAgent

# Run target agent directly
res = EvidenceAgent.run(context)
print(res.summary, res.findings)
```
