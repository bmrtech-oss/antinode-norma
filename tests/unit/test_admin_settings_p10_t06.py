"""Unit tests for Phase 10 Task P10-T06: Admin Settings Endpoints & Audit."""

import unittest
from fastapi.testclient import TestClient

from antinode_norma.server.api import app
from antinode_norma.server.routes.audit import audit_log


class TestAdminSettingsAPI(unittest.TestCase):
    def setUp(self):
        self.admin_client = TestClient(app, headers={"X-User-ID": "admin_user"})
        self.viewer_client = TestClient(app, headers={"X-User-ID": "viewer_user"})
        self.unauth_client = TestClient(app)

    def test_get_settings_unauthenticated_returns_401(self):
        res = self.unauth_client.get("/api/admin/settings")
        self.assertEqual(res.status_code, 401)

    def test_get_settings_non_admin_returns_403(self):
        res = self.viewer_client.get("/api/admin/settings")
        self.assertEqual(res.status_code, 403)

    def test_get_settings_admin_returns_200(self):
        res = self.admin_client.get("/api/admin/settings")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("app_name", data)
        self.assertIn("feature_flags", data)
        self.assertIn("max_repair_attempts", data)

    def test_update_settings_admin_updates_and_audits(self):
        initial_log_count = len(audit_log.records)

        payload = {
            "app_name": "Updated Antinode Norma",
            "feature_flags": {
                "auth_saml": True,
                "governance_audit": True,
            },
            "max_repair_attempts": 5,
            "audit_retention_days": 180,
        }

        res = self.admin_client.put("/api/admin/settings", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["app_name"], "Updated Antinode Norma")
        self.assertEqual(data["max_repair_attempts"], 5)

        # Confirm audit event was recorded
        self.assertEqual(len(audit_log.records), initial_log_count + 1)
        latest_record = audit_log.records[-1]
        self.assertEqual(latest_record.action, "admin:settings_update")
        self.assertEqual(latest_record.actor, "admin_user")
        self.assertEqual(latest_record.payload["new_settings"]["max_repair_attempts"], 5)


if __name__ == "__main__":
    unittest.main()
