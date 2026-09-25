from antinode_norma.gates.runner import GateRunner
from antinode_norma.gates.types import GateContext


def test_q11_detects_curated_fact_contradiction(monkeypatch):
    monkeypatch.setenv("NORMA_FEATURE_KNOWLEDGE_GRAPH", "true")
    context = GateContext(
        gherkin_text="""
Feature: Password reset
  Scenario: Never-expiring reset link
    Given the reset link remains valid forever
"""
    )

    verdict = GateRunner().evaluate(context)

    assert verdict.hard_pass is False
    assert verdict.gate_results["Q11"].passed is False
    assert "reset-link-expiry" in verdict.gate_results["Q11"].issues[0]


def test_q11_accepts_consistent_feature(monkeypatch):
    monkeypatch.setenv("NORMA_FEATURE_KNOWLEDGE_GRAPH", "true")
    context = GateContext(
        gherkin_text="""
Feature: Password reset
  Scenario: Expiring reset link
        Given the reset link expires in twenty-four hours
"""
    )

    verdict = GateRunner().evaluate(context)

    assert verdict.hard_pass is True
    assert verdict.gate_results["Q11"].passed is True
