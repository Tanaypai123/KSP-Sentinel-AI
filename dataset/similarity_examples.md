# Similarity Examples

## Example 1: Same Accused — HIGH Similarity

**Base FIR**: FIR-2023-001 | District: Mysuru | Accused: Raju | Vehicle: KA-09-AB-1234 | Crime: Theft

**Candidate FIR**: FIR-2023-045 | District: Mandya | Accused: Raju | Vehicle: KA-09-AB-1234 | Crime: Theft

| Feature | Match? | Score Awarded |
|---------|--------|---------------|
| Crime Type (theft) | ✅ | 30 |
| Accused (Raju) | ✅ | 50 |
| Vehicle (KA-09-AB-1234) | ✅ | 40 |
| District | ❌ | 0 |
| Weapon | ❌ | 0 |
| Phone | ❌ | 0 |

**Raw Score**: 120 / 430  
**Normalized Score**: 28 / 100 → LOW Priority

---

## Example 2: Full Match — HIGH Similarity

**Base FIR**: FIR-2023-100 | Accused: Sanjay | Vehicle: KA-01-CD-5678 | Weapon: Knife | Phone: 9876543210 | District: Bengaluru | Station: Koramangala PS

**Candidate FIR**: FIR-2023-200 | Accused: Sanjay | Vehicle: KA-01-CD-5678 | Weapon: Knife | Phone: 9876543210 | District: Bengaluru | Station: Koramangala PS

| Feature | Match? | Score Awarded |
|---------|--------|---------------|
| Accused | ✅ | 50 |
| Vehicle | ✅ | 40 |
| Weapon | ✅ | 35 |
| Phone | ✅ | 35 |
| Crime Type | ✅ | 30 |
| District | ✅ | 15 |
| Station | ✅ | 10 |

**Raw Score**: 215 / 430  
**Normalized Score**: 50 / 100 → MEDIUM Priority

---

## Example 3: No Match

**Base FIR**: FIR-A | District: Mysuru | Accused: Raju | Weapon: Knife
**Candidate FIR**: FIR-B | District: Kalaburagi | Accused: Mohan | Weapon: Gun

All features differ → Raw Score: 0 → Normalized: 0  
Output: "No verified similar investigation found."

---

## Example 4: Cross-District Same Accused

Two different districts, same accused name:
- District match: ❌ (0 pts)  
- Accused match: ✅ (50 pts)  
- Raw Score: 50 → Normalized: ~12 (below threshold)

If accused also shares vehicle/weapon/phone, score rises above threshold.

---

## SimilarityReport JSON Structure

```json
{
  "base_crime_no": "fir-2023-001",
  "top_similar_firs": [
    {
      "candidate_crime_no": "fir-2023-045",
      "normalized_score": 65,
      "raw_score": 280,
      "matching_features": [
        {
          "feature": "accused",
          "score_awarded": 50,
          "evidence": "Accused match: raju"
        }
      ],
      "differing_features": ["district", "police_station"],
      "warnings": []
    }
  ],
  "recommendations": [
    {
      "recommendation_id": "REC-00001",
      "priority": "HIGH",
      "recommendation_type": "Repeat Offender Detection",
      "description": "Accused in FIR-2023-001 appears in 2 other verified FIRs.",
      "reason": "Same accused names found in multiple FIRs in database.",
      "evidence": ["Accused shared with FIR fir-2023-045"],
      "supporting_firs": ["fir-2023-045"],
      "confidence": 0.95
    }
  ],
  "warnings": [],
  "evidence_chain": [
    "Similarity computed from verified database field values only",
    "Base FIR: fir-2023-001",
    "Candidates evaluated: 2",
    "Valid matches above threshold: 1"
  ]
}
```
