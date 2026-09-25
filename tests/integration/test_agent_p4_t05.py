from antinode_norma.core.agent import NormaAgent
from antinode_norma.core.types import TestCase


def test_agent_repair_loop_recovers_from_traceability_failure():
    responses = iter(
        [
            """
Feature: Login
  Scenario: Valid login
    Given the user is on the login page
    When the user submits credentials
    Then the user sees the dashboard
""",
            """
@TC-101
Feature: Login
  Scenario: Valid login
    Given the user is on the login page
    When the user submits credentials
    Then the user sees the dashboard
""",
        ]
    )

    agent = NormaAgent(llm_callable=lambda _: next(responses))
    test_case = TestCase(id="TC-101", title="Valid login")

    gherkin, verdict, attempts = agent.generate_feature_with_repair([test_case])

    assert attempts == 2
    assert "@TC-101" in gherkin
    assert verdict.hard_pass is True
