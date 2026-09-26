from antinode_norma.gates.graph import Q11GraphConsistencyGate, Q12GraphCoverageGate
from antinode_norma.gates.runner import GateRunner
from antinode_norma.gates.types import GateContext


def test_q11_rejects_curated_contradiction():
    result = Q11GraphConsistencyGate().evaluate(
        GateContext(gherkin_text="Feature: Reset\n  Scenario: Unsafe\n    Given the reset link remains valid forever")
    )

    assert result.passed is False
    assert "reset-link-expiry" in result.issues[0]


def test_q12_requires_graph_concept():
    result = Q12GraphCoverageGate().evaluate(
        GateContext(gherkin_text="Feature: Account\n  Scenario: Covered\n    Given the password requires eight characters")
    )

    assert result.passed is True
    assert result.score == 1.0


def test_q12_fails_without_graph_concept():
    result = Q12GraphCoverageGate().evaluate(
        GateContext(gherkin_text="Feature: Generic\n  Scenario: Uncovered\n    Given the system is ready")
    )

    assert result.passed is False
    assert result.score == 0.0


def test_graph_gates_are_opt_in(monkeypatch):
    monkeypatch.setenv("NORMA_FEATURE_KNOWLEDGE_GRAPH", "false")
    assert "Q11" not in [gate.gate_id for gate in GateRunner().gates]
    monkeypatch.setenv("NORMA_FEATURE_KNOWLEDGE_GRAPH", "true")
    gate_ids = [gate.gate_id for gate in GateRunner().gates]
    assert gate_ids[-2:] == ["Q11", "Q12"]
