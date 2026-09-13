from antinode_norma.core.types import TestCase
from antinode_norma.core.agent import NormaAgent


def test_norma_agent_single_generation():
    def mock_llm(prompt: str) -> str:
        return """
@TC-101
Feature: User Login
  Scenario: Login with valid credentials
    Given the user opens the login page
    When the user enters valid credentials
    Then the user sees the dashboard
"""

    tc = TestCase(
        id="TC-101",
        title="Login with valid credentials",
        role="user",
        action="log in",
        benefit="access my dashboard",
    )

    agent = NormaAgent(llm_callable=mock_llm)
    gherkin, verdict = agent.generate_feature([tc])

    assert "Feature: User Login" in gherkin
    assert verdict.hard_pass is True
    assert verdict.summary == "PASS"
    assert "Q0" in verdict.gate_results
    assert verdict.gate_results["Q0"].passed is True
    assert verdict.gate_results["Q3"].passed is True
