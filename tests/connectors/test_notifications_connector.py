import pytest
from unittest.mock import Mock, patch

from antinode_norma.connectors.notifications import post_slack_message, post_teams_message


@patch("antinode_norma.connectors.notifications.requests.post")
def test_post_slack_message_sends_payload(MockPost):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "ok"
    mock_response.raise_for_status.return_value = None
    MockPost.return_value = mock_response

    result = post_slack_message("https://hooks.slack.com/services/T/123/abc", "Hello world")

    MockPost.assert_called_once()
    assert result["status"] == "sent"
    assert result["response_code"] == 200


@patch("antinode_norma.connectors.notifications.requests.post")
def test_post_teams_message_sends_payload(MockPost):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "ok"
    mock_response.raise_for_status.return_value = None
    MockPost.return_value = mock_response

    result = post_teams_message(
        "https://outlook.office.com/webhook/foo", "Build Result", "All tests passed"
    )

    MockPost.assert_called_once()
    assert result["status"] == "sent"
    assert result["response_code"] == 200
