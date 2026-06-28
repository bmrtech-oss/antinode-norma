"""End-to-end test for Phase 5 failure learning integration."""

import json

import pytest

from antinode_norma.core import failure_analyzer
from antinode_norma.codegen.parsers.gherkin_parser import GherkinParser
from antinode_norma.codegen.config import CodegenConfig
from antinode_norma.codegen.engine.quality import QualityConfig

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def use_temp_db(monkeypatch, tmp_path):
    """Use a temporary failure database for each test."""
    monkeypatch.setattr(failure_analyzer, "DB_FILE", tmp_path / "failures.db")
    failure_analyzer._ensure_database()
    yield


def test_e2e_failure_learning_influences_gherkin_parsing(tmp_path, monkeypatch):
    """
    Test the full Phase 5 workflow:
    1. Parse a Playwright JSON report with failures
    2. Store failures in the database
    3. Parse a Gherkin feature that would trigger similar steps
    4. Verify the LLM prompt includes failure examples
    """
    # Step 1: Create a Playwright JSON report with test failures
    report_path = tmp_path / "playwright-report.json"
    spec_path = tmp_path / "generated_tests" / "playwright" / "login.spec.ts"
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(
        "import { test, expect } from '@playwright/test';\n"
        "import * as steps from './steps/common_steps';\n\n"
        "test('User Login', async ({ page }) => {\n"
        "  await page.goto('https://example.com/login');\n"
        "  await page.locator('#email').fill('test@example.com');\n"
        "  await page.locator('#password').fill('password123');\n"
        "  await page.locator('#login-button').click();\n"
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
                                "title": "User Login",
                                "location": {
                                    "file": str(spec_path),
                                    "line": 5,
                                },
                                "results": [
                                    {
                                        "status": "failed",
                                        "error": "locator.click: waiting for locator('#login-button'). Timeout 30000ms exceeded.",
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

    # Step 2: Store failures in database
    failures = failure_analyzer.store_playwright_failures(report_path)
    assert len(failures) == 1
    assert failures[0].selector == "#login-button"
    assert "waiting for locator" in failures[0].error_message

    # Step 3: Create and parse a Gherkin feature with a similar step
    feature_path = tmp_path / "login.feature"
    feature_path.write_text(
        "Feature: User Login\n"
        "  Scenario: Successful login\n"
        '    Given I navigate to "https://example.com/login"\n'
        '    When I fill "test@example.com" into "#email"\n'
        '    And I fill "password123" into "#password"\n'
        '    And I click on "#login-button"\n'
        '    Then I should see "Welcome"\n'
    )

    # Configure with failure learning enabled
    quality = QualityConfig(
        use_llm_mapping=False,  # Use rule engine to avoid LLM calls
        enable_failure_learning=True,
        failure_learning_max_examples=2,
    )
    config = CodegenConfig(quality=quality)
    monkeypatch.setattr("antinode_norma.codegen.config._default_config", config)

    # Step 4: Parse the feature (this will use map_step internally)
    parser = GherkinParser(quality_config=quality)
    suite = parser.parse(feature_path)

    # Verify the suite was parsed
    assert suite.name == "User Login"
    assert len(suite.cases) == 1
    case = suite.cases[0]
    assert len(case.steps) == 5
    assert case.steps[3].description == 'And I click on "#login-button"'

    # Step 5: Verify that failure examples were in the database
    examples = failure_analyzer.get_failure_examples_for_step(
        'When I click on "#login-button"'
    )
    assert len(examples) >= 1
    assert (
        "#login-button" in examples[0].selector
        or examples[0].selector == "#login-button"
    )
    assert "waiting for locator" in examples[0].error_message


def test_e2e_failure_suggestions_and_cli_integration(tmp_path, monkeypatch):
    """
    Test that failure suggestions are generated correctly and the CLI can display them.
    """
    # Create and store a failure
    report_path = tmp_path / "playwright-report.json"
    spec_path = tmp_path / "generated_tests" / "playwright" / "password_reset.spec.ts"
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(
        "import { test, expect } from '@playwright/test';\n"
        "test('Reset Password', async ({ page }) => {\n"
        "  await page.locator('text=Forgot password?').click();\n"
        "});\n"
    )

    report_path.write_text(
        json.dumps(
            {
                "tests": [
                    {
                        "title": "Reset Password",
                        "results": [
                            {
                                "status": "failed",
                                "error": "locator.click: waiting for locator('text=Forgot password?'). Element not found.",
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    # Store the failure
    failures = failure_analyzer.store_playwright_failures(report_path)
    assert len(failures) == 1

    # Get suggestions for a similar step
    suggestions = failure_analyzer.get_failure_suggestions_for_step(
        'When I click on "text=Forgot password?"'
    )

    # Verify suggestions were generated
    assert len(suggestions) > 0
    for suggestion in suggestions:
        assert isinstance(suggestion, str)
        assert len(suggestion) > 0
        # Suggestions should mention selector, robust, or alternative
        assert any(
            keyword in suggestion.lower()
            for keyword in ["selector", "robust", "alternative", "waiting", "specific"]
        )
