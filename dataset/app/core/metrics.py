"""Application Performance Metrics Tracking Engine.

Records requests, errors, latency statistics, cache hit metrics, and counts
by query intent to facilitate health monitoring diagnostics.
"""

from __future__ import annotations

import time


class ApplicationMetrics:
    """Core runtime counters tracking API usage and latencies."""

    def __init__(self) -> None:
        self.start_time = time.time()
        self.request_count = 0
        self.total_latency_ms = 0.0
        self.cache_hits = 0
        self.cache_misses = 0
        self.errors_count = 0
        self.prediction_count = 0
        self.analytics_count = 0

    @property
    def uptime(self) -> float:
        """Returns application uptime in seconds."""
        return time.time() - self.start_time

    @property
    def average_latency_ms(self) -> float:
        """Calculates running average latency per request."""
        if self.request_count == 0:
            return 0.0
        return round(self.total_latency_ms / self.request_count, 2)

    def record_request(
        self,
        latency_ms: float,
        is_hit: bool = False,
        is_error: bool = False,
        intent: str = ""
    ) -> None:
        """Record details of a processed API request."""
        self.request_count += 1
        self.total_latency_ms += latency_ms
        if is_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
        
        if is_error:
            self.errors_count += 1

        if intent == "PREDICT_CRIME":
            self.prediction_count += 1
        elif intent in ["CRIME_TREND", "HOTSPOT", "AGGREGATE_COUNT"]:
            self.analytics_count += 1


# Global metrics tracker instance
global_metrics = ApplicationMetrics()
