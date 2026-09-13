from antinode_norma.gates.types import GateContext
from antinode_norma.core.types import TestCase
from antinode_norma.gates.runner import GateRunner


def test_gate_runner_valid_eval():
    gherkin = """
@smoke @TC-101
Feature: Checkout
  @TC-101
  Scenario: Successful checkout
    Given user has item in cart
    When user submits payment
    Then order confirmation is displayed
"""
    test_cases = [TestCase(id="TC-101", title="Successful checkout")]
    ctx = GateContext(gherkin_text=gherkin, test_cases=test_cases)

    runner = GateRunner()
    verdict = runner.evaluate(ctx)

    assert verdict.hard_pass is True
    assert verdict.summary == "PASS"
    assert "Q0" in verdict.gate_results
    assert "Q1" in verdict.gate_results
    assert "Q2" in verdict.gate_results
    assert "Q3" in verdict.gate_results
    assert "Q4" in verdict.gate_results
    assert "Q5" in verdict.gate_results


def test_gate_runner_report_generation():
    gherkin = """
@smoke @TC-101
Feature: Checkout
  @TC-101
  Scenario: Successful checkout
    Given user has item in cart
    When user submits payment
    Then order confirmation is displayed
"""
    test_cases = [TestCase(id="TC-101", title="Successful checkout")]
    ctx = GateContext(gherkin_text=gherkin, test_cases=test_cases)

    runner = GateRunner()
    verdict = runner.evaluate(ctx)
    report = runner.generate_report(verdict)

    assert "# Quality Gate Validation Report" in report
    assert "**Overall Summary:** PASS" in report
    assert "### Gate Q0 — PASSED" in report
    assert "### Gate Q5 — PASSED" in report


def test_gate_runner_failing_eval():
    gherkin = """
Feature: Invalid Checkout
  Scenario: Duplicate title
    Given user submits payment

  Scenario: Duplicate title
    Given user submits payment
"""
    ctx = GateContext(gherkin_text=gherkin)

    runner = GateRunner()
    verdict = runner.evaluate(ctx)

    assert verdict.hard_pass is False
    assert verdict.summary == "FAIL"
    assert verdict.gate_results["Q5"].passed is False
