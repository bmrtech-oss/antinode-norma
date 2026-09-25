from antinode_norma.gates.reuse import Q7StepReuseGate
from antinode_norma.gates.types import GateContext


def test_q7_reuse_passes_repeated_vocabulary():
    gherkin = """
Feature: Account
  Scenario: View balance
    Given the user is logged in
    When the user opens the account
    Then the balance is displayed

  Scenario: View transactions
    Given the user is logged in
    When the user opens the account
    Then the balance is displayed
"""

    result = Q7StepReuseGate().evaluate(GateContext(gherkin_text=gherkin))

    assert result.gate_id == "Q7"
    assert result.passed is True
    assert result.score >= 0.90


def test_q7_reuse_flags_unique_vocabulary():
    gherkin = """
Feature: Account
  Scenario: View balance
    Given the user opens the balance dashboard
    When the user inspects the current account total
    Then the available funds are displayed

  Scenario: Update profile
    Given the customer visits personal preferences
    When the customer changes notification settings
    Then the profile confirmation appears
"""

    result = Q7StepReuseGate().evaluate(GateContext(gherkin_text=gherkin))

    assert result.gate_id == "Q7"
    assert result.passed is False
    assert result.score < 0.90
    assert result.issues


def test_q7_reuse_normalizes_parameters():
    gherkin = """
Feature: Orders
  Scenario: View first order
    Given the user opens order "1001"

  Scenario: View second order
    Given the user opens order "1002"
"""

    result = Q7StepReuseGate().evaluate(GateContext(gherkin_text=gherkin))

    assert result.passed is True
    assert result.score == 1.0
