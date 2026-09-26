import pytest

from antinode_aegis.approval import ApprovalWorkflow
from antinode_aegis.audit import AuditLedger
from antinode_aegis.xray import XrayAdapter


FEATURE = """
Feature: Xray delivery
  Scenario: Import case
    Given the feature is approved
"""


def test_aegis_xray_delivery_requires_approval(tmp_path):
    approvals = ApprovalWorkflow(audit=AuditLedger(path=tmp_path / "audit.jsonl"))
    adapter = XrayAdapter(approvals=approvals)

    with pytest.raises(PermissionError, match="not approved"):
        adapter.deliver(
            tenant_id="tenant-1",
            feature_id="FEAT-806",
            gherkin_text=FEATURE,
            project_key="AEG",
        )


def test_aegis_xray_delivery_test_mode(tmp_path):
    approvals = ApprovalWorkflow(audit=AuditLedger(path=tmp_path / "audit.jsonl"))
    request = approvals.submit(tenant_id="tenant-1", feature_id="FEAT-806", requested_by="author")
    approvals.approve(request.request_id, reviewer_id="reviewer")

    report = XrayAdapter(approvals=approvals).deliver(
        tenant_id="tenant-1",
        feature_id="FEAT-806",
        gherkin_text=FEATURE,
        project_key="AEG",
    )

    assert report.delivered_count == 1
    assert report.project_key == "AEG"
    assert report.test_mode is True
