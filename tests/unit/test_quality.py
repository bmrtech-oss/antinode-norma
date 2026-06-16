"""Unit tests for INVEST quality checks."""

import pytest
from antinode_norma.core.quality import (
    is_independent, is_negotiable, is_valuable,
    is_estimable, is_small, is_testable, compute_quality
)
from antinode_norma.core.schemas import UserStory

class TestInvestChecks:
    def test_is_independent(self):
        story = UserStory(role="u", action="a", benefit="b", acceptance_criteria=["c1"])
        # Default dependencies empty list
        assert is_independent(story) is True
        story.dependencies = ["dep1", "dep2"]
        assert is_independent(story) is True
        story.dependencies = ["dep1", "dep2", "dep3"]
        assert is_independent(story) is False

    def test_is_negotiable(self):
        story = UserStory(role="u", action="a", benefit="b", acceptance_criteria=["should update SQL database"])
        assert is_negotiable(story) == "needs_review"
        story.acceptance_criteria = ["should display the result"]
        assert is_negotiable(story) is True

    def test_is_valuable(self):
        story = UserStory(role="u", action="a", benefit="benefit", acceptance_criteria=["c1"])
        assert is_valuable(story) is True
        story.benefit = "call the API"
        assert is_valuable(story) is False

    def test_is_estimable(self):
        story = UserStory(role="u", action="a", benefit="b", acceptance_criteria=["clear step"])
        assert is_estimable(story) is True
        story.acceptance_criteria = ["handle various cases"]
        assert is_estimable(story) is False

    def test_is_small(self):
        story = UserStory(role="u", action="a", benefit="b", acceptance_criteria=["c1", "c2", "c3", "c4", "c5"])
        assert is_small(story) is True
        story.acceptance_criteria = ["c1", "c2", "c3", "c4", "c5", "c6"]
        assert is_small(story) is False
        story.estimated_points = 8
        assert is_small(story) is True
        story.estimated_points = 13
        assert is_small(story) is False

    def test_is_testable(self):
        story = UserStory(role="u", action="a", benefit="b", acceptance_criteria=["should return 200"])
        assert is_testable(story) is True
        story.acceptance_criteria = ["click the button"]
        assert is_testable(story) is False

    def test_compute_quality(self):
        story = UserStory(
            role="u", action="a", benefit="benefit",
            acceptance_criteria=["should display X", "should return Y"]
        )
        report = compute_quality(story)
        assert report.passes_invest is True
        assert report.quality_score == 1.0
        # Make it fail testable
        story.acceptance_criteria = ["click", "receive"]
        report = compute_quality(story)
        assert report.passes_invest is False
        assert report.quality_score < 1.0
        assert "testable" in report.issues[0]