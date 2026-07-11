# Developer Guide — Case Similarity Engine

## Module: `app/ai/case_similarity_engine.py`

### Quick Start

```python
# In a pipeline stage or test script:
from app.ai.case_similarity_engine import CaseSimilarityEngine, CaseSimilarityStage

# Run via stage (standard pipeline)
context = CaseSimilarityStage.run(context)
report_dict = context.similarity_report

# Run directly
report = CaseSimilarityEngine.find_similar_cases(context)
```

---

## Adding a New Feature

1. Add to `CaseFeature` enum:
```python
class CaseFeature(str, Enum):
    MY_NEW_FEATURE = "my_new_feature"
```

2. Add weight in `FEATURE_WEIGHTS`:
```python
CaseFeature.MY_NEW_FEATURE: 25,
```

3. Extract value in `CaseRecord.from_dict()`:
```python
my_field = _as_str(row.get("my_db_column"))
```

4. Add the field to `CaseRecord` dataclass:
```python
my_new_feature: str = ""
```

5. Add comparison logic in `SimilarityCalculator.compute()`:
```python
my_match = bool(base.my_new_feature and candidate.my_new_feature and
                base.my_new_feature == candidate.my_new_feature)
_check(CaseFeature.MY_NEW_FEATURE, my_match,
       base.my_new_feature, candidate.my_new_feature,
       f"My feature match: {base.my_new_feature}" if my_match else "Differs")
```

---

## Changing the Threshold

Edit `MINIMUM_THRESHOLD` in `case_similarity_engine.py`:
```python
MINIMUM_THRESHOLD: int = 25  # Raise to reduce false positives
```

---

## Changing Max Results

```python
MAX_TOP_RESULTS: int = 5  # Reduce to return fewer results
```

---

## Adding a New Recommendation Type

In `RecommendationGenerator.generate()`:
```python
my_firs = [s.candidate_crime_no for s in above_threshold
           if any(m.feature == CaseFeature.MY_NEW_FEATURE for m in s.matching_features)]
if my_firs:
    recs.append(Recommendation(
        recommendation_id=cls._next_rec_id(),
        priority="MEDIUM",
        recommendation_type="My Custom Type",
        description=f"FIR {base.crime_no} matched on my feature.",
        reason="My feature matched across verified records.",
        evidence=[f"My feature: {base.my_new_feature}"],
        supporting_firs=my_firs[:5],
        confidence=0.80,
    ))
```

---

## Testing New Features

```bash
# Run only similarity tests
python3 -m pytest tests/test_case_similarity.py -q

# Run with verbose output
python3 -m pytest tests/test_case_similarity.py -v

# Run specific class
python3 -m pytest tests/test_case_similarity.py::TestSimilarityCalculatorPerfectMatch -v
```

---

## Invariants (Never Break)
- `normalized_score` ∈ [0, 100] always
- `raw_score` ≤ `_MAX_RAW_SCORE` always
- Every `FeatureMatch.score_awarded` equals `FEATURE_WEIGHTS[feature]` (no partial credit)
- `SimilarityReport.top_similar_firs` is always sorted descending
- Candidate FIRs in report always come from input search_result
- All recommendations pass `RecommendationValidator` before inclusion
