import os
import requests
from typing import Any, Dict, List, Optional


class TestRailError(Exception):
    pass


def get_testrail_session() -> requests.Session:
    base_url = os.getenv("TESTRAIL_URL")
    username = os.getenv("TESTRAIL_USER")
    api_token = os.getenv("TESTRAIL_TOKEN")
    if not base_url or not username or not api_token:
        raise EnvironmentError(
            "TESTRAIL_URL, TESTRAIL_USER and TESTRAIL_TOKEN must be set to use TestRail."
        )
    session = requests.Session()
    session.auth = (username, api_token)
    session.headers.update({"Content-Type": "application/json"})
    return session


def _api_url(endpoint: str) -> str:
    base_url = os.getenv("TESTRAIL_URL")
    if not base_url:
        raise EnvironmentError("TESTRAIL_URL must be set to use TestRail.")
    return f"{base_url.rstrip('/')}/index.php?/api/v2/{endpoint.lstrip('/')}"


def add_test_case(
    section_id: int,
    title: str,
    description: str = "",
    case_type: int = 1,
    priority_id: int = 2,
) -> Dict[str, Any]:
    """Create a new TestRail test case under a section."""
    if not section_id or not title:
        raise ValueError("section_id and title are required.")
    session = get_testrail_session()
    payload = {
        "title": title,
        "template_id": case_type,
        "priority_id": priority_id,
        "custom_expected": description,
    }
    response = session.post(
        _api_url(f"add_case/{section_id}"), json=payload, timeout=30
    )
    if not response.ok:
        raise TestRailError(f"Failed to add test case: {response.text}")
    return response.json()


def add_test_result(test_id: int, status_id: int, comment: str = "") -> Dict[str, Any]:
    """Add a result to a TestRail test case."""
    if not test_id or not status_id:
        raise ValueError("test_id and status_id are required.")
    session = get_testrail_session()
    payload = {"status_id": status_id, "comment": comment}
    response = session.post(_api_url(f"add_result/{test_id}"), json=payload, timeout=30)
    if not response.ok:
        raise TestRailError(f"Failed to add test result: {response.text}")
    return response.json()


def create_test_run(
    project_id: int,
    suite_id: int,
    name: str,
    description: str = "",
    include_all: bool = True,
    case_ids: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """Create a TestRail test run."""
    if not project_id or not suite_id or not name:
        raise ValueError("project_id, suite_id and name are required.")
    session = get_testrail_session()
    payload = {
        "suite_id": suite_id,
        "name": name,
        "description": description,
        "include_all": include_all,
    }
    if case_ids:
        payload["case_ids"] = case_ids
    response = session.post(_api_url(f"add_run/{project_id}"), json=payload, timeout=30)
    if not response.ok:
        raise TestRailError(f"Failed to create test run: {response.text}")
    return response.json()
