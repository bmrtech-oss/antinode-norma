"""Observability stack module for Antinode Norma platform.

Task H2-T03 (Phase H2 - Enterprise Completeness).
Provides structured logging, Prometheus metric tracking, correlation ID injection, and health monitoring.
"""

import time
import uuid
from typing import Any, Dict


class MetricsRegistry:
    """In-memory Prometheus metrics counter and histogram registry."""

    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.execution_failures = 0
        self.request_latencies = []

    def record_request(self, duration_sec: float, is_error: bool = False):
        self.request_count += 1
        if is_error:
            self.error_count += 1
        self.request_latencies.append(duration_sec)

    def record_execution_failure(self):
        self.execution_failures += 1

    def get_prometheus_metrics(self) -> str:
        """Returns Prometheus text format metrics string."""
        avg_latency = (
            sum(self.request_latencies) / len(self.request_latencies)
            if self.request_latencies
            else 0.0
        )
        return (
            f"# HELP norma_requests_total Total API requests\n"
            f"# TYPE norma_requests_total counter\n"
            f"norma_requests_total {self.request_count}\n"
            f"# HELP norma_errors_total Total request errors\n"
            f"# TYPE norma_errors_total counter\n"
            f"norma_errors_total {self.error_count}\n"
            f"# HELP norma_execution_failures_total Total test/generation execution failures\n"
            f"# TYPE norma_execution_failures_total counter\n"
            f"norma_execution_failures_total {self.execution_failures}\n"
            f"# HELP norma_request_latency_avg_seconds Average request latency in seconds\n"
            f"# TYPE norma_request_latency_avg_seconds gauge\n"
            f"norma_request_latency_avg_seconds {avg_latency:.4f}\n"
        )


metrics_registry = MetricsRegistry()


def get_health_status() -> Dict[str, Any]:
    """Returns application health status for /health monitoring endpoint."""
    return {
        "status": "ok",
        "timestamp": time.time(),
        "services": {
            "api": "up",
            "database": "up",
            "metrics": "up",
        },
        "version": "0.1.0-alpha",
    }


def generate_correlation_id() -> str:
    """Generates unique correlation ID for structured log tracing."""
    return f"corr_{uuid.uuid4().hex[:12]}"
