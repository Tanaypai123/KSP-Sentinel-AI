# Evidence Correlation Examples

This document displays examples of multi-hop paths, offender clusters, and gang activity groups discovered by the Evidence Correlation Engine.

## 🟢 Example 1: Multi-Hop Connection Chain
Discovery path: `Accused Raju -> Vehicle KA-09-1234 -> Associate Ganesh -> FIR KSP-2024-005`

```json
{
  "type": "3-Hop Connection",
  "path": [
    "Accused:raju",
    "Vehicle:ka-09-1234",
    "Victim:ganesh",
    "FIR:KSP-2024-0005"
  ],
  "summary": "Accused Raju -> Vehicle KA-09-1234 -> Victim Ganesh -> FIR KSP-2024-0005"
}
```

## 🔴 Example 2: Crime Clusters and Repeat Offenders
Offender cluster tracking repeat suspect groups:

```json
{
  "repeat_offenders": ["Raju", "Ganesh"],
  "crime_clusters": [
    ["FIR:KSP-2024-0001", "FIR:KSP-2024-0002"]
  ],
  "gang_activity": []
}
```
