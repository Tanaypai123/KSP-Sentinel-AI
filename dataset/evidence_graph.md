# Evidence Graph Schema

This document details the node types, edge properties, and schemas of the `EvidenceGraph` produced by the correlation engine.

## 🟢 Node Schema
Nodes represent either database records or extracted entities:
- **FIR Nodes:** `id: "FIR:{crime_no}"`, attributes: `district`, `station`, `category`, `date`.
- **Accused Nodes:** `id: "Accused:{name}"`, label: suspect name.
- **Victim Nodes:** `id: "Victim:{name}"`, label: victim name.
- **Vehicle Nodes:** `id: "Vehicle:{number}"`, label: vehicle license number.
- **Weapon Nodes:** `id: "Weapon:{type}"`, label: weapon type description.
- **Phone Nodes:** `id: "Phone:{number}"`, label: phone number.

## 🔴 Edge Schema
Edges represent verified connections between nodes:
- `source`: Node ID.
- `target`: Node ID.
- `relationship_type`: "Accused Correlation", "Vehicle Correlation", "Phone Correlation", "Weapon Correlation", "Victim Correlation", "Location/Pattern Correlation", or direct link names.
- `strength`: `WEAK`, `MEDIUM`, `STRONG`, `VERY_STRONG`.
- `confidence`: float (0.0 to 1.0).
- `evidence_score`: integer (0 to 100).
- `source_firs`: List of crime numbers supporting this connection.
- `matching_fields`: List of matching properties (e.g. `["district", "police_station", "vehicle"]`).
- `details`: Plain text explanation of the link connection.
