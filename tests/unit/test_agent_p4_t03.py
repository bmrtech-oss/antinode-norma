from antinode_norma.core.types import TestCase
from antinode_norma.core.agent import NormaAgent


def test_repair_loop_passes_first_attempt():
    def mock_llm(prompt: str) -> str:
        return """
@TC-101
Feature: Login
  Scenario: Valid login
    Given user is on login page
    When user submits credentials
    Then user sees home
"""

    tc = TestCase(id="TC-101", title="Valid login")
    agent = NormaAgent(llm_callable=mock_llm)
    gherkin, verdict, attempts = agent.generate_feature_with_repair([tc])

    assert attempts == 1
    assert verdict.hard_pass is True


def test_repair_loop_passes_second_attempt():
    calls = 0
    captured_prompts = []

    def mock_llm(prompt: str) -> str:
        nonlocal calls
        calls += 1
        captured_prompts.append(prompt)
        if calls == 1:
            # Missing @TC-101 tag
            return """
Feature: Login
  Scenario: Valid login
    Given user is on login page
"""
        else:
            # Corrected with tag
            return """
@TC-101
Feature: Login
  Scenario: Valid login
    Given user is on login page
"""

    tc = TestCase(id="TC-101", title="Valid login")
    agent = NormaAgent(llm_callable=mock_llm)
    gherkin, verdict, attempts = agent.generate_feature_with_repair([tc])

    assert attempts == 2
    assert verdict.hard_pass is True
    assert "PREVIOUS EVALUATION FEEDBACK" in captured_prompts[1]


def test_repair_loop_exhausts_attempts():
    def mock_llm(prompt: str) -> str:
        return "Invalid content without feature keyword"

    tc = TestCase(id="TC-101", title="Valid login")
    agent = NormaAgent(llm_callable=mock_llm)
    gherkin, verdict, attempts = agent.generate_feature_with_repair([tc], max_attempts=3)

    assert attempts == 3
    assert verdict.hard_pass is False
