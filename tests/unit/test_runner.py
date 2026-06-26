"""Unit tests for the runner orchestration logic."""

import pytest
from unittest.mock import patch
from antinode_norma.runner import run_agent_from_raw
from antinode_norma.core.schemas import UserStory, QualityReport


@pytest.mark.asyncio
async def test_run_agent_from_raw_quality_only():
    """Test the quality-only flag returns the report without generating."""
    story = UserStory(
        role="tester",
        action="test",
        benefit="learn",
        acceptance_criteria=["should pass"],
    )
    with (
        patch("antinode_norma.runner.parse_story", return_value=story),
        patch("antinode_norma.runner.compute_quality") as mock_quality,
    ):
        mock_quality.return_value = QualityReport(
            passes_invest=True,
            invest_details={},
            issues=[],
            suggestions=[],
            quality_score=0.9,
        )
        result = await run_agent_from_raw("raw", quality_only=True)
        assert result["quality_score"] == 0.9
        assert result["passes_invest"] is True
        assert "feature_path" not in result


@pytest.mark.asyncio
async def test_run_agent_from_raw_generation():
    """Test the full generation flow with mocks."""
    story = UserStory(
        role="tester",
        action="test",
        benefit="learn",
        acceptance_criteria=["should pass"],
    )
    mock_report = QualityReport(
        passes_invest=True,
        invest_details={},
        issues=[],
        suggestions=[],
        quality_score=1.0,
    )
    with (
        patch("antinode_norma.runner.parse_story", return_value=story),
        patch("antinode_norma.runner.compute_quality", return_value=mock_report),
        patch("antinode_norma.runner.get_step_definitions", return_value=["Given a step"]),
        patch(
            "antinode_norma.runner.generate_gherkin",
            return_value="Feature: test\nScenario: test\nGiven something",
        ),
        patch("antinode_norma.runner.validate_gherkin") as mock_validate,
        patch("antinode_norma.runner.write_feature_file") as mock_write,
    ):
        mock_validate.return_value.valid = True
        mock_validate.return_value.errors = []
        result = await run_agent_from_raw("raw")
        assert result["feature_path"] is not None
        assert result["validation_passed"] is True
        mock_write.assert_called_once()


@pytest.mark.asyncio
async def test_run_agent_from_raw_fails_quality():
    """Test that the runner returns an error when quality fails."""
    story = UserStory(role="tester", action="test", benefit="learn", acceptance_criteria=["vague"])
    mock_report = QualityReport(
        passes_invest=False,
        invest_details={"testable": False},
        issues=["testable"],
        suggestions=["be more clear"],
        quality_score=0.5,
    )
    with (
        patch("antinode_norma.runner.parse_story", return_value=story),
        patch("antinode_norma.runner.compute_quality", return_value=mock_report),
    ):
        result = await run_agent_from_raw("raw")
        assert "error" in result
        assert "Quality check failed" in result["error"]
        assert "issues" in result


@pytest.mark.asyncio
async def test_run_agent_from_raw_gherkin_validation_fails():
    """Test that runner returns error when Gherkin validation fails."""
    story = UserStory(
        role="tester",
        action="test",
        benefit="learn",
        acceptance_criteria=["should pass"],
    )
    mock_report = QualityReport(
        passes_invest=True,
        invest_details={},
        issues=[],
        suggestions=[],
        quality_score=1.0,
    )
    with (
        patch("antinode_norma.runner.parse_story", return_value=story),
        patch("antinode_norma.runner.compute_quality", return_value=mock_report),
        patch("antinode_norma.runner.get_step_definitions", return_value=["Given a step"]),
        patch("antinode_norma.runner.generate_gherkin", return_value="bad gherkin"),
        patch("antinode_norma.runner.validate_gherkin") as mock_validate,
    ):
        mock_validate.return_value.valid = False
        mock_validate.return_value.errors = ["Missing Feature"]
        result = await run_agent_from_raw("raw")
        assert "error" in result
        assert "validation failed" in result["error"].lower()
        assert "errors" in result
