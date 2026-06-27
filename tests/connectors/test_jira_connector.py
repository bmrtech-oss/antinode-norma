"""Tests for JIRA connector (with mocks and optional real integration)."""

import os
import pytest
from unittest.mock import Mock, patch

from antinode_norma.connectors.jira_connector import (
    fetch_issue,
    fetch_issues,
    comment_on_issue,
    transition_issue,
)


@pytest.mark.skipif(
    not os.getenv("JIRA_SERVER") or not os.getenv("JIRA_TOKEN"),
    reason="JIRA credentials not set",
)
def test_jira_connector_integration():
    # This is a real integration test – requires real JIRA credentials.
    from antinode_norma.connectors import jira_connector

    assert hasattr(jira_connector, "main")
    assert hasattr(jira_connector, "fetch_issue")
    assert hasattr(jira_connector, "comment_on_issue")


@patch("antinode_norma.connectors.jira_connector.JIRA")
def test_jira_fetch_issues_uses_label_filter(MockJIRA):
    mock_jira = Mock()
    issue = Mock()
    issue.key = "JIRA-123"
    issue.fields.summary = "New login flow"
    issue.fields.description = "User should be able to log in."
    issue.fields.labels = ["bdd-ready"]
    issue.fields.status.name = "To Do"
    mock_jira.search_issues.return_value = [issue]
    MockJIRA.return_value = mock_jira

    with patch.dict(
        os.environ, {"JIRA_SERVER": "https://example.atlassian.net", "JIRA_TOKEN": "token"}
    ):
        results = fetch_issues()

    assert mock_jira.search_issues.called
    assert mock_jira.search_issues.call_args.args[0] == "labels = bdd-ready"
    assert results[0]["issue_key"] == "JIRA-123"
    assert results[0]["summary"] == "New login flow"
    assert results[0]["status"] == "To Do"


@patch("antinode_norma.connectors.jira_connector.JIRA")
def test_jira_search_stories_returns_issue_list(MockJIRA):
    from antinode_norma.agent_tools import search_jira_stories

    mock_jira = Mock()
    issue = Mock()
    issue.key = "JIRA-123"
    issue.fields.summary = "New login flow"
    issue.fields.description = "User should be able to log in."
    issue.fields.labels = ["bdd-ready"]
    issue.fields.status.name = "To Do"
    mock_jira.search_issues.return_value = [issue]
    MockJIRA.return_value = mock_jira

    with patch.dict(
        os.environ, {"JIRA_SERVER": "https://example.atlassian.net", "JIRA_TOKEN": "token"}
    ):
        result = search_jira_stories()

    assert result["issues"][0]["issue_key"] == "JIRA-123"


@patch("antinode_norma.connectors.jira_connector.JIRA")
def test_jira_fetch_issue_returns_issue_fields(MockJIRA):
    mock_jira = Mock()
    issue = Mock()
    issue.key = "JIRA-123"
    issue.fields.summary = "Search page"
    issue.fields.description = "As a user, I want search results."
    issue.fields.labels = ["bdd-ready"]
    issue.fields.status.name = "In Progress"
    mock_jira.issue.return_value = issue
    MockJIRA.return_value = mock_jira

    with patch.dict(
        os.environ, {"JIRA_SERVER": "https://example.atlassian.net", "JIRA_TOKEN": "token"}
    ):
        result = fetch_issue("JIRA-123")

    mock_jira.issue.assert_called_once_with("JIRA-123")
    assert result["issue_key"] == "JIRA-123"
    assert result["summary"] == "Search page"
    assert result["status"] == "In Progress"


@patch("antinode_norma.connectors.jira_connector.JIRA")
def test_jira_comment_on_issue_posts_comment(MockJIRA):
    mock_jira = Mock()
    issue = Mock()
    issue.key = "JIRA-123"
    issue.fields.summary = "Login flow"
    issue.fields.description = "As a user, I want to log in."
    mock_comment = Mock()
    mock_comment.id = "10001"
    mock_jira.issue.return_value = issue
    mock_jira.add_comment.return_value = mock_comment
    MockJIRA.return_value = mock_jira

    with patch.dict(
        os.environ, {"JIRA_SERVER": "https://example.atlassian.net", "JIRA_TOKEN": "token"}
    ):
        result = comment_on_issue("JIRA-123", "This is a test comment.")

    mock_jira.issue.assert_called_once_with("JIRA-123")
    mock_jira.add_comment.assert_called_once_with(
        issue, "This is a test comment.")
    assert result["comment_id"] == "10001"
    assert result["status"] == "posted"


@patch("antinode_norma.connectors.jira_connector.JIRA")
def test_jira_transition_issue_applies_transition(MockJIRA):
    mock_jira = Mock()
    issue = Mock()
    issue.key = "JIRA-123"
    mock_jira.issue.return_value = issue
    mock_jira.transitions.return_value = [
        {"id": "31", "name": "Done"},
        {"id": "21", "name": "In Progress"},
    ]
    MockJIRA.return_value = mock_jira

    with patch.dict(
        os.environ, {"JIRA_SERVER": "https://example.atlassian.net", "JIRA_TOKEN": "token"}
    ):
        result = transition_issue("JIRA-123", "Done")

    mock_jira.issue.assert_called_once_with("JIRA-123")
    mock_jira.transition_issue.assert_called_once_with(issue, "31")
    assert result["transition"] == "Done"
    assert result["status"] == "updated"
