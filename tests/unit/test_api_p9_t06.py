"""Unit tests for Phase 9 Task P9-T06: Audit & Traceability API Routes."""

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from antinode_norma.server.api import app


class TestAuditAndTraceabilityAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app, headers={"X-User-ID": "admin_user"})
        self.temp_dir = tempfile.TemporaryDirectory()
        self.feature_dir = Path(self.temp_dir.name)

        f1 = self.feature_dir / "checkout.feature"
        f1.write_text(
            """@REQ-501 @smoke
Feature: Online Checkout
  Scenario: Successful order placement
    Given the user has items in cart
    When the user completes payment
    Then order confirmation is displayed
""",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_get_traceability_matrix(self):
        response = self.client.get(f"/api/traceability?dir={self.feature_dir}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("items", data)
        self.assertTrue(len(data["items"]) > 0)
        self.assertEqual(data["items"][0]["requirement_id"], "@REQ-501")

    def test_audit_endpoints(self):
        # List audit records
        res_list = self.client.get("/api/audit")
        self.assertEqual(res_list.status_code, 200)
        self.assertIsInstance(res_list.json(), list)

        # Verify integrity via HTTP endpoint
        res_verify = self.client.get("/api/audit/verify")
        self.assertEqual(res_verify.status_code, 200)
        data = res_verify.json()
        self.assertIn("is_valid", data)
        self.assertIn("record_count", data)


if __name__ == "__main__":
    unittest.main()
