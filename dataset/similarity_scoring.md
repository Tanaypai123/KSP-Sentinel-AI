# Similarity Scoring Rules

## Feature Weights

| Feature                | Weight | Source Field(s) in DB Row |
|------------------------|--------|---------------------------|
| Same Accused           | 50     | `accused_name`, `accused_names` |
| Same Vehicle           | 40     | `vehicle_no`, `vehicle_nos`, `vehicle_number` |
| Same Weapon            | 35     | `weapon`, `weapons`, `crime_weapon` |
| Same Phone             | 35     | `phone`, `accused_mobile`, `mobile_number` |
| Crime Type             | 30     | `crime_head`, `crime_type`, `crime_category` |
| Crime Pattern          | 30     | `crime_pattern`, `pattern` |
| Knowledge Graph Link   | 25     | `_knowledge_graph_report.nodes[].node_id` |
| Modus Operandi         | 25     | `modus_operandi`, `mo` |
| Timeline Pattern       | 20     | `_timeline_report.events[].event_type` (≥ 2 shared types) |
| Victim                 | 20     | `victim_name`, `victim_names` |
| Gang                   | 20     | `gang_name`, `gang_names` |
| Repeat Offender        | 20     | `repeat_offender`, `is_repeat_offender`, `linked_firs` |
| District               | 15     | `district_name`, `district` |
| Recovery Pattern       | 15     | `recovery_pattern` |
| Investigation Duration | 15     | `_timeline_report.duration_stats[].duration_days` |
| Organization           | 15     | `organization`, `organizations` |
| Hotspot                | 10     | `hotspot`, `hotspot_area` |
| Police Station         | 10     | `police_station_name`, `police_station` |

**Maximum Raw Score** = 430 (sum of all weights)

## Normalization Formula
```
normalized_score = round((raw_score / MAX_RAW_SCORE) * 100)
normalized_score = max(0, min(100, normalized_score))
```

## Matching Logic

| Feature | Match Condition |
|---------|----------------|
| Accused, Victim, Vehicle, Weapon, Phone, Organization, Gang, KG Nodes | Set intersection is non-empty |
| Crime Type, Crime Pattern, MO, Recovery Pattern, Hotspot, District, Station | Exact string equality (lowercased) |
| Timeline Pattern | ≥ 2 shared event_type strings in both lists |
| Repeat Offender | Both records have `repeat_offender == True` |
| Investigation Duration | Both records have duration; difference ≤ 30 days |

## Priority Thresholds

| Priority | Normalized Score |
|----------|-----------------|
| HIGH     | ≥ 70            |
| MEDIUM   | 40–69           |
| LOW      | 20–39           |
| No Match | < 20 → "No verified similar investigation found." |

## Top Results
- Maximum 10 similar FIRs returned per query
- Results sorted descending by normalized_score, then raw_score (tiebreak)
