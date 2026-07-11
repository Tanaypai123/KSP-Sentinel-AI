# Agent Coordination and Orchestration

This document describes the orchestration loops and collection processes managed by the `AgentCoordinator`.

## 🔄 Coordination Execution Flow
The coordination flow follows a strictly deterministic pattern:
1. **Parallel Execution:** The coordinator triggers the `run()` class method of each agent on the provided `ExecutionContext`.
2. **Collection Loop:** The coordinator gathers `AgentResult` packages.
3. **Key Aggregation:** It identifies all key variables reported across the agents' `findings` maps.
4. **Agreement Extraction:** For each key, if all reporting agents match values, the finding is added to `agent_agreements`.
5. **Conflict Resolution:** If there are disagreeing values, it invokes the deterministic conflict resolver to find a winner or logs a tie-break block.
6. **Unified Report Compilation:** Compiles the merged result payload.
