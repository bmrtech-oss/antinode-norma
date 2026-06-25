from pathlib import Path
from unittest.mock import patch
from antinode_norma.core.schemas import UserStory
from antinode_norma.agent_tools import generate_feature


def test_generate_feature_from_raw_text(tmp_path):
    story = UserStory(
        raw_text="As a user, I want to reset my password so that I can regain access.",
        role="registered user",
        action="reset password",
        benefit="regain access",
        acceptance_criteria=["The system sends a reset email."],
    )

    with (
        patch("antinode_norma.agent_tools.parse_story", return_value=story),
        patch(
            "antinode_norma.agent_tools.create_llm_callable",
            return_value=lambda prompt: "feature content",
        ),
        patch(
            "antinode_norma.agent_tools.generate_gherkin",
            return_value="Feature: Reset password\nScenario: Reset password\n  Given ...",
        ),
        patch("antinode_norma.agent_tools.validate_gherkin") as mock_validate,
        patch("antinode_norma.agent_tools.write_feature_file") as mock_write,
    ):
        mock_validate.return_value.valid = True
        mock_validate.return_value.errors = []

        result = generate_feature(raw_text=story.raw_text, output_dir=str(tmp_path))

    assert result["feature_path"].startswith(str(tmp_path))
    assert result["validation_passed"] is True
    mock_write.assert_called_once()


def test_generate_feature_returns_error_without_story():
    result = generate_feature()
    assert "error" in result
    assert "No story text provided" in result["error"]


def test_generate_feature_from_story_dict(tmp_path):
    story_dict = {
        "raw_text": "As a shopper, I want to search products so that I can find items.",
        "role": "shopper",
        "action": "search products",
        "benefit": "find items",
        "acceptance_criteria": ["Search results show matching products."],
    }

    with (
        patch(
            "antinode_norma.agent_tools.create_llm_callable",
            return_value=lambda prompt: "feature content",
        ),
        patch(
            "antinode_norma.agent_tools.generate_gherkin",
            return_value="Feature: Search products\nScenario: Search products\n  Given ...",
        ),
        patch("antinode_norma.agent_tools.validate_gherkin") as mock_validate,
        patch("antinode_norma.agent_tools.write_feature_file") as mock_write,
    ):
        mock_validate.return_value.valid = True
        mock_validate.return_value.errors = []

        result = generate_feature(story=story_dict, output_dir=str(tmp_path))

    assert result["feature_path"].startswith(str(tmp_path))
    assert result["validation_passed"] is True
    mock_write.assert_called_once()
