# Memory Audit Trail Reference

This document outlines the change tracking standards of the **MemoryAudit** layer.

## 🎯 Compliance Requirements
For legal defensibility and administrative compliance:
1. **Delta-Only Logging:** Only record field changes where the old value differs from the new value.
2. **Attribution:** Document the justification/reason for the change (e.g. `Updated active district based on query search result`).
3. **Immutability:** Once written to `cls._audits`, audit trails cannot be altered or overwritten.

## 🗃️ Audit Trail Structure
Each log entry contains:
- `version`: Monotonically incrementing integer.
- `timestamp`: Epoch seconds.
- `changes`: List of dicts specifying `field`, `old_value`, `new_value`, and `reason`.
- `summary`: Human-readable version changes sentence.
