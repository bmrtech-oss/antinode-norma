"""Unit tests for Phase 9 Task P9-T05: Approval Queue API Routes."""

import unittest
from fastapi.testclient import TestClient

from antinode_norma.server.api import app


class TestApprovalQueueAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_approval_workflow(self):
        # 1. Create approval request
        res_create = self.client.post(
            "/api/approvals",
            json={
                "feature_id": "feat-101",
                "gherkin_text": "Feature: Login\n  Scenario: Valid login",
                "requested_by": "developer_1",
            },
        )
        self.assertEqual(res_create.status_code, 200)
        req_data = res_create.json()
        req_id = req_data["id"]
        self.assertEqual(req_data["status"], "PENDING")
        self.assertEqual(req_data["feature_id"], "feat-101")

        # 2. List approval requests
        res_list = self.client.get("/api/approvals")
        self.assertEqual(res_list.status_code, 200)
        items = res_list.json()
        self.assertTrue(any(i["id"] == req_id for i in items))

        # 3. Approve request
        res_approve = self.client.post(
            f"/api/approvals/{req_id}/approve",
            json={"reviewer": "qa_lead", "reason": "Looks good"},
        )
        self.assertEqual(res_approve.status_code, 200)
        approved_data = res_approve.json()
        self.assertEqual(approved_data["status"], "APPROVED")
        self.assertEqual(approved_data["reviewer"], "qa_lead")

    def test_reject_workflow(self):
        res_create = self.client.post(
            "/api/approvals",
            json={"feature_id": "feat-102", "gherkin_text": "Feature: Checkout"},
        )
        req_id = res_create.json()["id"]

        res_reject = self.client.post(
            f"/api/approvals/{req_id}/reject",
            json={"reviewer": "sec_lead", "reason": "Missing security tag"},
        )
        self.assertEqual(res_reject.status_code, 200)
        rejected_data = res_reject.json()
        self.assertEqual(rejected_data["status"], "REJECTED")
        self.assertEqual(rejected_data["reason"], "Missing security tag")

    def test_approve_nonexistent_returns_404(self):
        res = self.client.post("/api/approvals/nonexistent-id/approve", json={})
        self.assertEqual(res.status_code, 404)


if __name__ == "__main__":
    unittest.main()
