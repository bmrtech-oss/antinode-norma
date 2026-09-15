from antinode_norma.core.agent import NormaAgent
from antinode_norma.core.types import TestCase
from antinode_norma.governance.audit import AuditLog
from antinode_norma.governance.approval import ApprovalGate


def mock_llm(prompt: str) -> str:
    return """
    @TC-101
    Feature: Transfer Money

      Scenario: Valid transfer
        Given user has account
        When transfer is executed
        Then confirmation is displayed
    """


def test_governance_flags_disabled_by_default(monkeypatch, tmp_path):
    log_file = tmp_path / "audit.jsonl"
    audit = AuditLog(log_path=log_file)
    approval = ApprovalGate(audit_log=audit)

    agent = NormaAgent(
        llm_callable=mock_llm,
        audit_log=audit,
        approval_gate=approval,
    )

    tc = TestCase(id="TC-101", title="Valid transfer", steps=["Given user has account"])
    agent.generate_feature([tc])

    assert len(audit.records) == 0
    assert len(approval.requests) == 0


def test_governance_flags_enabled(monkeypatch, tmp_path):
    monkeypatch.setenv("NORMA_FEATURE_GOVERNANCE_AUDIT", "true")
    monkeypatch.setenv("NORMA_FEATURE_GOVERNANCE_APPROVAL", "true")

    log_file = tmp_path / "audit.jsonl"
    audit = AuditLog(log_path=log_file)
    approval = ApprovalGate(audit_log=audit)

    agent = NormaAgent(
        llm_callable=mock_llm,
        audit_log=audit,
        approval_gate=approval,
    )

    tc = TestCase(id="TC-101", title="Valid transfer", steps=["Given user has account"])
    agent.generate_feature([tc])

    # Audit records: 1 for feature generation + 1 for approval submission
    assert len(audit.records) == 2
    assert len(approval.requests) == 1
    assert audit.records[0].action == "feature_generated"
    assert audit.records[1].action == "approval_submitted"
