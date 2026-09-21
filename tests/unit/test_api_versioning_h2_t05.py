"""Unit tests for Phase H2 Task H2-T05: API Versioning and Deprecation Policy."""

import unittest
from fastapi.testclient import TestClient

from antinode_norma.server.api import app
from bin.check_api_versioning import verify_v1_versioning


class TestAPIVersioningH2T05(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app, headers={"X-User-ID": "admin_user"})

    def test_v1_route_access(self):
        # Versioned route
        v1_res = self.client.get("/v1/api/audit")
        self.assertEqual(v1_res.status_code, 200)

        # Legacy unversioned route alias
        legacy_res = self.client.get("/api/audit")
        self.assertEqual(legacy_res.status_code, 200)

    def test_versioning_verification_script(self):
        self.assertTrue(verify_v1_versioning())


if __name__ == "__main__":
    unittest.main()
