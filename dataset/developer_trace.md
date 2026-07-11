# Developer Explainability Trace Reference

This document describes the structure and profiling details of **Developer Mode** within the Explainability Engine.

## 🎯 Purpose
Equip enterprise developers and AI architects with detailed profiling metadata of the internal execution stages, latencies, and SQL representations for diagnostic purposes.

## 📋 Developer Mode Metrics
1. **Modules:** List of pipeline stages executed.
2. **Latency (ms):** Detailed execution time per stage (e.g. `SearchServiceStage`, `IntelligenceEngineStage`).
3. **Execution Order:** Linear list of executed stages.
4. **SQL Query String:** The exact SQL query prepared by SQLAlchemy (excluding developer mode filters, raw text formatting).
5. **Decision Path:** The dynamic agenda items inside `plan`.
