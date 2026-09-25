from antinode_norma.governance.approval import ApprovalGate
from antinode_norma.governance.audit import AuditLog
from antinode_norma.database import migrate


def test_database_backed_audit_and_approval_survive_reload(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'app.db'}"
    migrate(database_url)
    audit = AuditLog(database_url=database_url)
    approvals = ApprovalGate(audit_log=audit, database_url=database_url)

    request = approvals.submit_request(
        feature_id="DB-FEATURE-1",
        gherkin_text="Feature: Database persistence",
        requested_by="admin",
        tenant_id="tenant-1",
    )
    approvals.approve(request.id, reviewer="reviewer", reason="verified")

    reloaded_audit = AuditLog(database_url=database_url)
    reloaded_approvals = ApprovalGate(audit_log=reloaded_audit, database_url=database_url)

    assert reloaded_approvals.is_approved("DB-FEATURE-1") is True
    assert len(reloaded_audit.records) == 2
    assert reloaded_audit.verify_integrity() is True
