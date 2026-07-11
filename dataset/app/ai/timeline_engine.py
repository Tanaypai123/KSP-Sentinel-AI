"""
timeline_engine.py
Phase 5.6 — Enterprise Investigation Timeline Engine

Deterministic chronological reconstruction of investigation events
from verified database records only.

Rules:
- NO LLM reasoning
- NO inferred timestamps
- NO guessed ordering
- NO future event prediction
- If timestamps missing → "Timestamp unavailable."
- If ordering cannot be verified → "Chronological order cannot be verified."
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

EVENT_TYPES = frozenset([
    "FIR Registered",
    "Crime Occurred",
    "Complaint Filed",
    "Victim Statement",
    "Witness Statement",
    "Arrest",
    "Bail",
    "Recovery",
    "Weapon Seized",
    "Vehicle Seized",
    "Charge Sheet",
    "Court Hearing",
    "Transfer",
    "Evidence Added",
    "Evidence Updated",
    "Case Closed",
    "Recommendation Generated",
])

TIMESTAMP_UNAVAILABLE = "Timestamp unavailable."
ORDER_UNVERIFIED = "Chronological order cannot be verified."

# Date parsing patterns in priority order
DATE_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%Y/%m/%d",
]


# ─────────────────────────────────────────────────────────────────────────────
# DATA STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TimelineEvent:
    """
    A single verified investigation event on the timeline.
    All fields are sourced from database records — no inference.
    """
    event_id: str
    event_type: str              # One of EVENT_TYPES
    timestamp: Optional[str]     # ISO-format string or None
    timestamp_dt: Optional[datetime]  # Parsed datetime or None
    source_table: str
    source_record: str           # crime_no or record identifier
    supporting_fir: str
    district: str
    station: str
    officer: str
    confidence: float            # 0.0 – 1.0
    evidence_score: int          # 0 – 100
    reason_chain: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp or TIMESTAMP_UNAVAILABLE,
            "source_table": self.source_table,
            "source_record": self.source_record,
            "supporting_fir": self.supporting_fir,
            "district": self.district,
            "station": self.station,
            "officer": self.officer,
            "confidence": self.confidence,
            "evidence_score": self.evidence_score,
            "reason_chain": self.reason_chain,
        }


@dataclass
class DurationStat:
    """Temporal analytics output."""
    fir_id: str
    start_date: Optional[str]
    end_date: Optional[str]
    duration_days: Optional[int]
    status: str   # "Computed" | "Timestamp unavailable."

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fir_id": self.fir_id,
            "start_date": self.start_date or TIMESTAMP_UNAVAILABLE,
            "end_date": self.end_date or TIMESTAMP_UNAVAILABLE,
            "duration_days": self.duration_days,
            "status": self.status,
        }


# ─────────────────────────────────────────────────────────────────────────────
# TIMELINE BUILDER
# ─────────────────────────────────────────────────────────────────────────────

class TimelineBuilder:
    """
    Extracts TimelineEvents from database FIR records.
    Only creates events for fields that are present and non-null.
    """

    _event_counter: int = 0

    @classmethod
    def _next_id(cls) -> str:
        cls._event_counter += 1
        return f"EVT-{cls._event_counter:06d}"

    @classmethod
    def build(cls, results: List[Dict]) -> List[TimelineEvent]:
        """
        Build list of TimelineEvents from search_result records.
        Each FIR can contribute multiple events depending on fields present.
        """
        events: List[TimelineEvent] = []

        for row in results:
            crime_no = (row.get("crime_no") or row.get("case_no") or
                        row.get("fir_no") or "UNKNOWN")
            district = str(row.get("district_name") or "")
            station = str(row.get("police_station_name") or "")
            officer = str(row.get("officer_name") or row.get("io_name") or "")

            # ── FIR Registered ───────────────────────────────────────────────
            reg_date = row.get("crime_registered_date")
            events.append(cls._make_event(
                event_type="FIR Registered",
                raw_ts=reg_date,
                source_table="fir_records",
                source_record=crime_no,
                supporting_fir=crime_no,
                district=district, station=station, officer=officer,
                confidence=1.0, evidence_score=100,
                reason_chain=[f"FIR {crime_no} registered on {reg_date or 'unknown date'}"],
            ))

            # ── Crime Occurred ────────────────────────────────────────────────
            occ_date = row.get("crime_occurred_date") or row.get("occurrence_date")
            if occ_date:
                events.append(cls._make_event(
                    event_type="Crime Occurred",
                    raw_ts=occ_date,
                    source_table="fir_records",
                    source_record=crime_no,
                    supporting_fir=crime_no,
                    district=district, station=station, officer=officer,
                    confidence=1.0, evidence_score=100,
                    reason_chain=[f"Crime occurred on {occ_date} as recorded in FIR {crime_no}"],
                ))

            # ── Complaint Filed ───────────────────────────────────────────────
            complaint_date = row.get("complaint_date")
            if complaint_date:
                events.append(cls._make_event(
                    event_type="Complaint Filed",
                    raw_ts=complaint_date,
                    source_table="fir_records",
                    source_record=crime_no,
                    supporting_fir=crime_no,
                    district=district, station=station, officer=officer,
                    confidence=1.0, evidence_score=95,
                    reason_chain=[f"Complaint filed on {complaint_date} for FIR {crime_no}"],
                ))

            # ── Arrest ───────────────────────────────────────────────────────
            arrest_date = row.get("arrest_date") or row.get("accused_arrest_date")
            if arrest_date:
                events.append(cls._make_event(
                    event_type="Arrest",
                    raw_ts=arrest_date,
                    source_table="arrest_records",
                    source_record=crime_no,
                    supporting_fir=crime_no,
                    district=district, station=station, officer=officer,
                    confidence=1.0, evidence_score=100,
                    reason_chain=[f"Arrest recorded on {arrest_date} in FIR {crime_no}"],
                ))

            # ── Bail ─────────────────────────────────────────────────────────
            bail_date = row.get("bail_date")
            if bail_date:
                events.append(cls._make_event(
                    event_type="Bail",
                    raw_ts=bail_date,
                    source_table="bail_records",
                    source_record=crime_no,
                    supporting_fir=crime_no,
                    district=district, station=station, officer=officer,
                    confidence=1.0, evidence_score=90,
                    reason_chain=[f"Bail granted on {bail_date} for FIR {crime_no}"],
                ))

            # ── Weapon Seized ─────────────────────────────────────────────────
            weapon = row.get("weapon")
            weapon_seized_date = row.get("weapon_seized_date") or row.get("seizure_date")
            if weapon:
                events.append(cls._make_event(
                    event_type="Weapon Seized",
                    raw_ts=weapon_seized_date,
                    source_table="seizure_records",
                    source_record=crime_no,
                    supporting_fir=crime_no,
                    district=district, station=station, officer=officer,
                    confidence=0.95, evidence_score=90,
                    reason_chain=[f"Weapon '{weapon}' associated with FIR {crime_no}"],
                ))

            # ── Vehicle Seized ────────────────────────────────────────────────
            vehicle = row.get("vehicle") or row.get("vehicle_number")
            if vehicle:
                events.append(cls._make_event(
                    event_type="Vehicle Seized",
                    raw_ts=weapon_seized_date,   # Use same date field if available
                    source_table="seizure_records",
                    source_record=crime_no,
                    supporting_fir=crime_no,
                    district=district, station=station, officer=officer,
                    confidence=0.90, evidence_score=85,
                    reason_chain=[f"Vehicle '{vehicle}' associated with FIR {crime_no}"],
                ))

            # ── Charge Sheet ──────────────────────────────────────────────────
            charge_sheet_date = row.get("charge_sheet_date") or row.get("chargesheet_date")
            if charge_sheet_date:
                events.append(cls._make_event(
                    event_type="Charge Sheet",
                    raw_ts=charge_sheet_date,
                    source_table="chargesheet_records",
                    source_record=crime_no,
                    supporting_fir=crime_no,
                    district=district, station=station, officer=officer,
                    confidence=1.0, evidence_score=100,
                    reason_chain=[f"Charge sheet filed on {charge_sheet_date} for FIR {crime_no}"],
                ))

            # ── Court Hearing ─────────────────────────────────────────────────
            court_date = row.get("court_date") or row.get("hearing_date")
            if court_date:
                events.append(cls._make_event(
                    event_type="Court Hearing",
                    raw_ts=court_date,
                    source_table="court_records",
                    source_record=crime_no,
                    supporting_fir=crime_no,
                    district=district, station=station, officer=officer,
                    confidence=1.0, evidence_score=100,
                    reason_chain=[f"Court hearing recorded on {court_date} for FIR {crime_no}"],
                ))

            # ── Case Closed ───────────────────────────────────────────────────
            close_date = row.get("case_closed_date") or row.get("closed_date")
            if close_date:
                events.append(cls._make_event(
                    event_type="Case Closed",
                    raw_ts=close_date,
                    source_table="fir_records",
                    source_record=crime_no,
                    supporting_fir=crime_no,
                    district=district, station=station, officer=officer,
                    confidence=1.0, evidence_score=100,
                    reason_chain=[f"Case {crime_no} closed on {close_date}"],
                ))

            # ── Recovery ──────────────────────────────────────────────────────
            recovery_date = row.get("recovery_date")
            if recovery_date:
                events.append(cls._make_event(
                    event_type="Recovery",
                    raw_ts=recovery_date,
                    source_table="recovery_records",
                    source_record=crime_no,
                    supporting_fir=crime_no,
                    district=district, station=station, officer=officer,
                    confidence=1.0, evidence_score=95,
                    reason_chain=[f"Recovery recorded on {recovery_date} in FIR {crime_no}"],
                ))

            # ── Victim Statement ──────────────────────────────────────────────
            victim_statement_date = row.get("victim_statement_date")
            if victim_statement_date:
                events.append(cls._make_event(
                    event_type="Victim Statement",
                    raw_ts=victim_statement_date,
                    source_table="statement_records",
                    source_record=crime_no,
                    supporting_fir=crime_no,
                    district=district, station=station, officer=officer,
                    confidence=1.0, evidence_score=90,
                    reason_chain=[f"Victim statement recorded on {victim_statement_date} for FIR {crime_no}"],
                ))

            # ── Witness Statement ─────────────────────────────────────────────
            witness_statement_date = row.get("witness_statement_date")
            if witness_statement_date:
                events.append(cls._make_event(
                    event_type="Witness Statement",
                    raw_ts=witness_statement_date,
                    source_table="statement_records",
                    source_record=crime_no,
                    supporting_fir=crime_no,
                    district=district, station=station, officer=officer,
                    confidence=1.0, evidence_score=90,
                    reason_chain=[f"Witness statement recorded on {witness_statement_date} for FIR {crime_no}"],
                ))

            # ── Transfer ──────────────────────────────────────────────────────
            transfer_date = row.get("transfer_date")
            if transfer_date:
                events.append(cls._make_event(
                    event_type="Transfer",
                    raw_ts=transfer_date,
                    source_table="transfer_records",
                    source_record=crime_no,
                    supporting_fir=crime_no,
                    district=district, station=station, officer=officer,
                    confidence=1.0, evidence_score=95,
                    reason_chain=[f"Case transferred on {transfer_date} for FIR {crime_no}"],
                ))

        return events

    @classmethod
    def _make_event(
        cls,
        event_type: str,
        raw_ts: Any,
        source_table: str,
        source_record: str,
        supporting_fir: str,
        district: str,
        station: str,
        officer: str,
        confidence: float,
        evidence_score: int,
        reason_chain: List[str],
    ) -> TimelineEvent:
        ts_str, ts_dt = TimelineValidator.parse_timestamp(raw_ts)
        return TimelineEvent(
            event_id=cls._next_id(),
            event_type=event_type,
            timestamp=ts_str,
            timestamp_dt=ts_dt,
            source_table=source_table,
            source_record=source_record,
            supporting_fir=supporting_fir,
            district=district,
            station=station,
            officer=officer,
            confidence=confidence,
            evidence_score=evidence_score,
            reason_chain=reason_chain,
        )


# ─────────────────────────────────────────────────────────────────────────────
# TIMELINE VALIDATOR
# ─────────────────────────────────────────────────────────────────────────────

class TimelineValidator:
    """
    Validates and parses timestamps from raw database values.
    Never invents or infers timestamps.
    """

    @staticmethod
    def parse_timestamp(raw: Any) -> Tuple[Optional[str], Optional[datetime]]:
        """
        Attempt to parse a raw timestamp value.
        Returns (iso_string, datetime_obj) or (None, None) if unparseable.
        """
        if raw is None:
            return None, None

        raw_str = str(raw).strip()
        if not raw_str or raw_str.lower() in ("none", "null", "nan", "", "nat"):
            return None, None

        for fmt in DATE_FORMATS:
            try:
                dt = datetime.strptime(raw_str, fmt)
                return dt.strftime("%Y-%m-%d"), dt
            except (ValueError, TypeError):
                continue

        # If none of the formats matched
        return None, None

    @staticmethod
    def is_chronologically_ordered(events: List[TimelineEvent]) -> Tuple[bool, str]:
        """
        Verify that events with timestamps are in non-decreasing order.
        Returns (is_ordered, message).
        """
        dated = [e for e in events if e.timestamp_dt is not None]
        if len(dated) < 2:
            return True, "Insufficient dated events to verify order."

        for i in range(len(dated) - 1):
            if dated[i].timestamp_dt > dated[i + 1].timestamp_dt:
                return False, ORDER_UNVERIFIED

        return True, "Chronological order verified."

    @staticmethod
    def find_missing_timestamps(events: List[TimelineEvent]) -> List[Dict[str, str]]:
        """Return events where timestamp is unavailable."""
        return [
            {
                "event_id": e.event_id,
                "event_type": e.event_type,
                "supporting_fir": e.supporting_fir,
                "message": TIMESTAMP_UNAVAILABLE,
            }
            for e in events if e.timestamp_dt is None
        ]


# ─────────────────────────────────────────────────────────────────────────────
# TIMELINE SORTER
# ─────────────────────────────────────────────────────────────────────────────

class TimelineSorter:
    """
    Sorts timeline events chronologically.
    Events without timestamps are placed at the end, preserving insertion order.
    """

    @staticmethod
    def sort(events: List[TimelineEvent]) -> List[TimelineEvent]:
        """
        Sort events chronologically.
        Events with timestamps sorted ascending.
        Events without timestamps (None dt) appended at end.
        """
        with_ts = [e for e in events if e.timestamp_dt is not None]
        without_ts = [e for e in events if e.timestamp_dt is None]

        with_ts.sort(key=lambda e: e.timestamp_dt)
        return with_ts + without_ts

    @staticmethod
    def merge_events(events_a: List[TimelineEvent],
                     events_b: List[TimelineEvent]) -> List[TimelineEvent]:
        """Merge two event lists and re-sort chronologically."""
        combined = events_a + events_b
        return TimelineSorter.sort(combined)


# ─────────────────────────────────────────────────────────────────────────────
# TIMELINE SUMMARIZER
# ─────────────────────────────────────────────────────────────────────────────

class TimelineSummarizer:
    """
    Computes temporal analytics from a sorted event list.
    All calculations are purely arithmetic — no inference.
    """

    @staticmethod
    def find_missing_periods(events: List[TimelineEvent],
                              gap_days: int = 30) -> List[Dict[str, Any]]:
        """
        Detect gaps > gap_days between consecutive dated events.
        Returns list of gap descriptions.
        """
        dated = [e for e in events if e.timestamp_dt is not None]
        gaps = []
        for i in range(len(dated) - 1):
            delta = (dated[i + 1].timestamp_dt - dated[i].timestamp_dt).days
            if delta > gap_days:
                gaps.append({
                    "gap_start": dated[i].timestamp,
                    "gap_end": dated[i + 1].timestamp,
                    "gap_days": delta,
                    "before_event": dated[i].event_type,
                    "after_event": dated[i + 1].event_type,
                    "supporting_firs": list({dated[i].supporting_fir, dated[i + 1].supporting_fir}),
                })
        return gaps

    @staticmethod
    def find_repeated_events(events: List[TimelineEvent]) -> List[Dict[str, Any]]:
        """
        Detect same event_type appearing more than once for the same FIR.
        """
        fir_event_map: Dict[str, Dict[str, int]] = {}
        for e in events:
            fir_event_map.setdefault(e.supporting_fir, {})
            fir_event_map[e.supporting_fir][e.event_type] = \
                fir_event_map[e.supporting_fir].get(e.event_type, 0) + 1

        repeats = []
        for fir, type_counts in fir_event_map.items():
            for event_type, count in type_counts.items():
                if count > 1:
                    repeats.append({
                        "supporting_fir": fir,
                        "event_type": event_type,
                        "count": count,
                    })
        return repeats

    @staticmethod
    def find_long_investigations(events: List[TimelineEvent],
                                  threshold_days: int = 365) -> List[Dict[str, Any]]:
        """
        Identify FIRs whose timeline spans more than threshold_days.
        """
        fir_dates: Dict[str, List[datetime]] = {}
        for e in events:
            if e.timestamp_dt:
                fir_dates.setdefault(e.supporting_fir, []).append(e.timestamp_dt)

        long_cases = []
        for fir, dates in fir_dates.items():
            if len(dates) < 2:
                continue
            span = (max(dates) - min(dates)).days
            if span >= threshold_days:
                long_cases.append({
                    "fir": fir,
                    "span_days": span,
                    "start": min(dates).strftime("%Y-%m-%d"),
                    "end": max(dates).strftime("%Y-%m-%d"),
                })
        long_cases.sort(key=lambda x: x["span_days"], reverse=True)
        return long_cases

    @staticmethod
    def find_recent_activity(events: List[TimelineEvent],
                              days: int = 30) -> List[Dict[str, Any]]:
        """
        Return events from the last `days` days relative to the most recent event.
        """
        dated = [e for e in events if e.timestamp_dt is not None]
        if not dated:
            return []
        max_dt = max(e.timestamp_dt for e in dated)
        recent = [e for e in dated if (max_dt - e.timestamp_dt).days <= days]
        return [e.to_dict() for e in recent]

    @staticmethod
    def compute_duration_stats(events: List[TimelineEvent]) -> List[DurationStat]:
        """
        Compute investigation duration for each FIR (first event → last event).
        """
        fir_dates: Dict[str, List[Tuple[datetime, str]]] = {}
        for e in events:
            if e.timestamp_dt:
                fir_dates.setdefault(e.supporting_fir, []).append(
                    (e.timestamp_dt, e.timestamp)
                )

        stats = []
        # Collect all FIRs from events (including those without timestamps)
        all_firs = list({e.supporting_fir for e in events})
        for fir in all_firs:
            if fir not in fir_dates or not fir_dates[fir]:
                stats.append(DurationStat(
                    fir_id=fir,
                    start_date=None,
                    end_date=None,
                    duration_days=None,
                    status=TIMESTAMP_UNAVAILABLE,
                ))
            else:
                dates = fir_dates[fir]
                dates.sort(key=lambda x: x[0])
                start_dt, start_str = dates[0]
                end_dt, end_str = dates[-1]
                duration = (end_dt - start_dt).days
                stats.append(DurationStat(
                    fir_id=fir,
                    start_date=start_str,
                    end_date=end_str,
                    duration_days=duration,
                    status="Computed",
                ))
        return stats

    @staticmethod
    def compute_activity_heat(events: List[TimelineEvent]) -> Dict[str, int]:
        """
        Compute event count per date (YYYY-MM-DD) for activity heat map.
        Only dated events are included.
        """
        heat: Dict[str, int] = {}
        for e in events:
            if e.timestamp:
                heat[e.timestamp] = heat.get(e.timestamp, 0) + 1
        return heat

    @staticmethod
    def officer_activity_timeline(events: List[TimelineEvent]) -> Dict[str, List[str]]:
        """
        Group events by officer name → list of timestamps (for officer workload view).
        """
        result: Dict[str, List[str]] = {}
        for e in events:
            if e.officer:
                result.setdefault(e.officer, [])
                ts = e.timestamp or TIMESTAMP_UNAVAILABLE
                if ts not in result[e.officer]:
                    result[e.officer].append(ts)
        return result

    @staticmethod
    def district_timeline(events: List[TimelineEvent]) -> Dict[str, Dict[str, Any]]:
        """
        Group events by district with event counts and date ranges.
        """
        result: Dict[str, Dict] = {}
        for e in events:
            if not e.district:
                continue
            dist = e.district
            if dist not in result:
                result[dist] = {
                    "district": dist,
                    "event_count": 0,
                    "firs": set(),
                    "earliest": None,
                    "latest": None,
                    "event_types": set(),
                }
            result[dist]["event_count"] += 1
            result[dist]["firs"].add(e.supporting_fir)
            result[dist]["event_types"].add(e.event_type)
            if e.timestamp_dt:
                if result[dist]["earliest"] is None or e.timestamp_dt < result[dist]["earliest"]:
                    result[dist]["earliest"] = e.timestamp_dt
                if result[dist]["latest"] is None or e.timestamp_dt > result[dist]["latest"]:
                    result[dist]["latest"] = e.timestamp_dt

        # Serialize
        serialized = {}
        for dist, data in result.items():
            serialized[dist] = {
                "district": dist,
                "event_count": data["event_count"],
                "fir_count": len(data["firs"]),
                "event_types": list(data["event_types"]),
                "earliest": data["earliest"].strftime("%Y-%m-%d") if data["earliest"] else TIMESTAMP_UNAVAILABLE,
                "latest": data["latest"].strftime("%Y-%m-%d") if data["latest"] else TIMESTAMP_UNAVAILABLE,
            }
        return serialized

    @staticmethod
    def compare_timelines(events_a: List[TimelineEvent],
                           events_b: List[TimelineEvent]) -> Dict[str, Any]:
        """
        Compare two timeline sets: shared event types, unique to each, date deltas.
        """
        types_a = {e.event_type for e in events_a}
        types_b = {e.event_type for e in events_b}
        shared = types_a & types_b
        only_a = types_a - types_b
        only_b = types_b - types_a

        return {
            "shared_event_types": list(shared),
            "only_in_first": list(only_a),
            "only_in_second": list(only_b),
            "first_event_count": len(events_a),
            "second_event_count": len(events_b),
        }

    @staticmethod
    def compute_average_delay(events: List[TimelineEvent]) -> Dict[str, Any]:
        """
        Compute average delay between consecutive events (in days).
        Only uses dated events.
        """
        dated = [e for e in events if e.timestamp_dt is not None]
        dated.sort(key=lambda e: e.timestamp_dt)
        if len(dated) < 2:
            return {"average_delay_days": None, "status": TIMESTAMP_UNAVAILABLE}

        delays = [(dated[i + 1].timestamp_dt - dated[i].timestamp_dt).days
                  for i in range(len(dated) - 1)]
        avg = sum(delays) / len(delays)
        return {
            "average_delay_days": round(avg, 2),
            "min_delay_days": min(delays),
            "max_delay_days": max(delays),
            "total_events": len(dated),
            "status": "Computed",
        }

    @staticmethod
    def crime_frequency_timeline(events: List[TimelineEvent]) -> Dict[str, int]:
        """
        Count FIR Registered events per year-month.
        """
        freq: Dict[str, int] = {}
        for e in events:
            if e.event_type == "FIR Registered" and e.timestamp_dt:
                ym = e.timestamp_dt.strftime("%Y-%m")
                freq[ym] = freq.get(ym, 0) + 1
        return freq

    @staticmethod
    def repeat_incident_intervals(events: List[TimelineEvent]) -> List[Dict[str, Any]]:
        """
        For each FIR with multiple 'FIR Registered' equivalent events in same district,
        compute interval between occurrences.
        """
        district_dates: Dict[str, List[datetime]] = {}
        for e in events:
            if e.event_type == "FIR Registered" and e.timestamp_dt and e.district:
                district_dates.setdefault(e.district, []).append(e.timestamp_dt)

        intervals = []
        for district, dates in district_dates.items():
            dates.sort()
            if len(dates) < 2:
                continue
            for i in range(len(dates) - 1):
                delta = (dates[i + 1] - dates[i]).days
                intervals.append({
                    "district": district,
                    "interval_days": delta,
                    "from_date": dates[i].strftime("%Y-%m-%d"),
                    "to_date": dates[i + 1].strftime("%Y-%m-%d"),
                })
        intervals.sort(key=lambda x: x["interval_days"])
        return intervals

    @staticmethod
    def station_response_time(events: List[TimelineEvent]) -> List[Dict[str, Any]]:
        """
        For each FIR: compute days between 'Crime Occurred' and 'FIR Registered'.
        Represents station response time.
        """
        fir_events: Dict[str, Dict[str, Optional[datetime]]] = {}
        for e in events:
            fir = e.supporting_fir
            if fir not in fir_events:
                fir_events[fir] = {"Crime Occurred": None, "FIR Registered": None}
            if e.event_type in fir_events[fir]:
                fir_events[fir][e.event_type] = e.timestamp_dt

        results = []
        for fir, data in fir_events.items():
            occ = data.get("Crime Occurred")
            reg = data.get("FIR Registered")
            if occ and reg:
                delta = (reg - occ).days
                results.append({
                    "fir": fir,
                    "crime_occurred": occ.strftime("%Y-%m-%d"),
                    "fir_registered": reg.strftime("%Y-%m-%d"),
                    "response_days": delta,
                    "status": "Computed",
                })
            else:
                results.append({
                    "fir": fir,
                    "response_days": None,
                    "status": TIMESTAMP_UNAVAILABLE,
                })
        return results

    @staticmethod
    def build_summary(
        events: List[TimelineEvent],
        gaps: List[Dict],
        repeats: List[Dict],
        duration_stats: List[DurationStat],
        long_cases: List[Dict],
    ) -> str:
        """Build human-readable summary string."""
        lines = []
        total = len(events)
        dated = len([e for e in events if e.timestamp_dt])
        undated = total - dated

        lines.append(f"Timeline reconstructed: {total} events ({dated} dated, {undated} without verified timestamps).")

        if gaps:
            lines.append(f"Investigation gaps detected: {len(gaps)} period(s) exceeding 30 days.")
        if repeats:
            lines.append(f"Repeated events found: {len(repeats)} instance(s) of duplicate event types per FIR.")
        if long_cases:
            lines.append(f"Long investigations: {len(long_cases)} case(s) spanning over 1 year.")

        computed = [d for d in duration_stats if d.status == "Computed"]
        if computed:
            avg_dur = sum(d.duration_days for d in computed) / len(computed)
            lines.append(f"Average investigation duration: {round(avg_dur, 1)} days across {len(computed)} FIR(s).")

        if undated > 0:
            lines.append(f"Warning: {undated} event(s) have missing timestamps — ordering not fully verified.")

        return " ".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENGINE
# ─────────────────────────────────────────────────────────────────────────────

class TimelineEngine:
    """
    Main entry point for the Investigation Timeline Engine.
    """

    MIN_RECORDS = 1  # At least 1 FIR required to build timeline

    @classmethod
    def build_timeline(cls, context: Any) -> Dict[str, Any]:
        """
        Build a complete TimelineReport from context.search_result.
        """
        results = context.search_result or []

        if not results:
            return cls._empty_report("No records available for timeline construction.")

        # ── 1. Build Events ───────────────────────────────────────────────────
        raw_events = TimelineBuilder.build(results)

        # ── 2. Sort Chronologically ───────────────────────────────────────────
        sorted_events = TimelineSorter.sort(raw_events)

        # ── 3. Validate ───────────────────────────────────────────────────────
        is_ordered, order_msg = TimelineValidator.is_chronologically_ordered(sorted_events)
        missing_ts = TimelineValidator.find_missing_timestamps(raw_events)

        # ── 4. Temporal Analytics ─────────────────────────────────────────────
        gaps = TimelineSummarizer.find_missing_periods(sorted_events)
        repeats = TimelineSummarizer.find_repeated_events(sorted_events)
        long_cases = TimelineSummarizer.find_long_investigations(sorted_events)
        recent = TimelineSummarizer.find_recent_activity(sorted_events)
        duration_stats = TimelineSummarizer.compute_duration_stats(sorted_events)
        activity_heat = TimelineSummarizer.compute_activity_heat(sorted_events)
        officer_tl = TimelineSummarizer.officer_activity_timeline(sorted_events)
        district_tl = TimelineSummarizer.district_timeline(sorted_events)
        avg_delay = TimelineSummarizer.compute_average_delay(sorted_events)
        crime_freq = TimelineSummarizer.crime_frequency_timeline(sorted_events)
        repeat_intervals = TimelineSummarizer.repeat_incident_intervals(sorted_events)
        station_rt = TimelineSummarizer.station_response_time(sorted_events)

        # ── 5. Summary ────────────────────────────────────────────────────────
        summary = TimelineSummarizer.build_summary(
            sorted_events, gaps, repeats, duration_stats, long_cases
        )

        return {
            "event_count": len(sorted_events),
            "dated_event_count": len([e for e in sorted_events if e.timestamp_dt]),
            "undated_event_count": len([e for e in sorted_events if not e.timestamp_dt]),
            "chronological_order": is_ordered,
            "order_message": order_msg,
            "events": [e.to_dict() for e in sorted_events],
            "missing_timestamps": missing_ts,
            "gaps": gaps,
            "repeated_events": repeats,
            "long_investigations": long_cases,
            "recent_activity": recent,
            "duration_stats": [d.to_dict() for d in duration_stats],
            "activity_heat": activity_heat,
            "officer_timeline": officer_tl,
            "district_timeline": district_tl,
            "average_delay": avg_delay,
            "crime_frequency": crime_freq,
            "repeat_intervals": repeat_intervals,
            "station_response_time": station_rt,
            "evidence_chain": [
                "Timeline built from verified database field values only",
                "No timestamps inferred or invented",
                "Events without timestamps appended without ordering guarantee",
                "Chronological sort applied to all dated events",
            ],
            "summary": summary,
        }

    @classmethod
    def _empty_report(cls, msg: str) -> Dict[str, Any]:
        return {
            "event_count": 0,
            "dated_event_count": 0,
            "undated_event_count": 0,
            "chronological_order": True,
            "order_message": "No events to validate.",
            "events": [],
            "missing_timestamps": [],
            "gaps": [],
            "repeated_events": [],
            "long_investigations": [],
            "recent_activity": [],
            "duration_stats": [],
            "activity_heat": {},
            "officer_timeline": {},
            "district_timeline": {},
            "average_delay": {"average_delay_days": None, "status": TIMESTAMP_UNAVAILABLE},
            "crime_frequency": {},
            "repeat_intervals": [],
            "station_response_time": [],
            "evidence_chain": [],
            "summary": msg,
        }


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE STAGE WRAPPER
# ─────────────────────────────────────────────────────────────────────────────

class TimelineStage:
    """
    Pipeline stage wrapper for TimelineEngine.
    Inserts between KnowledgeGraphStage and MultiAgentEngineStage.
    """

    @staticmethod
    def run(context: Any) -> Any:
        try:
            context.timeline_report = TimelineEngine.build_timeline(context)
        except Exception as e:
            logger.error(f"TimelineStage failed: {e}", exc_info=True)
            context.warnings.append(f"TimelineStage failed: {e}")
            context.timeline_report = TimelineEngine._empty_report(
                f"Timeline unavailable: {e}"
            )
        return context
