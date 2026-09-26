from antinode_aegis.approval import ApprovalWorkflow
from antinode_aegis.audit import AuditLedger
from antinode_norma.core.agent import NormaAgent
from antinode_norma.core.types import TestCase


FEATURE = """
@TC-804
Feature: Aegis governance
  Scenario: Governed feature
    Given the user is authenticated
    When the user requests a feature
    Then the feature is generated
"""


def test_aegis_governance_wiring_is_disabled_by_default(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    audit = AuditLedger(path=tmp_path / "audit.jsonl")
    approval = ApprovalWorkflow(audit=audit)
    agent = NormaAgent(llm_callable=lambda _: FEATURE, aegis_audit=audit, aegis_approval=approval)

    agent.generate_feature([TestCase(id="TC-804", title="Governed feature")])

    assert audit.events == []
    assert approval.requests == {}


def test_aegis_governance_wiring_records_generation_and_request(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NORMA_FEATURE_AEGIS_GOVERNANCE", "true")
    audit = AuditLedger(path=tmp_path / "audit.jsonl")
    approval = ApprovalWorkflow(audit=audit)
    agent = NormaAgent(llm_callable=lambda _: FEATURE, aegis_audit=audit, aegis_approval=approval)

    agent.generate_feature([TestCase(id="TC-804", title="Governed feature")])

    assert [event.action for event in audit.events] == [
        "generation.completed",
        "approval.requested",
    ]
    assert len(approval.requests) == 1
    assert audit.verify_integrity() is True
