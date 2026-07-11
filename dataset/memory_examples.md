# Memory State Examples

This document displays examples of structured memory payloads and audit logs.

## 🟢 Example 1: Active Memory State
Below is an example of an `InvestigationMemory` instance:

```json
{
  "conversation_id": "default",
  "active_fir": {
    "crime_no": "KSP-2024-0001",
    "district_name": "Mysuru",
    "accused_name": "Raju"
  },
  "active_accused": {
    "accused_name": "Raju"
  },
  "active_victim": {
    "victim_name": "Ganesh"
  },
  "active_station": {
    "police_station": "Hubli"
  },
  "active_district": {
    "district": "Dharwad"
  },
  "timestamps": {
    "created_time": 1719586100.0,
    "last_updated_time": 1719586150.0,
    "version": 2
  }
}
```

## 🔴 Example 2: Memory Audit Trail Record
Below is an example of a `MemoryAudit` change log:

```json
{
  "version": 2,
  "timestamp": 1719586150.0,
  "changes": [
    {
      "field": "active_fir",
      "old_value": null,
      "new_value": {
        "crime_no": "KSP-2024-0001",
        "district_name": "Mysuru",
        "accused_name": "Raju"
      },
      "reason": "Updated active FIR record based on query search result."
    },
    {
      "field": "active_accused",
      "old_value": null,
      "new_value": {
        "accused_name": "Raju"
      },
      "reason": "Updated accused based on search query."
    }
  ],
  "summary": "Version 2 changes: active_fir updated, active_accused updated"
}
```
