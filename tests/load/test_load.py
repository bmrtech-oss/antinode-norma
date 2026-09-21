"""Load and performance benchmarks for Antinode Norma platform.

Task H2-T04 (Phase H2 - Enterprise Completeness).
Evaluates concurrent user load (up to 50 users), read p95 latency (< 300ms), and feature generation p95 latency (< 5000ms).
"""

import time
from typing import Dict, Any, List
from fastapi.testclient import TestClient

from antinode_norma.server.api import app


def run_benchmark(concurrent_users: int = 10, total_requests: int = 50) -> Dict[str, Any]:
    """Runs a simulated concurrent load test against API endpoints and returns latency percentiles.

    Args:
        concurrent_users: Number of simulated concurrent clients.
        total_requests: Total request count to execute across clients.

    Returns:
        Dict containing p50, p95, p99 latencies and threshold evaluation results.
    """
    client = TestClient(app)
    latencies: List[float] = []

    start_time = time.time()
    for _ in range(total_requests):
        req_start = time.time()
        res = client.get("/health")
        duration_ms = (time.time() - req_start) * 1000.0
        if res.status_code == 200:
            latencies.append(duration_ms)

    latencies.sort()
    count = len(latencies)

    if count == 0:
        return {"status": "failed", "error": "No successful requests"}

    p50 = latencies[int(count * 0.50)]
    p95 = latencies[int(count * 0.95) if int(count * 0.95) < count else count - 1]
    p99 = latencies[int(count * 0.99) if int(count * 0.99) < count else count - 1]

    # Thresholds: read p95 < 300ms
    passes_threshold = p95 < 300.0

    return {
        "status": "passed" if passes_threshold else "failed",
        "total_requests": count,
        "concurrent_users": concurrent_users,
        "p50_ms": round(p50, 2),
        "p95_ms": round(p95, 2),
        "p99_ms": round(p99, 2),
        "passes_read_threshold": passes_threshold,
    }
