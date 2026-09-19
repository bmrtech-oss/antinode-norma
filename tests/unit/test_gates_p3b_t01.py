from antinode_norma.gates.types import GateContext
from antinode_norma.gates.declarative import Q6DeclarativeStyleGate


def test_q6_declarative_style_clean():
    gherkin = """
Feature: User Login
  Scenario: Login with valid credentials
    Given the user is on the login page
    When the user submits valid credentials
    Then the user reaches the dashboard
"""
    ctx = GateContext(gherkin_text=gherkin)
    gate = Q6DeclarativeStyleGate()
    res = gate.evaluate(ctx)

    assert res.gate_id == "Q6"
    assert gate.is_hard_gate is False
    assert res.passed is True
    assert res.score == 1.0


def test_q6_declarative_style_imperative_detected():
    gherkin = """
Feature: Imperative UI Test
  Scenario: Click and type mechanics
    When click on the "Submit" button
    And type "test@example.com" into
    And fill in the "Password" field
"""
    ctx = GateContext(gherkin_text=gherkin)
    gate = Q6DeclarativeStyleGate()
    res = gate.evaluate(ctx)

    assert res.gate_id == "Q6"
    assert res.passed is False
    assert res.score < 0.90
    assert len(res.issues) == 3
