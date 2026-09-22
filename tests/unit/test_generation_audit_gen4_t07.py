"""Focused lifecycle audit coverage for GEN-4-T07."""

from antinode_norma.auth.models import Role, User
from antinode_norma.governance.approval import ApprovalGate
from antinode_norma.server.routes.imports import _audit
from antinode_norma.server.routes import imports
from antinode_norma.governance.audit import AuditLog


def test_generation_lifecycle_audit_contains_safe_context(tmp_path, monkeypatch):
    log = AuditLog(log_path=tmp_path / "audit.jsonl")
    monkeypatch.setattr(imports, "audit_log", log)
    user = User(id="owner-1", username="owner", email="owner@norma.local",
                roles=[Role.VIEWER], tenant_id="tenant-1")

    _audit("generation.uploaded", "import-1", user, format="csv",
           row_count=3, file_size=42)
    _audit("generation.failed", "job-1", user, result="failure",
           error_type="validation", prompt="must-not-be-recorded")

    assert [record.action for record in log.records] == [
        "generation.uploaded", "generation.failed"
    ]
    assert log.records[0].payload["owner_id"] == "owner-1"
    assert log.records[0].payload["tenant_id"] == "tenant-1"
    assert log.records[0].payload["row_count"] == 3
    assert "prompt" not in log.records[1].payload
    assert log.records[1].payload["result"] == "failure"
    assert log.verify_integrity()


def test_approval_lifecycle_audit_preserves_owner_tenant_without_content(tmp_path):
    log = AuditLog(log_path=tmp_path / "approval-audit.jsonl")
    gate = ApprovalGate(audit_log=log)
    request = gate.submit_request(
        feature_id="case-1",
        gherkin_text="Given sensitive generated content",
        requested_by="owner-1",
        owner_id="owner-1",
        tenant_id="tenant-1",
    )
    gate.approve(request.id, reviewer="reviewer-1", reason="internal note")

    assert [record.action for record in log.records] == [
        "approval_submitted", "approval_approved"
    ]
    for record in log.records:
        assert record.payload["owner_id"] == "owner-1"
        assert record.payload["tenant_id"] == "tenant-1"
        assert "Given sensitive generated content" not in record.model_dump_json()
        assert "internal note" not in record.model_dump_json()
