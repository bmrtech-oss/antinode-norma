import json

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
    result = runner.invoke(
        cli, ["learn", "--report-file", str(report_path), "--show-suggestions"]
    )

    assert result.exit_code == 0
    assert "Stored 1 failure event(s)" in result.output
    assert "Suggestions for text=Forgot password" in result.output
    assert "Consider using a more robust selector" in result.output


def test_init_creates_norma_config(tmp_path, monkeypatch):
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    input_text = """openrouter
playwright
generated_tests
y
n
y
prettier
"""
    result = runner.invoke(cli, ["init"], input=input_text)

    assert result.exit_code == 0
    config_path = tmp_path / "norma.config.yml"
    assert config_path.exists()

    content = config_path.read_text(encoding="utf-8")
    assert "llm_provider: openrouter" in content
    assert "default_framework: playwright" in content
    assert "output_dir: generated_tests" in content
    assert "use_page_objects: true" in content
    assert "generate_step_defs: false" in content
    assert "run_formatter: true" in content
    assert "formatter_tool: prettier" in content


def test_init_force_overwrites_existing_config(tmp_path, monkeypatch):
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    config_path = tmp_path / "norma.config.yml"
    config_path.write_text("llm_provider: openai\n")

    input_text = """anthropic
selenium
out_tests
n
y
n
ruff
"""
    result = runner.invoke(cli, ["init", "--force"], input=input_text)

    assert result.exit_code == 0
    content = config_path.read_text(encoding="utf-8")
    assert "llm_provider: anthropic" in content
    assert "default_framework: selenium" in content
    assert "output_dir: out_tests" in content
    assert "use_page_objects: false" in content
    assert "generate_step_defs: true" in content
    assert "run_formatter: false" in content
    assert "formatter_tool: ruff" in content


def test_parse_show_mapping_decisions_writes_summary_and_debug_log(tmp_path, monkeypatch):
    feature_path = tmp_path / "sample.feature"
    feature_path.write_text(
        """Feature: Login\n  Scenario: Valid login\n    Given I open \"https://example.com\"\n    When I click \"#login-button\"\n""",
        encoding="utf-8",
    )

    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        cli,
        ["parse", str(feature_path), "--show-mapping-decisions"],
    )

    assert result.exit_code == 0
    assert "Input text" in result.output
    assert "Selected mapping" in result.output
    assert "Reason" in result.output
    assert (tmp_path / ".antinode_norma_mapping_decisions.jsonl").exists()
