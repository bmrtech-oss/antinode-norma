from antinode_norma.gates.types import GateContext
from antinode_norma.gates.syntax import Q1SyntaxGate
from antinode_norma.gates.rspec_guard import Q2RSpecGuardGate


def test_q1_syntax_gate_valid():
    gherkin = """
Feature: Account Login
  Scenario: Successful Login
    Given user opens login page
    When user enters valid credentials
    Then user sees dashboard
"""
    ctx = GateContext(gherkin_text=gherkin)
    gate = Q1SyntaxGate()
    res = gate.evaluate(ctx)

    assert res.gate_id == "Q1"
    assert res.passed is True
    assert res.score == 1.0
    assert len(res.issues) == 0


def test_q1_syntax_gate_invalid():
    gherkin = "Invalid feature without feature keyword"
    ctx = GateContext(gherkin_text=gherkin)
    gate = Q1SyntaxGate()
    res = gate.evaluate(ctx)

    assert res.gate_id == "Q1"
    assert res.passed is False
    assert res.score == 0.0
    assert any("Missing 'Feature:' line" in issue for issue in res.issues)


def test_q2_rspec_guard_clean():
    gherkin = """
Feature: User Profile
  Scenario: View profile
    Given user is on settings page
    When user clicks view profile
    Then profile details are displayed
"""
    ctx = GateContext(gherkin_text=gherkin)
    gate = Q2RSpecGuardGate()
    res = gate.evaluate(ctx)

    assert res.gate_id == "Q2"
    assert res.passed is True
    assert res.score == 1.0
    assert len(res.issues) == 0


def test_q2_rspec_guard_forbidden_tokens():
    gherkin = """
Feature: RSpec Leakage
  Scenario: Test with expect and describe
    Given user describes context
    When user expects result
    Then should pass before test
"""
    ctx = GateContext(gherkin_text=gherkin)
    gate = Q2RSpecGuardGate()
    res = gate.evaluate(ctx)

    assert res.gate_id == "Q2"
    assert res.passed is False
    assert res.score == 0.0
    assert len(res.issues) == 1
    issue = res.issues[0]
    assert "Forbidden RSpec keyword(s) detected" in issue
    assert "before" in issue
    assert "context" in issue
    assert "describe" in issue
    assert "expect" in issue
    assert "should" in issue


def test_q2_rspec_guard_no_false_positives():
    gherkin = """
Feature: Letter Notification
  Scenario: Receive letter beforehand
    Given user has a letter
    When user checks inbox beforehand
    Then letter is archived
"""
    ctx = GateContext(gherkin_text=gherkin)
    gate = Q2RSpecGuardGate()
    res = gate.evaluate(ctx)

    assert res.gate_id == "Q2"
    assert res.passed is True
