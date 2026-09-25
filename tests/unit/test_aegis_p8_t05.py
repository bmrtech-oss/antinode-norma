import pytest

from antinode_aegis.approval import ApprovalWorkflow
from antinode_aegis.audit import AuditLedger
from antinode_aegis.testrail import TestRailAdapter


FEATURE = """
Feature: Delivery
  Scenario: First case
    Given the feature is approved
  Scenario: Second case
    Given the feature is approved
"""


def test_aegis_testrail_delivery_requires_approval(tmp_path):
    approvals = ApprovalWorkflow(audit=AuditLedger(path=tmp_path / "audit.jsonl"))
    adapter = TestRailAdapter(approvals=approvals)

    with pytest.raises(PermissionError, match="not approved"):
        adapter.deliver(
            tenant_id="tenant-1",
            feature_id="FEAT-805",
            gherkin_text=FEATURE,
            project_id=8,
        )


def test_aegis_testrail_delivery_test_mode(tmp_path):
    approvals = ApprovalWorkflow(audit=AuditLedger(path=tmp_path / "audit.jsonl"))
    request = approvals.submit(tenant_id="tenant-1", feature_id="FEAT-805", requested_by="author")
    approvals.approve(request.request_id, reviewer_id="reviewer")
    adapter = TestRailAdapter(approvals=approvals)

    report = adapter.deliver(
        tenant_id="tenant-1",
        feature_id="FEAT-805",
        gherkin_text=FEATURE,
        project_id=8,
    )

    assert report.delivered_count == 2
    assert report.case_ids == [8001, 8002]
    assert report.test_mode is True
