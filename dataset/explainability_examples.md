# Explainability Report Examples

This document displays sample structured execution reports for search queries and safety-blocked queries.

## 🟢 Example 1: Clean Search Query
Query: `"Find theft cases in Bengaluru Urban"`

```json
{
  "execution_id": "exec_1719586100000",
  "conversation_id": "default",
  "intent": "SEARCH_CASES",
  "resolved_entities": {
    "crime_category": "THEFT",
    "district": "Bengaluru Urban"
  },
  "query_summary": "User initiated query: 'Find theft cases in Bengaluru Urban'",
  "sql_summary": "The system searched database case records matching crime category 'theft' registered within the Bengaluru Urban Police District.",
  "reasoning_summary": {
    "evidence_used": ["Record 1: KSP-2024-0001", "Record 2: KSP-2024-0002"],
    "reasoning_path": ["Extracted Bengaluru Urban district filters", "Retrieved matched case master entries"],
    "conclusion": "Query processed normally.",
    "alternative_possibilities": [],
    "missing_evidence": [],
    "rejected_paths": []
  },
  "analytics_used": [
    {
      "module": "Pattern",
      "reason": "Triggered to enrich analysis for intent 'SEARCH_CASES'.",
      "detail": "Synthesized temporal patterns."
    }
  ],
  "recommendation_sources": [],
  "confidence_breakdown": {
    "intent_confidence": 0.98,
    "entities_verification": 1.0,
    "database_coverage": 1.0,
    "reasoning_accuracy": 1.0,
    "safety_verification": 1.0,
    "final_score": 0.98
  },
  "hallucination_checks": {
    "checked": true,
    "safe": true,
    "violations_detected": [],
    "action_taken": "None — response is fully evidence-backed."
  },
  "officer_mode": {
    "concise_explanation": [
      "Detected Intent: Search Cases.",
      "Extracted search parameters: crime_category=THEFT, district=Bengaluru Urban.",
      "Successfully matched and retrieved 2 records from the database.",
      "Safety Guard: Response is fully backed by database evidence.",
      "System Confidence: 98.0%."
    ]
  }
}
```

## 🔴 Example 2: Safety-Blocked Query (Zero Evidence)
Query: `"Find accomplice for Raju"` (Where Raju is not in the database)

```json
{
  "execution_id": "exec_1719586200000",
  "conversation_id": "default",
  "intent": "NETWORK_SEARCH",
  "resolved_entities": {
    "accused_name": "Raju"
  },
  "query_summary": "User initiated query: 'Find accomplice for Raju'",
  "sql_summary": "The system searched database suspect profiles associated with accused individual 'Raju'.",
  "reasoning_summary": {
    "evidence_used": [],
    "reasoning_path": ["Attempted to build associate map for Raju"],
    "conclusion": "Insufficient evidence.",
    "alternative_possibilities": [],
    "missing_evidence": ["accused_name"],
    "rejected_paths": []
  },
  "analytics_used": [
    {
      "module": "None",
      "reason": "Direct lookup query did not trigger advanced analytics engines."
    }
  ],
  "recommendation_sources": [],
  "confidence_breakdown": {
    "intent_confidence": 0.95,
    "entities_verification": 1.0,
    "database_coverage": 0.50,
    "reasoning_accuracy": 0.50,
    "safety_verification": 0.0,
    "final_score": 0.0
  },
  "hallucination_checks": {
    "checked": true,
    "safe": false,
    "violations_detected": [
      {
        "category": "names",
        "detail": "Name 'Raju' was asserted in the query but is absent from all DB result rows."
      }
    ],
    "action_taken": "Insufficient evidence."
  },
  "officer_mode": {
    "concise_explanation": [
      "Detected Intent: Network Search.",
      "Extracted search parameters: accused_name=Raju.",
      "No database records matched your search parameters.",
      "Safety Guard: Some unbacked details were suppressed to prevent hallucination.",
      "System Confidence: 0.0%."
    ]
  }
}
```
