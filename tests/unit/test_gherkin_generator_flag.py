from antinode_norma.core.schemas import UserStory
from antinode_norma.core.gherkin_generator import generate_gherkin


def test_generate_gherkin_flag_disabled(monkeypatch):
    monkeypatch.setenv("NORMA_FEATURE_UNIFIED_AGENT", "false")

    mock_llm_called = False

    def mock_llm(prompt: str) -> str:
        nonlocal mock_llm_called
        mock_llm_called = True
        assert "Analyze the story below and the acceptance criteria" in prompt
        return "Feature: Legacy\n\nScenario: Test\n  Given step"

    story = UserStory(
        role="tester",
        action="run test",
        benefit="verify system",
        acceptance_criteria=["Criterion 1"],
    )

    result = generate_gherkin(story, [], mock_llm)
    assert mock_llm_called is True
    assert "Feature: Legacy" in result


def test_generate_gherkin_flag_enabled(monkeypatch):
    monkeypatch.setenv("NORMA_FEATURE_UNIFIED_AGENT", "true")

    mock_llm_called = False

    def mock_llm(prompt: str) -> str:
        nonlocal mock_llm_called
        mock_llm_called = True
        return """
@TC-101
Feature: Unified Agent
  Scenario: Test unified agent
    Given step 1
"""

    story = UserStory(
        role="tester",
        action="run test",
        benefit="verify system",
        acceptance_criteria=["Criterion 1"],
    )

    result = generate_gherkin(story, [], mock_llm)
    assert mock_llm_called is True
    assert "Feature: Unified Agent" in result
