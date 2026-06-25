import os
import pytest
from unittest.mock import Mock, patch

from antinode_norma.connectors.testrail_connector import add_test_case, add_test_result, create_test_run


@patch("antinode_norma.connectors.testrail_connector.requests.Session")
def test_add_test_case_posts_payload(MockSession):
    mock_session = Mock()
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {"id": 123, "title": "Example case"}
    mock_session.post.return_value = mock_response
    MockSession.return_value = mock_session

    with patch.dict(
        os.environ,
        {"TESTRAIL_URL": "https://testrail.example.com", "TESTRAIL_USER": "user", "TESTRAIL_TOKEN": "token"},
    ):
        result = add_test_case(101, "Login test", "Verify login flow")

    mock_session.post.assert_called_once()
    assert result["id"] == 123


@patch("antinode_norma.connectors.testrail_connector.requests.Session")
def test_add_test_result_posts_payload(MockSession):
    mock_session = Mock()
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {"id": 555, "status_id": 1}
    mock_session.post.return_value = mock_response
    MockSession.return_value = mock_session

    with patch.dict(
        os.environ,
        {"TESTRAIL_URL": "https://testrail.example.com", "TESTRAIL_USER": "user", "TESTRAIL_TOKEN": "token"},
    ):
        result = add_test_result(222, 1, "Passed")

    mock_session.post.assert_called_once()
    assert result["status_id"] == 1


@patch("antinode_norma.connectors.testrail_connector.requests.Session")
def test_create_test_run_posts_payload(MockSession):
    mock_session = Mock()
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {"id": 10, "name": "Daily run"}
    mock_session.post.return_value = mock_response
    MockSession.return_value = mock_session

    with patch.dict(
        os.environ,
        {"TESTRAIL_URL": "https://testrail.example.com", "TESTRAIL_USER": "user", "TESTRAIL_TOKEN": "token"},
    ):
        result = create_test_run(1, 2, "Daily run", "Daily smoke suite")

    mock_session.post.assert_called_once()
    assert result["name"] == "Daily run"
