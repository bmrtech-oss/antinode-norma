"""Unit tests for Phase 9 Task P9-T01: API Foundation."""

import unittest
from fastapi.testclient import TestClient

from antinode_norma.server.api import app


class TestAPIFoundation(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_check_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["version"], "0.1.0-alpha")
        self.assertIn("timestamp", data)

    def test_cors_headers(self):
        response = self.client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("access-control-allow-origin"), "*")
        self.assertNotIn("access-control-allow-credentials", response.headers)

    def test_404_not_found(self):
        response = self.client.get("/nonexistent-endpoint")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
