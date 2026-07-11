# Evidence Correlation Scoring Guidelines

This document details the scoring weight criteria, matching formulas, and strength bands.

## ⚖️ Scoring Formula
The correlation engine assigns points to linkages based on overlap attributes:

| Match Category | Points | Description |
| :--- | :--- | :--- |
| **District Overlap** | +15 | Matching police district boundary. |
| **Station Overlap** | +15 | Matching police station boundary. |
| **Crime Head Overlap** | +15 | Overlap in major crime category code. |
| **Date Proximity** | +20 | Crime registration date within 30 days of each other. |
| **Geo Proximity** | +20 | Overlapping GPS coordinates. |
| **Accused Overlap** | +30 | Suspect name match. |
| **Victim Overlap** | +30 | Victim name match. |
| **Vehicle Overlap** | +30 | Vehicle license plate number match. |
| **Phone Overlap** | +30 | Mobile phone number match. |
| **Weapon Overlap** | +30 | Weapon description match. |

## 📊 Strength Bands
Points are summed and capped between 0 and 100:
- **VERY_STRONG:** Score $\ge 80$.
- **STRONG:** Score $\ge 60$.
- **MEDIUM:** Score $\ge 40$.
- **WEAK:** Score $< 40$.
