import pytest

from antinode_aegis.approval import ApprovalStatus, ApprovalWorkflow
from antinode_aegis.audit import AuditLedger


def test_aegis_approval_lifecycle_is_tenant_aware(tmp_path):
    audit = AuditLedger(path=tmp_path / "audit.jsonl")
    workflow = ApprovalWorkflow(audit=audit)

    request = workflow.submit(
        tenant_id="tenant-1",
        feature_id="FEAT-802",
        requested_by="author-1",
    )
    assert request.status is ApprovalStatus.PENDING
    assert workflow.is_approved(tenant_id="tenant-1", feature_id="FEAT-802") is False

    approved = workflow.approve(request.request_id, reviewer_id="reviewer-1", reason="Reviewed")
    assert approved.status is ApprovalStatus.APPROVED
    assert workflow.is_approved(tenant_id="tenant-1", feature_id="FEAT-802") is True
    assert workflow.is_approved(tenant_id="tenant-2", feature_id="FEAT-802") is False
    assert [event.action for event in audit.events] == [
        "approval.requested",
        "approval.approved",
    ]
    assert audit.verify_integrity() is True


def test_aegis_approval_rejects_invalid_transition(tmp_path):
    workflow = ApprovalWorkflow(audit=AuditLedger(path=tmp_path / "audit.jsonl"))
    request = workflow.submit(
        tenant_id="tenant-1",
        feature_id="FEAT-803",
        requested_by="author-1",
    )
    workflow.reject(request.request_id, reviewer_id="reviewer-1", reason="Needs revision")

    with pytest.raises(ValueError, match="Cannot transition request in REJECTED state"):
        workflow.approve(request.request_id, reviewer_id="reviewer-2")
