from antinode_norma.gates.types import GateContext
from antinode_norma.gates.duplicates import Q5DuplicatesGate


def test_q5_duplicates_clean():
    gherkin = """
Feature: Shopping Cart
  Scenario: Add item to cart
    Given user is on product page
    When user clicks add to cart
    Then item is in cart

  Scenario Outline: Remove item from cart
    Given user has <item> in cart
    When user clicks remove
    Then cart is empty

    Examples:
      | item   |
      | Book   |
      | Laptop |
"""
    ctx = GateContext(gherkin_text=gherkin)
    gate = Q5DuplicatesGate()
    res = gate.evaluate(ctx)

    assert res.gate_id == "Q5"
    assert res.passed is True
    assert res.score == 1.0
    assert len(res.issues) == 0


def test_q5_duplicates_detected():
    gherkin = """
Feature: Shopping Cart
  Scenario: Add item to cart
    Given user is on product page
    When user clicks add to cart
    Then item is in cart

  Scenario: Add Item To Cart
    Given user is on another product page
    When user clicks add to cart
    Then item is in cart
"""
    ctx = GateContext(gherkin_text=gherkin)
    gate = Q5DuplicatesGate()
    res = gate.evaluate(ctx)

    assert res.gate_id == "Q5"
    assert res.passed is False
    assert res.score == 0.0
    assert len(res.issues) == 1
    assert "Add Item To Cart" in res.issues[0] or "Add item to cart" in res.issues[0]
