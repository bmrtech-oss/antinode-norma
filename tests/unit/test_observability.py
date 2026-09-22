"""Unit tests for Phase H2 Task H2-T03: Observability Stack."""

import unittest
from fastapi.testclient import TestClient

from antinode_norma.server.api import app
from antinode_norma.utils.observability import (
    generate_correlation_id,
    get_health_status,
    metrics_registry,
)


class TestObservability(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_get_health_status(self):
        status = get_health_status()
        self.assertEqual(status["status"], "ok")
        self.assertIn("services", status)
        self.assertEqual(status["services"]["api"], "up")

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")

    def test_metrics_registry_and_endpoint(self):
        metrics_registry.record_request(0.12, is_error=False)
        metrics_registry.record_execution_failure()

        metrics_text = metrics_registry.get_prometheus_metrics()
        self.assertIn("norma_requests_total", metrics_text)
        self.assertIn("norma_execution_failures_total", metrics_text)

        response = self.client.get("/metrics")
        self.assertEqual(response.status_code, 200)
        self.assertIn("norma_requests_total", response.text)

    def test_generate_correlation_id(self):
        corr_id = generate_correlation_id()
        self.assertTrue(corr_id.startswith("corr_"))
        self.assertEqual(len(corr_id), 17)


if __name__ == "__main__":
    unittest.main()
