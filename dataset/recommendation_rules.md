# Recommendation Rules

## Recommendation Types

| Type | Trigger Condition | Default Priority |
|------|-------------------|-----------------|
| Similar FIRs | Any score ≥ threshold | Score-derived |
| Repeat Offender Detection | ACCUSED feature matched | HIGH |
| Common Vehicles | VEHICLE feature matched | Score-derived |
| Common Weapons | WEAPON feature matched | Score-derived |
| Common Phones | PHONE feature matched | HIGH |
| Common Districts | DISTRICT feature matched | MEDIUM |
| Common Stations | POLICE_STATION feature matched | LOW |
| Related Hotspots | HOTSPOT feature matched | MEDIUM |
| Likely Associated FIRs | KNOWLEDGE_GRAPH_LINK matched | Score-derived |
| Investigation Priority | Any valid matches exist | Score-derived |

## Priority Derivation Logic
```python
def _priority(normalized_score: int) -> str:
    if normalized_score >= 70: return "HIGH"
    if normalized_score >= 40: return "MEDIUM"
    return "LOW"
```

## Validation Rules (RecommendationValidator)
A recommendation is accepted only if ALL of the following are satisfied:
1. `recommendation_id` is non-empty
2. `priority` ∈ {"HIGH", "MEDIUM", "LOW"}
3. `description` is non-empty
4. `reason` is non-empty
5. `evidence` list is non-empty (at least one verified evidence string)
6. `supporting_firs` list is non-empty (at least one verified FIR number)
7. `0.0 ≤ confidence ≤ 1.0`

Any recommendation that fails validation is dropped and a warning is added to the report.

## Safety Rules
- Never fabricate FIR numbers — all supporting FIRs must be from input search_result rows
- Never create a recommendation if no candidates exceed MINIMUM_THRESHOLD
- Every evidence string must describe an actual match, not an assumed one
- Confidence is always numeric, never string-based
