"""Unit tests for Phase 9 Task P9-T02: Feature Viewer Endpoints."""

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from antinode_norma.server.api import app


class TestFeatureViewerEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app, headers={"X-User-ID": "admin_user"})
        self.temp_dir = tempfile.TemporaryDirectory()
        self.feature_dir = Path(self.temp_dir.name)

        # Create sample feature files
        f1 = self.feature_dir / "user_login.feature"
        f1.write_text(
            """Feature: User Login
  Scenario: Login with valid credentials
    Given the user is on login page
    When the user submits valid credentials
    Then the user lands on dashboard

  Scenario Outline: Login with invalid credentials
    Given the user is on login page
    When the user enters "<user>" and "<pass>"
    Then error message is displayed
""",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_list_features(self):
        response = self.client.get(f"/api/features?dir={self.feature_dir}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["filename"], "user_login.feature")
        self.assertEqual(data[0]["scenario_count"], 2)

    def test_get_feature_detail(self):
        response = self.client.get(f"/api/features/user_login.feature?dir={self.feature_dir}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["filename"], "user_login.feature")
        self.assertEqual(len(data["scenarios"]), 2)
        self.assertIn("Login with valid credentials", data["scenarios"])
        self.assertIn("Login with invalid credentials", data["scenarios"])
        self.assertIn("Feature: User Login", data["content"])

    def test_get_feature_detail_with_gates(self):
        response = self.client.get(f"/api/features/user_login.feature?dir={self.feature_dir}&run_gates=true")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsNotNone(data["gate_results"])
        self.assertIn("hard_pass", data["gate_results"])

    def test_get_feature_404_not_found(self):
        response = self.client.get(f"/api/features/nonexistent.feature?dir={self.feature_dir}")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("detail", data)


if __name__ == "__main__":
    unittest.main()
