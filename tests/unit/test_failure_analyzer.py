import json
from pathlib import Path

import pytest

from antinode_norma.core import failure_analyzer


@pytest.fixture(autouse=True)
def use_temp_db(monkeypatch, tmp_path):
    monkeypatch.setattr(failure_analyzer, "DB_FILE", tmp_path / "failures.db")
    failure_analyzer._ensure_database()
    yield


def test_store_playwright_failures_extracts_selector_and_step_text(tmp_path):
    report_path = tmp_path / "playwright-report.json"
    spec_path = tmp_path / "generated_tests" / "playwright" / "user_login.spec.ts"
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(
        "import { test, expect } from '@playwright/test';\n"
        "import * as steps from './steps/common_steps';\n\n"
        "test('User Login', async ({ page }) => {\n"
        "  await steps.fillField(page, '#email', 'testuser@example.com');\n"
        "});\n"
    )

    report_path.write_text(
        json.dumps({
            "suites": [
                {
                    "title": "",
                    "suites": [],
                    "tests": [
                        {
                            "title": "User Login › Successful login",
                            "location": {
                                "file": str(spec_path),
                                "line": 5,
                            },
                            "results": [
                                {
                                    "status": "failed",
                                    "error": "locator.fill: Test timeout of 30000ms exceeded. waiting for locator('#email')",
                                }
                            ],
                        }
                    ],
                }
            ]
        }),
        encoding="utf-8",
    )

    events = failure_analyzer.store_playwright_failures(report_path)
    assert len(events) == 1
    event = events[0]
    assert event.selector == "#email"
    assert "steps.fillField" in (event.step_text or "")
    assert event.test_title == "User Login › Successful login"

    examples = failure_analyzer.get_failure_examples_for_step("When I fill 'testuser@example.com' into '#email'")
    assert len(examples) == 1
    assert examples[0].selector == "#email"


def test_get_recent_failures_returns_stored_records(tmp_path):
    report_path = tmp_path / "playwright-report.json"
    report_path.write_text(
        json.dumps({
            "tests": [
                {
                    "title": "Forgot password",
                    "results": [
                        {
                            "status": "failed",
                            "error": "locator.click: waiting for locator('text=Forgot password')",
                        }
                    ],
                }
            ]
        }),
        encoding="utf-8",
    )

    failure_analyzer.store_playwright_failures(report_path)
    recent = failure_analyzer.get_recent_failures(limit=5)
    assert len(recent) == 1
    assert recent[0].test_title == "Forgot password"
    assert recent[0].selector == "text=Forgot password"


def test_get_failure_suggestions_for_step_returns_fix_recommendations(tmp_path):
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
        json.dumps({
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
        }),
        encoding="utf-8",
    )

    failure_analyzer.store_playwright_failures(report_path)
    suggestions = failure_analyzer.get_failure_suggestions_for_step("When I click on \"text=Forgot password\"")

    assert len(suggestions) == 1
    assert "Consider using a more robust selector" in suggestions[0]
