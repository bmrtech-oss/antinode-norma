"""Observability stack module for Antinode Norma platform.

Task H2-T03 (Phase H2 - Enterprise Completeness).
Provides structured logging, Prometheus metric tracking, correlation ID injection, and health monitoring.
"""

import time
import uuid
import threading
from typing import Any, Dict


class MetricsRegistry:
    """In-memory Prometheus metrics counter and histogram registry."""

    def __init__(self):
        self._lock = threading.Lock()
        self.request_count = 0
        self.error_count = 0
        self.execution_failures = 0
        self.request_latencies = []
        self.generation_queue_depth = 0
        self.generation_active = 0
        self.generation_capacity = 0
        self.generation_queue_rejections = 0
        self.generation_jobs_completed = 0
        self.generation_jobs_failed = 0
        self.generation_jobs_abandoned = 0
        self.generation_jobs_cancelled = 0
        self.generation_rows_processed = 0
        self.generation_duration_sum = 0.0
        self.generation_duration_count = 0
        self.generation_duration_max = 0.0
        self.rate_limit_rejections = {"upload": 0, "generation": 0}
        self.retention_deleted_artifacts = 0
        self.retention_deleted_imports = 0
        self.retention_skipped_protected = 0
        self.provider_calls = 0
        self.provider_failures = 0
        self.provider_timeouts = 0
        self.provider_retries = 0
        self.provider_circuit_open = 0

    def record_request(self, duration_sec: float, is_error: bool = False):
        self.request_count += 1
        if is_error:
            self.error_count += 1
        self.request_latencies.append(duration_sec)

    def record_execution_failure(self):
        self.execution_failures += 1

    def record_provider_call(self, *, success: bool = False, timeout: bool = False,
                             retry: bool = False, circuit_open: bool = False) -> None:
        with self._lock:
            self.provider_calls += 1
            self.provider_failures += not success
            self.provider_timeouts += timeout
            self.provider_retries += retry
            self.provider_circuit_open += circuit_open

    def set_generation_capacity(self, capacity: int) -> None:
        self.generation_capacity = max(0, capacity)

    def record_generation_admitted(self) -> None:
        with self._lock:
            self.generation_queue_depth += 1

    def record_generation_queue_rejection(self) -> None:
        with self._lock:
            self.generation_queue_rejections += 1

    def record_generation_not_started(self) -> None:
        with self._lock:
            self.generation_queue_depth = max(0, self.generation_queue_depth - 1)

    def record_generation_worker_stopped(self) -> None:
        with self._lock:
            self.generation_active = max(0, self.generation_active - 1)

    def record_generation_started(self) -> None:
        with self._lock:
            self.generation_queue_depth = max(0, self.generation_queue_depth - 1)
            self.generation_active += 1

    def record_generation_finished(self, status: str, duration_sec: float = 0.0,
                                  rows_processed: int = 0) -> None:
        with self._lock:
            self.generation_active = max(0, self.generation_active - 1)
            self.generation_jobs_completed += status in {"completed", "completed_with_errors"}
            self.generation_jobs_failed += status in {"failed", "completed_with_errors"}
            self.generation_jobs_abandoned += status == "abandoned"
            self.generation_jobs_cancelled += status == "cancelled"
            self.generation_rows_processed += max(0, rows_processed)
            if duration_sec > 0:
                self.generation_duration_sum += duration_sec
                self.generation_duration_count += 1
                self.generation_duration_max = max(self.generation_duration_max, duration_sec)

    def record_rate_limit_rejection(self, limit: str) -> None:
        if limit in self.rate_limit_rejections:
            with self._lock:
                self.rate_limit_rejections[limit] += 1

    def record_retention_cleanup(self, report: Dict[str, int]) -> None:
        with self._lock:
            self.retention_deleted_artifacts += report.get("deleted_artifacts", 0)
            self.retention_deleted_imports += report.get("deleted_imports", 0)
            self.retention_skipped_protected += report.get("skipped_protected", 0)

    def get_generation_snapshot(self) -> Dict[str, Any]:
        """Return non-sensitive operational generation signals for dashboards."""
        with self._lock:
            return {
                "queue_depth": self.generation_queue_depth,
                "active_jobs": self.generation_active,
                "capacity": self.generation_capacity,
                "queue_rejections": self.generation_queue_rejections,
                "completed_jobs": self.generation_jobs_completed,
                "failed_jobs": self.generation_jobs_failed,
                "abandoned_jobs": self.generation_jobs_abandoned,
                "cancelled_jobs": self.generation_jobs_cancelled,
                "rows_processed": self.generation_rows_processed,
                "average_duration_seconds": round(
                    self.generation_duration_sum / self.generation_duration_count, 4
                ) if self.generation_duration_count else 0.0,
                "max_duration_seconds": round(self.generation_duration_max, 4),
                "rate_limit_rejections": dict(self.rate_limit_rejections),
                "retention_cleanup": {
                    "deleted_artifacts": self.retention_deleted_artifacts,
                    "deleted_imports": self.retention_deleted_imports,
                    "skipped_protected": self.retention_skipped_protected,
                },
                "provider": {
                    "calls": self.provider_calls,
                    "failures": self.provider_failures,
                    "timeouts": self.provider_timeouts,
                    "retries": self.provider_retries,
                    "circuit_open": self.provider_circuit_open,
                },
            }

    def get_prometheus_metrics(self) -> str:
        """Returns Prometheus text format metrics string."""
        avg_latency = (
            sum(self.request_latencies) / len(self.request_latencies)
            if self.request_latencies
            else 0.0
        )
        with self._lock:
            generation_duration_avg = (
                self.generation_duration_sum / self.generation_duration_count
                if self.generation_duration_count else 0.0
            )
            values = {
                "generation_queue_depth": self.generation_queue_depth,
                "generation_active": self.generation_active,
                "generation_capacity": self.generation_capacity,
                "generation_queue_rejections": self.generation_queue_rejections,
                "generation_jobs_completed": self.generation_jobs_completed,
                "generation_jobs_failed": self.generation_jobs_failed,
                "generation_jobs_abandoned": self.generation_jobs_abandoned,
                "generation_jobs_cancelled": self.generation_jobs_cancelled,
                "generation_rows_processed": self.generation_rows_processed,
                "generation_duration_avg": generation_duration_avg,
                "generation_duration_max": self.generation_duration_max,
                "upload_rate_limit_rejections": self.rate_limit_rejections["upload"],
                "generation_rate_limit_rejections": self.rate_limit_rejections["generation"],
                "retention_deleted_artifacts": self.retention_deleted_artifacts,
                "retention_deleted_imports": self.retention_deleted_imports,
                "retention_skipped_protected": self.retention_skipped_protected,
                "provider_calls": self.provider_calls,
                "provider_failures": self.provider_failures,
                "provider_timeouts": self.provider_timeouts,
                "provider_retries": self.provider_retries,
                "provider_circuit_open": self.provider_circuit_open,
            }
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
            "# HELP norma_generation_queue_depth Current admitted generation jobs\n"
            "# TYPE norma_generation_queue_depth gauge\n"
            f"norma_generation_queue_depth {values['generation_queue_depth']}\n"
            "# HELP norma_generation_active_jobs Current running generation jobs\n"
            "# TYPE norma_generation_active_jobs gauge\n"
            f"norma_generation_active_jobs {values['generation_active']}\n"
            "# HELP norma_generation_capacity Configured running plus queued capacity\n"
            "# TYPE norma_generation_capacity gauge\n"
            f"norma_generation_capacity {values['generation_capacity']}\n"
            "# HELP norma_generation_queue_rejections_total Jobs rejected at capacity\n"
            "# TYPE norma_generation_queue_rejections_total counter\n"
            f"norma_generation_queue_rejections_total {values['generation_queue_rejections']}\n"
            "# HELP norma_generation_jobs_total Generation jobs by outcome\n"
            "# TYPE norma_generation_jobs_total counter\n"
            f"norma_generation_jobs_total{{status=\"completed\"}} {values['generation_jobs_completed']}\n"
            f"norma_generation_jobs_total{{status=\"failed\"}} {values['generation_jobs_failed']}\n"
            f"norma_generation_jobs_total{{status=\"abandoned\"}} {values['generation_jobs_abandoned']}\n"
            f"norma_generation_jobs_total{{status=\"cancelled\"}} {values['generation_jobs_cancelled']}\n"
            "# HELP norma_generation_rows_processed_total Generated rows processed\n"
            "# TYPE norma_generation_rows_processed_total counter\n"
            f"norma_generation_rows_processed_total {values['generation_rows_processed']}\n"
            "# HELP norma_generation_duration_seconds Average and maximum job duration\n"
            "# TYPE norma_generation_duration_seconds gauge\n"
            f"norma_generation_duration_seconds{{stat=\"avg\"}} {values['generation_duration_avg']:.4f}\n"
            f"norma_generation_duration_seconds{{stat=\"max\"}} {values['generation_duration_max']:.4f}\n"
            "# HELP norma_rate_limit_rejections_total Rate-limit rejections by operation\n"
            "# TYPE norma_rate_limit_rejections_total counter\n"
            f"norma_rate_limit_rejections_total{{operation=\"upload\"}} {values['upload_rate_limit_rejections']}\n"
            f"norma_rate_limit_rejections_total{{operation=\"generation\"}} {values['generation_rate_limit_rejections']}\n"
            "# HELP norma_retention_cleanup_total Retention cleanup outcomes\n"
            "# TYPE norma_retention_cleanup_total counter\n"
            f"norma_retention_cleanup_total{{result=\"deleted_artifacts\"}} {values['retention_deleted_artifacts']}\n"
            f"norma_retention_cleanup_total{{result=\"deleted_imports\"}} {values['retention_deleted_imports']}\n"
            f"norma_retention_cleanup_total{{result=\"skipped_protected\"}} {values['retention_skipped_protected']}\n"
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
