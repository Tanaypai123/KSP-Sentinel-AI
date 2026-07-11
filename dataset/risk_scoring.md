# Predictive Risk Scoring Reference

This document defines the deterministic scoring rules, classifications, and thresholds for repeat offender risks and crime escalation.

## 📊 Repeat Offender Risk Matrix

| Offense Count | Recurrence Interval | Risk Grade | Risk Score |
| :--- | :--- | :--- | :--- |
| **1 Case** | N/A | **LOW** | 10 |
| **2 Cases** | > 30 Days | **MEDIUM** | 45 |
| **2 Cases** | $\le$ 30 Days | **CRITICAL** | 95 |
| **3 Cases** | N/A | **HIGH** | 75 |
| **$\ge$ 4 Cases** | N/A | **CRITICAL** | 95 |

## ⚖️ Crime Escalation Indicators
Crime escalation flags are triggered when a suspect sequential record displays:
- **Increasing Gravity Indexes:** Moving from minor offenses (e.g. `THEFT`, index 1) to major violent offenses (e.g. `ROBBERY`, index 2, or `MURDER`, index 3).
- Escalation overrides score to **85 (HIGH)**.
