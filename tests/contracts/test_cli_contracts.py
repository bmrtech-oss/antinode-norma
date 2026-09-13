from click.testing import CliRunner
from antinode_norma.cli import cli


def test_cli_contract_commands_exist():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0

    expected_commands = [
        "generate",
        "agent",
        "jira-search",
        "jira-comment",
        "jira-transition",
        "jira-status",
        "testrail-case",
        "testrail-result",
        "notify-slack",
        "notify-teams",
        "learn",
        "completion",
        "parse",
        "serve",
        "init",
    ]
    for cmd in expected_commands:
        assert cmd in result.output, f"Missing CLI command contract: {cmd}"


def test_cli_contract_generate_options():
    runner = CliRunner()
    result = runner.invoke(cli, ["generate", "--help"])
    assert result.exit_code == 0
    assert "--file" in result.output
    assert "--output-dir" in result.output
    assert "--quality-only" in result.output
    assert "--dry-run" in result.output
    assert "--interactive" in result.output
