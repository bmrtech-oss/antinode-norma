from antinode_norma.gates.types import GateContext
from antinode_norma.core.types import TestCase
from antinode_norma.gates.traceability import Q3TraceabilityGate, Q4OrphanTagsGate


def test_q3_traceability_all_present():
    gherkin = """
@TC-101 @TC-102
Feature: Authentication
  @TC-101
  Scenario: Login
    Given user opens login page
    When user enters password
    Then user is authenticated

  @TC-102
  Scenario: Logout
    Given user is logged in
    When user clicks logout
    Then user is logged out
"""
    test_cases = [
        TestCase(id="TC-101", title="Login"),
        TestCase(id="TC-102", title="Logout"),
    ]
    ctx = GateContext(gherkin_text=gherkin, test_cases=test_cases)
    gate = Q3TraceabilityGate()
    res = gate.evaluate(ctx)

    assert res.gate_id == "Q3"
    assert res.passed is True
    assert res.score == 1.0
    assert len(res.issues) == 0


def test_q3_traceability_missing_id():
    gherkin = """
@TC-101
Feature: Authentication
  @TC-101
  Scenario: Login
    Given user opens login page
"""
    test_cases = [
        TestCase(id="TC-101", title="Login"),
        TestCase(id="TC-102", title="Logout"),
    ]
    ctx = GateContext(gherkin_text=gherkin, test_cases=test_cases)
    gate = Q3TraceabilityGate()
    res = gate.evaluate(ctx)

    assert res.gate_id == "Q3"
    assert res.passed is False
    assert res.score == 0.0
    assert len(res.issues) == 1
    assert "TC-102" in res.issues[0]


def test_q4_orphan_tags_clean():
    gherkin = """
@smoke @TC-101
Feature: Authentication
  @TC-101 @ui
  Scenario: Login
    Given user opens login page
"""
    test_cases = [TestCase(id="TC-101", title="Login")]
    ctx = GateContext(gherkin_text=gherkin, test_cases=test_cases)
    gate = Q4OrphanTagsGate()
    res = gate.evaluate(ctx)

    assert res.gate_id == "Q4"
    assert res.passed is True
    assert res.score == 1.0
    assert len(res.issues) == 0


def test_q4_orphan_tags_detected():
    gherkin = """
@smoke @TC-101 @UNKNOWN-TAG
Feature: Authentication
  @TC-101 @ORPHAN-999
  Scenario: Login
    Given user opens login page
"""
    test_cases = [TestCase(id="TC-101", title="Login")]
    ctx = GateContext(gherkin_text=gherkin, test_cases=test_cases)
    gate = Q4OrphanTagsGate()
    res = gate.evaluate(ctx)

    assert res.gate_id == "Q4"
    assert res.passed is False
    assert res.score == 0.0
    assert len(res.issues) == 1
    assert "@ORPHAN-999" in res.issues[0]
    assert "@UNKNOWN-TAG" in res.issues[0]
