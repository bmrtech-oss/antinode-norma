import pytest
from antinode_norma.governance.audit import AuditLog
from antinode_norma.governance.approval import ApprovalGate, ApprovalStatus


def test_approval_gate_lifecycle(tmp_path):
    log_file = tmp_path / "audit.jsonl"
    audit = AuditLog(log_path=log_file)
    gate = ApprovalGate(audit_log=audit)

    # Submit
    req = gate.submit_request(feature_id="FEAT-100", gherkin_text="Feature: Account", requested_by="dev1")
    assert req.status == ApprovalStatus.PENDING
    assert gate.is_approved("FEAT-100") is False

    # Approve
    approved_req = gate.approve(request_id=req.id, reviewer="lead1", reason="Looks solid")
    assert approved_req.status == ApprovalStatus.APPROVED
    assert approved_req.reviewer == "lead1"
    assert gate.is_approved("FEAT-100") is True

    # Check audit log records
    assert len(audit.records) == 2
    assert audit.records[0].action == "approval_submitted"
    assert audit.records[1].action == "approval_approved"
    assert audit.verify_integrity() is True


def test_approval_gate_reject_flow(tmp_path):
    log_file = tmp_path / "audit.jsonl"
    audit = AuditLog(log_path=log_file)
    gate = ApprovalGate(audit_log=audit)

    req = gate.submit_request(feature_id="FEAT-200", gherkin_text="Feature: Bad", requested_by="dev2")
    rejected_req = gate.reject(request_id=req.id, reviewer="lead2", reason="Missing Given step")

    assert rejected_req.status == ApprovalStatus.REJECTED
    assert gate.is_approved("FEAT-200") is False
    assert audit.records[1].action == "approval_rejected"
    assert audit.verify_integrity() is True


def test_approval_gate_invalid_transition(tmp_path):
    log_file = tmp_path / "audit.jsonl"
    audit = AuditLog(log_path=log_file)
    gate = ApprovalGate(audit_log=audit)

    req = gate.submit_request(feature_id="FEAT-300", gherkin_text="Feature: Test")
    gate.approve(request_id=req.id, reviewer="lead3")

    with pytest.raises(ValueError, match="Cannot approve request in APPROVED state"):
        gate.approve(request_id=req.id, reviewer="lead3")
