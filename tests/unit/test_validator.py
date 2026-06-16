# tests/unit/test_validator.py

"""Unit tests for Gherkin validator."""

from antinode_norma.core.validator import validate_gherkin

def test_validate_gherkin_passes():
    """Test that a well-formed Gherkin file passes validation."""
    content = """Feature: Login
  Scenario: Successful login
    Given the user is on the login page
    When the user enters valid credentials
    Then the user sees the dashboard"""
    result = validate_gherkin(content)
    assert result.valid is True
    assert result.errors == []

def test_validate_gherkin_missing_feature():
    """Test that validation fails when Feature: is missing."""
    content = """Scenario: test
    Given something"""
    result = validate_gherkin(content)
    assert result.valid is False
    assert "Missing 'Feature:' line" in result.errors

def test_validate_gherkin_missing_scenario():
    """Test that validation fails when Scenario: is missing."""
    content = """Feature: test
    Given something"""
    result = validate_gherkin(content)
    assert result.valid is False
    # The validator returns a combined message for missing Scenario/Scenario Outline
    assert "Missing 'Scenario:' or 'Scenario Outline:'" in result.errors

def test_validate_gherkin_incomplete_step():
    """Test that validation fails when a step has no text after the keyword."""
    content = """Feature: test
  Scenario: test
    Given"""
    result = validate_gherkin(content)
    assert result.valid is False
    assert len(result.errors) > 0
    assert "Step incomplete" in result.errors[0]

def test_validate_gherkin_incomplete_step_with_and():
    """Test incomplete step with And keyword."""
    content = """Feature: test
  Scenario: test
    Given the user is logged in
    And"""
    result = validate_gherkin(content)
    assert result.valid is False
    assert "Step incomplete: 'And'" in result.errors

def test_validate_gherkin_valid_scenario_outline():
    """Test that Scenario Outline with Examples passes validation."""
    content = """Feature: Login
  Scenario Outline: Login with multiple users
    Given the user is on login page
    When the user enters "<username>" and "<password>"
    Then the user sees the dashboard
    Examples:
      | username | password |
      | alice    | secret   |
      | bob      | 1234     |"""
    result = validate_gherkin(content)
    assert result.valid is True