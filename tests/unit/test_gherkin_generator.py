"""Unit tests for Gherkin generator (uses mock LLM)."""

from antinode_norma.core.gherkin_generator import generate_gherkin
from antinode_norma.core.schemas import UserStory


def test_generate_gherkin_calls_llm(mock_llm_call):
    story = UserStory(
        role="user",
        action="reset password",
        benefit="access",
        acceptance_criteria=["c1"],
    )
    step_defs = ["Given the user is on login page"]
    result = generate_gherkin(story, step_defs, mock_llm_call)
    assert isinstance(result, str)


def test_generate_gherkin_prompt_content():
    # Test that the prompt includes story details by capturing it
    story = UserStory(role="tester", action="test", benefit="learn", acceptance_criteria=["c1"])
    step_defs = ["Given a"]
    recorded_prompt = None

    def mock_llm(prompt):
        nonlocal recorded_prompt
        recorded_prompt = prompt
        return "feature content"

    generate_gherkin(story, step_defs, mock_llm)
    assert "tester" in recorded_prompt
    assert "test" in recorded_prompt
    assert "c1" in recorded_prompt
