"""
Unit tests for Phase 12 Task P12-T04: Release provision verification.
"""

from pathlib import Path
import yaml
from fastapi.testclient import TestClient

import antinode_norma
from antinode_norma.server.api import app


def test_package_version_consistency():
    assert antinode_norma.__version__ == "0.1.0-alpha"

    pyproject_text = Path("pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.1.0-alpha"' in pyproject_text

    setup_text = Path("setup.py").read_text(encoding="utf-8")
    assert 'version="0.1.0-alpha"' in setup_text


def test_api_health_version():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0-alpha"


def test_release_workflow_configuration():
    workflow_path = Path(".github/workflows/release.yml")
    assert workflow_path.exists(), ".github/workflows/release.yml does not exist."

    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    assert workflow["name"] == "Release"

    on_section = workflow.get("on") or workflow.get(True)
    assert on_section is not None, "Missing 'on' section in release workflow."

    # Check triggers
    push_triggers = on_section["push"]["tags"]
    assert "v*" in push_triggers
    assert "[0-9]*" in push_triggers

    # Check job steps contain build and gh-release
    steps = workflow["jobs"]["test-and-build"]["steps"]
    step_uses = [s.get("uses", "") for s in steps]
    assert any("action-gh-release" in u for u in step_uses)
    assert any("python -m build" in s.get("run", "") for s in steps)
