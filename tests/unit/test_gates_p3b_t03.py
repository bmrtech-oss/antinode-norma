from antinode_norma.gates.types import GateContext
from antinode_norma.gates.outline import Q8OutlineUsageGate
from antinode_norma.core.types import TestCase


def test_q8_empty_context():
    gate = Q8OutlineUsageGate()
    context = GateContext(gherkin_text="")
    result = gate.evaluate(context)
    assert result.passed is True
    assert result.score == 1.0


def test_q8_valid_scenario_outline():
    gherkin = """
    Feature: User Login

      Scenario Outline: Login with multiple credentials
        Given the user opens the login page
        When the user enters "<username>" and "<password>"
        Then the user should see "<status>"

      Examples:
        | username | password | status  |
        | alice    | pass123  | success |
        | bob      | wrong    | failure |
    """
    gate = Q8OutlineUsageGate()
    context = GateContext(gherkin_text=gherkin)
    result = gate.evaluate(context)
    assert result.passed is True
    assert result.score == 1.0


def test_q8_repetitive_scenarios_failing():
    gherkin = """
    Feature: User Login Repetitive

      Scenario: Login with Alice
        Given the user opens the login page
        When the user enters "alice" and "pass123"
        Then the user should see "success"

      Scenario: Login with Bob
        Given the user opens the login page
        When the user enters "bob" and "wrong"
        Then the user should see "failure"
    """
    gate = Q8OutlineUsageGate()
    context = GateContext(gherkin_text=gherkin)
    result = gate.evaluate(context)
    assert result.passed is False
    assert result.score < 1.0
    assert len(result.issues) > 0


def test_q8_different_scenarios_passing():
    gherkin = """
    Feature: Account Features

      Scenario: User logs in
        Given the user opens the login page
        When the user submits credentials
        Then the dashboard opens

      Scenario: User logs out
        Given the user is on the dashboard
        When the user clicks logout
        Then the login page opens
    """
    gate = Q8OutlineUsageGate()
    context = GateContext(gherkin_text=gherkin)
    result = gate.evaluate(context)
    assert result.passed is True
    assert result.score == 1.0


def test_q8_test_cases_input():
    tc1 = TestCase(id="TC1", title="Case 1", steps=["Given page opens", "When input 'a' entered", "Then status is 'ok'"])
    tc2 = TestCase(id="TC2", title="Case 2", steps=["Given page opens", "When input 'b' entered", "Then status is 'ok'"])
    gate = Q8OutlineUsageGate()
    context = GateContext(test_cases=[tc1, tc2])
    result = gate.evaluate(context)
    assert result.passed is False
    assert result.score < 1.0
