"""Pytest fixtures and configuration."""

import os
import pytest
from pathlib import Path
from dotenv import load_dotenv
from antinode_norma.core.schemas import UserStory

# Load environment variables once for integration tests
load_dotenv()

# ------------------------------
# Sample stories as fixtures
# ------------------------------


@pytest.fixture
def sample_story_pass() -> str:
    return (
        "As a registered user, I want to reset my password via email so that "
        "I can regain access to my account. Acceptance criteria: "
        "- The system should send a password reset link to the user's registered email. "
        "- The user should be able to click the link and set a new password. "
        "- The system should display an error message when an invalid token is used. "
        "- The system should expire the reset link after 30 minutes."
    )


@pytest.fixture
def sample_story_fail() -> str:
    return "User wants to reset password."


@pytest.fixture
def parsed_story_pass() -> UserStory:
    return UserStory(
        raw_text="",
        role="registered user",
        action="reset password via email",
        benefit="regain access to my account",
        acceptance_criteria=[
            "The system should send a password reset link to the user's registered email.",
            "The user should be able to click the link and set a new password.",
            "The system should display an error message when an invalid token is used.",
            "The system should expire the reset link after 30 minutes.",
        ],
    )


# ------------------------------
# Mock LLM for parser tests
# ------------------------------


@pytest.fixture
def mock_llm_call():
    def _mock(prompt: str) -> str:
        return (
            '{"role": "tester", "action": "test action", "benefit": "test benefit", '
            '"acceptance_criteria": ["criterion one", "criterion two"]}'
        )

    return _mock


# ------------------------------
# Temporary directory for file output
# ------------------------------


@pytest.fixture
def tmp_features(tmp_path):
    """Creates a temporary features/ subdirectory."""
    features = tmp_path / "features"
    features.mkdir()
    return features


# ------------------------------
# Skip markers for missing credentials
# ------------------------------


def has_openrouter_key() -> bool:
    return bool(os.getenv("OPENROUTER_API_KEY"))


def has_jira_creds() -> bool:
    return bool(os.getenv("JIRA_SERVER") and os.getenv("JIRA_TOKEN"))


pytest.mark.integration = pytest.mark.skipif(
    not has_openrouter_key(), reason="OPENROUTER_API_KEY not set"
)
