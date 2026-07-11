# Agent Roles and Responsibilities

This document describes the individual specialties, schemas, and outputs of each of the 5 investigation agents.

## 📋 Agent Specifications

### 1. Evidence Agent
- **Responsibility:** Parses search result structures to extract counts of victims, accused, and primary crime heads.
- **Key Output Metric:** `accused_count`, `victim_count`.

### 2. Crime Pattern Agent
- **Responsibility:** Scans temporal crime summaries and geo hotspot locations.
- **Key Output Metric:** `patterns_detected`, `hotspot_count`.

### 3. Network Agent
- **Responsibility:** Translates evidence correlation edges and BFS hop paths into graph summaries.
- **Key Output Metric:** `relational_edges`, `hop_paths`.

### 4. Recommendation Agent
- **Responsibility:** Compiles action suggestions, priorities, and workflow next steps.
- **Key Output Metric:** `recommendation_count`.

### 5. Safety Agent
- **Responsibility:** Monitors hallucination blocks, safety status overrides, and system warning metrics.
- **Key Output Metric:** `safety_status` (SAFE/BLOCKED).
