# Agent Conflict Resolution

This document details the deterministic rules used to resolve conflicts when agents report differing finding values.

## ⚖️ Conflict Resolution Priority Rules

```mermaid
graph TD
    Conflict[Conflict Detected] --> Priority1["Rule 1: Higher Evidence Count (Matched fields)"]
    Priority1 --> Tie1{Tie?}
    Tie1 -- No --> Winner1[Winner Selected]
    Tie1 -- Yes --> Priority2["Rule 2: Higher Confidence Score"]
    Priority2 --> Tie2{Tie?}
    Tie2 -- No --> Winner2[Winner Selected]
    Tie2 -- Yes --> Priority3["Rule 3: More supporting FIR IDs"]
    Priority3 --> Tie3{Tie?}
    Tie3 -- No --> Winner3[Winner Selected]
    Tie3 -- Yes --> Unresolved[Mark 'CONFLICT' - Never Fabricate Consensus]
```

## 📋 Conflict Logging Examples
- **Example 1 (Resolved):** `Conflict on key 'accused_count' resolved in favor of evidence_agent value '4' (Rules applied).`
- **Example 2 (Unresolved):** `Conflict on key 'active_parameter' between reporting agents (Tied on all priorities).`
