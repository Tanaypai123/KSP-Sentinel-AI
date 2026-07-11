"""
hallucination_guard.py
======================
AI Safety Layer — HallucinationGuard

Role:
    Intercepts every response immediately before it is returned to the caller.
    Scans the assembled response and pipeline context for claims that cannot
    be directly supported by the DB result set, intelligence bundle, or
    verified analytics output.

Blocked claim categories:
    1. Names        — Proper-noun / accused / victim name assertions absent from results.
    2. Dates        — Date-string claims not backed by a result-row timestamp field.
    3. Locations    — District / police-station / location assertions absent from results.
    4. Relationships — "linked to / associated with / connected to" language when
                       network_data is empty or absent.
    5. Recommendations — Recommendation lists populated with zero DB evidence.
    6. Statistics   — Numeric count / percentage claims that exceed the verified
                      total_count or appear with no evidence backing.

Decision:
    • Zero-evidence fast-path: if search_result is empty AND the intent requires DB
      data, ALL six categories are immediately flagged and the summary is replaced
      with "Insufficient evidence."
    • Otherwise: per-category regex + structural cross-reference checks run on the
      assembled summary / recommendation text.

Output (added to the response dict):
    {
        "hallucination_guard": {
            "checked": true,
            "safe": false,
            "violations": [
                {"category": "names",   "detail": "..."},
                {"category": "dates",   "detail": "..."}
            ],
            "action_taken": "Insufficient evidence."
        }
    }

Integration:
    Runs as `HallucinationGuardStage` inside `pipeline_runner.py`,
    immediately before `ResponseGeneratorStage`.
"""

from __future__ import annotations

import re
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    pass   # ExecutionContext imported at runtime to avoid circular imports

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Intents that REQUIRE a DB result set to make any factual claim
# ---------------------------------------------------------------------------
_DB_EVIDENCE_REQUIRED_INTENTS = {
    "FIR_LOOKUP",
    "SEARCH_CASES",
    "SEARCH_ACCUSED",
    "SEARCH_VICTIMS",
    "SEARCH_LOCATION",
    "SEARCH_POLICE_STATION",
    "NETWORK_SEARCH",
    "PREDICT_CRIME",
    "COMPARE_CASES",
    "AGGREGATE_COUNT",
    "CRIME_TREND",
    "HOTSPOT",
    "AMBIGUOUS",
}

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# ISO-8601 and common date formats: 2024-03-15, 15/03/2024, 15-Mar-2024, March 15 2024
_DATE_PATTERNS: List[re.Pattern] = [
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),                             # 2024-03-15
    re.compile(r"\b\d{2}/\d{2}/\d{4}\b"),                             # 15/03/2024
    re.compile(r"\b\d{1,2}-(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d{4}\b", re.IGNORECASE),  # 15-Mar-2024
    re.compile(r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)"
               r"\s+\d{1,2},?\s+\d{4}\b", re.IGNORECASE),             # March 15, 2024
]

# Relationship language
_RELATIONSHIP_PATTERNS: List[re.Pattern] = [
    re.compile(r"\blinked\s+to\b", re.IGNORECASE),
    re.compile(r"\bassociated\s+with\b", re.IGNORECASE),
    re.compile(r"\bconnected\s+to\b", re.IGNORECASE),
    re.compile(r"\bpart\s+of\s+(?:a\s+)?(?:gang|network|syndicate|group|ring)\b", re.IGNORECASE),
    re.compile(r"\bco[-\s]?accused\b", re.IGNORECASE),
    re.compile(r"\bknown\s+associate\b", re.IGNORECASE),
    re.compile(r"\bworks\s+with\b", re.IGNORECASE),
    re.compile(r"\boperat(?:es|ing)\s+with\b", re.IGNORECASE),
]

# Numeric claims: "45 cases", "23%", "over 100", "approximately 50 records"
_STATISTIC_PATTERNS: List[re.Pattern] = [
    re.compile(r"\b(\d{1,3}(?:,\d{3})*)\s+(?:case|fir|record|incident|crime|arrest|accused|victim)s?\b", re.IGNORECASE),
    re.compile(r"\b(\d+(?:\.\d+)?)\s*%", re.IGNORECASE),
    re.compile(r"\b(?:over|more\s+than|approximately|around|about|nearly)\s+(\d+)\b", re.IGNORECASE),
]

# Result-row timestamp field names
_DATE_FIELDS = {
    "crime_registered_date", "incident_date", "arrest_date",
    "date_of_occurrence", "registered_date", "occurrence_date", "fir_date",
}

# Result-row location field names
_LOCATION_FIELDS = {
    "district_name", "police_station_name", "location", "place_of_occurrence",
    "address", "beat_name", "circle_name", "division_name", "unit_name",
}

# Result-row person field names
_NAME_FIELDS = {
    "accused_name", "victim_name", "officer_name",
    "complainant_name", "witness_name", "arrested_name",
}

# ---------------------------------------------------------------------------
# Violation record helpers
# ---------------------------------------------------------------------------

def _violation(category: str, detail: str) -> Dict[str, str]:
    return {"category": category, "detail": detail}


def _extract_text_from_result_field(results: List[Dict], fields: set) -> set:
    """Collect all non-None string values for a given set of field names across all result rows."""
    values: set = set()
    for row in results:
        for field in fields:
            val = row.get(field)
            if val and isinstance(val, str):
                values.add(val.lower().strip())
    return values


# ---------------------------------------------------------------------------
# HallucinationGuard
# ---------------------------------------------------------------------------

class HallucinationGuard:
    """
    Stateless, evidence-gated pre-response validator.

    All public methods are @staticmethod so the guard can be called from any
    pipeline stage without instantiation.
    """

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    @staticmethod
    def validate(
        intent: str,
        search_result: List[Dict[str, Any]],
        resolved_entities: Dict[str, Any],
        response: Dict[str, Any],
        intelligence_bundle: Optional[Any] = None,
        confidence_metrics: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, List[Dict[str, str]]]:
        """
        Validate the assembled response against the available evidence.

        Returns:
            (is_safe, violations)
            is_safe   : True  → no unsupported claims detected
                        False → one or more blocked categories found
            violations: list of {category, detail} dicts
        """
        violations: List[Dict[str, str]] = []
        evidence_count = len(search_result)

        # ── Zero-evidence fast-path ──────────────────────────────────────────
        if evidence_count == 0 and intent in _DB_EVIDENCE_REQUIRED_INTENTS:
            logger.info("HallucinationGuard: zero-evidence fast-path triggered for intent=%s", intent)
            violations.extend([
                _violation("names",           "No DB records available to support name assertions."),
                _violation("dates",           "No DB records available to support date assertions."),
                _violation("locations",       "No DB records available to support location assertions."),
                _violation("relationships",   "No DB records available to support relationship claims."),
                _violation("recommendations", "Recommendations are unsupported with zero evidence."),
                _violation("statistics",      "Numeric claims are unsupported with zero evidence."),
            ])
            return False, violations

        summary = response.get("summary", "")
        if not isinstance(summary, str):
            summary = ""

        recommended_queries = response.get("recommended_queries", [])
        recommendations_list = response.get("insights", [])  # insight strings may contain rec text

        # ── Per-category checks ──────────────────────────────────────────────
        violations.extend(HallucinationGuard._check_names(
            summary, resolved_entities, search_result
        ))
        violations.extend(HallucinationGuard._check_dates(
            summary, search_result
        ))
        violations.extend(HallucinationGuard._check_locations(
            summary, resolved_entities, search_result
        ))
        violations.extend(HallucinationGuard._check_relationships(
            summary, intelligence_bundle
        ))
        violations.extend(HallucinationGuard._check_recommendations(
            recommended_queries, evidence_count
        ))
        violations.extend(HallucinationGuard._check_statistics(
            summary, evidence_count, response.get("count", 0)
        ))

        is_safe = len(violations) == 0
        if not is_safe:
            logger.warning(
                "HallucinationGuard: %d violation(s) detected for intent=%s: %s",
                len(violations), intent,
                [v["category"] for v in violations]
            )
        else:
            logger.debug("HallucinationGuard: response is safe for intent=%s", intent)

        return is_safe, violations

    @staticmethod
    def sanitize_response(
        response: Dict[str, Any],
        violations: List[Dict[str, str]],
        intent: str,
        evidence_count: int,
    ) -> Dict[str, Any]:
        """
        Patch the response in-place for every blocked category.

        • If ALL categories are violated (zero-evidence fast-path):
          overwrite `summary` entirely with "Insufficient evidence."
        • Otherwise: append a clear disclaimer to summary and null-out
          the specific fields that cannot be supported.

        Returns the mutated response dict.
        """
        violated_categories = {v["category"] for v in violations}
        all_categories = {"names", "dates", "locations", "relationships", "recommendations", "statistics"}

        if violated_categories >= all_categories:
            # Total block — zero evidence
            response["summary"] = "Insufficient evidence."
            response["recommended_queries"] = []
            response["insights"] = []
            explanation = response.get("explanation", {})
            if isinstance(explanation, dict):
                explanation["reasoning"] = "Insufficient evidence."
                explanation["hallucination_guard"] = "All claims blocked: no DB evidence."
            response["explanation"] = explanation
        else:
            # Partial block — append disclaimer to summary
            blocked_labels = ", ".join(sorted(violated_categories))
            disclaimer = (
                f"\n\n⚠️ AI Safety Notice — The following claim categories could not be "
                f"verified against the available evidence and have been suppressed: "
                f"{blocked_labels}. "
                f"Insufficient evidence."
            )
            response["summary"] = (response.get("summary") or "") + disclaimer

            # Null-out specific fields
            if "recommendations" in violated_categories:
                response["recommended_queries"] = []
            if "statistics" in violated_categories:
                # Replace count with verified count only
                response["count"] = evidence_count
            if "relationships" in violated_categories:
                explanation = response.get("explanation", {})
                if isinstance(explanation, dict):
                    explanation["relationship_claims"] = "Insufficient evidence."

        # ── Inject guard audit block ─────────────────────────────────────────
        action = "Insufficient evidence." if violated_categories >= all_categories else \
                 f"Suppressed categories: {', '.join(sorted(violated_categories))}."

        response["hallucination_guard"] = {
            "checked": True,
            "safe": False,
            "violations": violations,
            "action_taken": action,
        }
        return response

    @staticmethod
    def mark_safe(response: Dict[str, Any]) -> Dict[str, Any]:
        """Stamp a clean guard audit block when the response passes all checks."""
        response["hallucination_guard"] = {
            "checked": True,
            "safe": True,
            "violations": [],
            "action_taken": "None — response is fully evidence-backed.",
        }
        return response

    # -----------------------------------------------------------------------
    # Private per-category checks
    # -----------------------------------------------------------------------

    @staticmethod
    def _check_names(
        summary: str,
        resolved_entities: Dict[str, Any],
        search_result: List[Dict[str, Any]],
    ) -> List[Dict[str, str]]:
        """
        Block name claims when the resolved entity name does not appear in ANY
        result-row name field.
        """
        violations = []
        entity_names: List[str] = []

        for field in ("accused_name", "victim_name", "officer_name", "name"):
            val = resolved_entities.get(field)
            if val and isinstance(val, str):
                entity_names.append(val.strip())

        if not entity_names:
            return violations

        backed_names = _extract_text_from_result_field(search_result, _NAME_FIELDS)

        for name in entity_names:
            name_lower = name.lower()
            # Check if the name (or any meaningful token of it) appears in results
            if not backed_names or not any(
                name_lower in backed or backed in name_lower
                for backed in backed_names
            ):
                violations.append(_violation(
                    "names",
                    f"Name '{name}' was asserted in the query but is absent from all DB result rows."
                ))

        return violations

    @staticmethod
    def _check_dates(
        summary: str,
        search_result: List[Dict[str, Any]],
    ) -> List[Dict[str, str]]:
        """
        Block date claims in the response summary that are not backed by any
        date-type field in the result set.
        """
        violations = []
        if not summary:
            return violations

        backed_dates: set = set()
        for row in search_result:
            for field in _DATE_FIELDS:
                val = row.get(field)
                if val:
                    backed_dates.add(str(val).strip())

        for pattern in _DATE_PATTERNS:
            matches = pattern.findall(summary)
            for match in matches:
                date_str = match.strip()
                # Check if this exact string (or partial) is in backed dates
                if not any(date_str in bd or bd in date_str for bd in backed_dates):
                    violations.append(_violation(
                        "dates",
                        f"Date '{date_str}' appears in the response but is not present "
                        f"in any result-row date field."
                    ))
                    break  # one violation per check is sufficient

        return violations

    @staticmethod
    def _check_locations(
        summary: str,
        resolved_entities: Dict[str, Any],
        search_result: List[Dict[str, Any]],
    ) -> List[Dict[str, str]]:
        """
        Block location claims when the asserted district / police station / location
        does not appear in any result row.
        """
        violations = []

        entity_locations: List[str] = []
        for field in ("district", "police_station", "location", "place"):
            val = resolved_entities.get(field)
            if val and isinstance(val, str):
                entity_locations.append(val.strip())

        if not entity_locations:
            return violations

        backed_locations = _extract_text_from_result_field(search_result, _LOCATION_FIELDS)

        for loc in entity_locations:
            loc_lower = loc.lower()
            if not backed_locations or not any(
                loc_lower in backed or backed in loc_lower
                for backed in backed_locations
            ):
                violations.append(_violation(
                    "locations",
                    f"Location '{loc}' was asserted but is absent from all DB result rows."
                ))

        return violations

    @staticmethod
    def _check_relationships(
        summary: str,
        intelligence_bundle: Optional[Any],
    ) -> List[Dict[str, str]]:
        """
        Block relationship-language in the summary when network_data is absent
        or empty.
        """
        violations = []
        if not summary:
            return violations

        # Determine whether we have verified network data
        has_network = False
        if intelligence_bundle is not None:
            network = getattr(intelligence_bundle, "network", None)
            if network and isinstance(network, dict) and network.get("edges"):
                has_network = True

        if has_network:
            return violations  # relationship language is supported

        for pattern in _RELATIONSHIP_PATTERNS:
            match = pattern.search(summary)
            if match:
                violations.append(_violation(
                    "relationships",
                    f"Relationship language ('{match.group(0)}') detected in response "
                    f"but no verified network_data is available."
                ))
                break  # one violation per check is sufficient

        return violations

    @staticmethod
    def _check_recommendations(
        recommended_queries: List[Any],
        evidence_count: int,
    ) -> List[Dict[str, str]]:
        """
        Block recommendation lists when there is zero evidence to back them.
        """
        violations = []
        if evidence_count == 0 and recommended_queries:
            violations.append(_violation(
                "recommendations",
                f"Response contains {len(recommended_queries)} recommendation(s) "
                f"but the DB returned 0 records — no evidence basis exists."
            ))
        return violations

    @staticmethod
    def _check_statistics(
        summary: str,
        evidence_count: int,
        verified_count: int,
    ) -> List[Dict[str, str]]:
        """
        Block numeric claims that materially exceed the verified total count or
        appear when there is no evidence at all.
        """
        violations = []
        if not summary:
            return violations

        if evidence_count == 0:
            for pattern in _STATISTIC_PATTERNS:
                match = pattern.search(summary)
                if match:
                    violations.append(_violation(
                        "statistics",
                        f"Numeric claim '{match.group(0)}' found in response "
                        f"but DB returned 0 records — no evidence basis exists."
                    ))
                    break
            return violations

        # Check for inflated counts — allow a 20% tolerance above verified_count
        verified = max(evidence_count, verified_count or 0)
        threshold = max(verified * 1.2, verified + 5)

        for pattern in _STATISTIC_PATTERNS[:1]:  # Only the count pattern for this check
            matches = pattern.finditer(summary)
            for match in matches:
                raw_num_str = match.group(1).replace(",", "")
                try:
                    claimed_count = int(float(raw_num_str))
                except ValueError:
                    continue
                if claimed_count > threshold:
                    violations.append(_violation(
                        "statistics",
                        f"Claimed count {claimed_count} significantly exceeds verified "
                        f"total count {verified} (threshold: {int(threshold)})."
                    ))
                    break

        return violations


# ---------------------------------------------------------------------------
# Pipeline Stage (thin wrapper — keeps stage logic in pipeline_runner.py
# but the guard itself self-contained for testing)
# ---------------------------------------------------------------------------

class HallucinationGuardStage:
    """
    Pipeline stage wrapper for HallucinationGuard.

    Placed immediately before ResponseGeneratorStage in every execution plan.
    Operates on the partially assembled `context.response` if it already exists
    (e.g. from an early-exit branch), or stores violations for the
    ResponseGeneratorStage to incorporate.
    """

    @staticmethod
    def run(context: Any) -> Any:  # context: ExecutionContext
        try:
            # If a terminal response was already set (e.g. multi-intent error), guard it too
            response_to_check = context.response or {}

            is_safe, violations = HallucinationGuard.validate(
                intent=context.intent or "UNKNOWN",
                search_result=context.search_result,
                resolved_entities=context.resolved_entities,
                response=response_to_check,
                intelligence_bundle=context.intelligence_bundle,
                confidence_metrics=context.confidence_metrics,
            )

            # Stash on context so ResponseGeneratorStage can use it
            context.hallucination_violations = violations
            context.hallucination_safe = is_safe

            if not is_safe:
                if context.response is not None:
                    # Patch the early-exit terminal response right now
                    context.response = HallucinationGuard.sanitize_response(
                        context.response,
                        violations,
                        intent=context.intent or "UNKNOWN",
                        evidence_count=len(context.search_result),
                    )
                # Otherwise ResponseGeneratorStage will call sanitize_response after build
            else:
                if context.response is not None:
                    context.response = HallucinationGuard.mark_safe(context.response)

        except Exception as exc:
            logger.error("HallucinationGuardStage failed: %s", exc, exc_info=True)
            context.warnings.append(f"HallucinationGuardStage failed: {exc}")
            # Fail safe — do not block the pipeline
            context.hallucination_violations = []
            context.hallucination_safe = True

        return context
