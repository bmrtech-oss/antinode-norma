from antinode_norma.gates.types import GateContext
from antinode_norma.gates.state import Q9StateModelGate
from antinode_norma.core.types import TestCase


def test_q9_empty_context():
    gate = Q9StateModelGate()
    context = GateContext(gherkin_text="")
    result = gate.evaluate(context)
    assert result.passed is True
    assert result.score == 1.0


def test_q9_all_keywords_present():
    gherkin = """
    Feature: Transfer Money

      Scenario: Successful transfer
        Given the user logged in
        When the user submits transfer
        Then money is transferred
    """
    gate = Q9StateModelGate()
    context = GateContext(gherkin_text=gherkin)
    result = gate.evaluate(context)
    assert result.passed is True
    assert result.score == 1.0


def test_q9_missing_when_and_then():
    gherkin = """
    Feature: Transfer Money

      Scenario: Incomplete scenario
        Given the user logged in
        And the balance is $100
    """
    gate = Q9StateModelGate()
    context = GateContext(gherkin_text=gherkin)
    result = gate.evaluate(context)
    assert result.passed is False
    assert result.score == 0.0
    assert "missing keywords: When, Then" in result.issues[0]


def test_q9_background_given_inheritance():
    gherkin = """
    Feature: Background Given

      Background:
        Given the system is initialized

      Scenario: Perform action
        When user clicks execute
        Then operation completes
    """
    gate = Q9StateModelGate()
    context = GateContext(gherkin_text=gherkin)
    result = gate.evaluate(context)
    assert result.passed is True
    assert result.score == 1.0


def test_q9_test_cases_input():
    tc1 = TestCase(id="TC1", title="Case 1", steps=["Given state 1", "When action 1", "Then outcome 1"])
    tc2 = TestCase(id="TC2", title="Case 2", steps=["When action 2", "Then outcome 2"])
    gate = Q9StateModelGate()
    context = GateContext(test_cases=[tc1, tc2])
    result = gate.evaluate(context)
    assert result.passed is False
    assert result.score == 0.5
