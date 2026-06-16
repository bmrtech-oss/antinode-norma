"""Unit tests for story parser (uses mock LLM)."""

from antinode_norma.core.parser import parse_story

def test_parse_story_uses_llm_call(mock_llm_call):
    raw = "As a tester, I want to test so that I learn."
    story = parse_story(raw, mock_llm_call)
    assert story.role == "tester"
    assert story.action == "test action"
    assert story.benefit == "test benefit"
    assert story.acceptance_criteria == ["criterion one", "criterion two"]