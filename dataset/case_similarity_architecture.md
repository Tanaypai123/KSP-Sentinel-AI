# Case Similarity Engine — Architecture

## Overview
The Case Similarity Engine (Phase 5.7) is a deterministic, weighted feature-matching system that finds verified similar investigations and generates priority-ranked recommendations.

## Design Principles
- **Deterministic**: Same input always produces identical output. No randomness, no ML.
- **Explainable**: Every score is the sum of weights for matched features. Every match contains evidence text.
- **Evidence-Only**: Features are extracted exclusively from database-sourced search result rows.
- **No Hallucination**: If no verified match exists above the threshold, outputs "No verified similar investigation found."

## Pipeline Position
```
KnowledgeGraphStage
        ↓
TimelineStage
        ↓
CaseSimilarityStage   ← NEW
        ↓
MultiAgentEngineStage
        ↓
PredictiveEngineStage
        ↓
ConfidenceEngineStage
        ↓
HallucinationGuardStage
        ↓
ExplainabilityEngineStage
        ↓
MemoryEngineStage
        ↓
ResponseGeneratorStage
```

## Component Map
```
CaseSimilarityEngine (main API)
    ├── CaseRecord.from_dict()       → Converts raw DB row to typed record
    ├── SimilarityCalculator.compute()→ Weighted feature comparison
    ├── RecommendationGenerator.generate() → Priority-ranked recommendations
    ├── RecommendationValidator.validate() → Safety & completeness checks
    └── CaseSimilarityStage.run()    → Pipeline wrapper
```

## Data Flow
1. `PipelineRunner` calls `CaseSimilarityStage.run(context)`
2. Stage calls `CaseSimilarityEngine.find_similar_cases(context)`
3. Engine reads `context.search_result` (list of DB row dicts)
4. Each row → `CaseRecord` (verified fields only)
5. First record = **base FIR**; remaining = **candidates**
6. `SimilarityCalculator.compute(base, candidate)` → `SimilarityScore` per candidate
7. Scores sorted descending; filtered by `MINIMUM_THRESHOLD=20`
8. `RecommendationGenerator` + `RecommendationValidator` → `[Recommendation]`
9. `SimilarityReport` assembled and stored in `context.similarity_report`

## Safety Guarantees
- Scores below `MINIMUM_THRESHOLD` → warning "No verified similar investigation found."
- Self-comparisons skipped (candidate.crime_no == base.crime_no)
- Every `Recommendation` must pass `RecommendationValidator` (evidence, FIRs, priority, confidence)
- No external API calls, no ML, no embeddings
