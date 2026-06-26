"""Unit tests for Pydantic schemas."""

import pytest
from antinode_norma.core.schemas import UserStory


def test_user_story_requires_acceptance_criteria():
    with pytest.raises(ValueError):
        UserStory(role="r", action="a", benefit="b", acceptance_criteria=[])


def test_user_story_defaults_dependencies_to_empty_list():
    story = UserStory(role="r", action="a", benefit="b", acceptance_criteria=["c1"])
    assert story.dependencies == []


def test_user_story_handles_null_dependencies():
    story = UserStory(
        role="r", action="a", benefit="b", acceptance_criteria=["c1"], dependencies=None
    )
    assert story.dependencies == []


def test_user_story_story_id_is_optional():
    story = UserStory(role="r", action="a", benefit="b", acceptance_criteria=["c1"])
    assert story.story_id is None


def test_user_story_raw_text_is_optional():
    story = UserStory(role="r", action="a", benefit="b", acceptance_criteria=["c1"])
    assert story.raw_text == ""
