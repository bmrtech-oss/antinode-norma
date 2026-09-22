#!/usr/bin/env python3
"""Load test runner CLI script for Antinode Norma platform.

Task H2-T04 (Phase H2 - Enterprise Completeness).
"""

import sys
from pathlib import Path

# Add repo root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests.load.test_load import run_benchmark


def main():
    print("Executing Antinode Norma Load Test Benchmark (H2-T04)...")
    results = run_benchmark(concurrent_users=50, total_requests=100)

    print(f"Status: {results['status']}")
    print(f"Total Requests: {results['total_requests']}")
    print(f"Concurrent Users: {results['concurrent_users']}")
    print(f"Latency p50: {results['p50_ms']} ms")
    print(f"Latency p95: {results['p95_ms']} ms (Threshold: < 300.0 ms)")
    print(f"Latency p99: {results['p99_ms']} ms")

    if not results["passes_read_threshold"]:
        print("Load test failed p95 latency threshold check (< 300ms)!")
        sys.exit(1)

    print("Load test benchmark passed successfully!")


if __name__ == "__main__":
    main()
