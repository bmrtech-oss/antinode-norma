import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from antinode_norma.cli import cli
from antinode_norma.core import failure_analyzer


@pytest.fixture(autouse=True)
def use_temp_db(monkeypatch, tmp_path):
    monkeypatch.setattr(failure_analyzer, "DB_FILE", tmp_path / "failures.db")
    failure_analyzer._ensure_database()
    yield


def test_learn_command_stores_failures_and_shows_suggestions(monkeypatch, tmp_path):
    report_path = tmp_path / "playwright-report.json"
    spec_path = tmp_path / "generated_tests" / "playwright" / "forgot_password.spec.ts"
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(
        "import { test, expect } from '@playwright/test';\n"
        "test('Forgot password', async ({ page }) => {\n"
        "  await page.locator('text=Forgot password').click();\n"
        "});\n"
    )

    report_path.write_text(
        json.dumps(
            {
                "suites": [
                    {
                        "title": "",
                        "suites": [],
                        "tests": [
                            {
                                "title": "Forgot password",
                                "location": {
                                    "file": str(spec_path),
                                    "line": 3,
                                },
                                "results": [
                                    {
                                        "status": "failed",
                                        "error": "locator.click: waiting for locator('text=Forgot password')",
                                    }
                                ],
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["learn", "--report-file", str(report_path), "--show-suggestions"])

    assert result.exit_code == 0
    assert "Stored 1 failure event(s)" in result.output
    assert "Suggestions for text=Forgot password" in result.output
    assert "Consider using a more robust selector" in result.output
