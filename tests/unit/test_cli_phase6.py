"""Tests for Phase 6 CLI and UX improvements."""

from click.testing import CliRunner
from antinode_norma.cli import cli
from unittest.mock import patch


class TestCLIOutput:
    """Test improved CLI output with color-coded messages."""

    def test_cli_help_shows_examples(self):
        """Verify help text includes usage examples."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Quick start:" in result.output
        assert "anorm generate" in result.output
        assert "anorm learn" in result.output

    def test_generate_command_help_shows_examples(self):
        """Verify generate command help has multiple examples."""
        runner = CliRunner()
        result = runner.invoke(cli, ["generate", "--help"])
        assert result.exit_code == 0
        assert "Examples:" in result.output
        assert "--dry-run" in result.output
        assert "--interactive" in result.output

    def test_learn_command_help_shows_examples(self):
        """Verify learn command help has usage examples."""
        runner = CliRunner()
        result = runner.invoke(cli, ["learn", "--help"])
        assert result.exit_code == 0
        assert "Examples:" in result.output
        assert "--show-suggestions" in result.output
        assert "--db-file" in result.output


class TestCLIDryRun:
    """Test --dry-run mode."""

    @patch("antinode_norma.cli.run_agent_from_raw")
    def test_generate_dry_run_shows_what_would_be_written(self, mock_run):
        """Verify dry-run shows target file without writing."""
        mock_run.return_value = {
            "feature_path": "features/test_feature.feature",
            "quality_score": 0.9,
            "passes_invest": True,
        }

        runner = CliRunner()
        result = runner.invoke(cli, ["generate", "As a user, I want to log in", "--dry-run"])

        assert result.exit_code == 0
        assert "Dry-run mode" in result.output
        assert "Would write to" in result.output
        assert "features/test_feature.feature" in result.output

    def test_generate_without_story_shows_helpful_error(self):
        """Verify helpful error when no story is provided."""
        runner = CliRunner()
        result = runner.invoke(cli, ["generate"])
        assert result.exit_code == 1
        assert "No story provided" in result.output
        assert "Run 'anorm generate --help'" in result.output


class TestCLIInteractiveMode:
    """Test --interactive mode options."""

    def test_generate_interactive_flag_accepted(self):
        """Verify interactive flag is recognized."""
        runner = CliRunner()
        result = runner.invoke(cli, ["generate", "--help"])
        assert result.exit_code == 0
        assert "--interactive" in result.output

    @patch("antinode_norma.cli.run_agent_from_raw")
    def test_generate_interactive_retry_prompt(self, mock_run):
        """Verify interactive retry flow asks for corrected story text."""
        mock_run.side_effect = [
            {"error": "Quality check failed", "issues": ["too vague"]},
            {"feature_path": "features/retry.feature", "validation_passed": True},
        ]
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["generate", "As a user, I want to log in", "--interactive"],
            input="y\nAs a user, I want to log in with valid credentials\n",
        )
        assert result.exit_code == 0
        assert "Interactive mode is enabled" in result.output
        assert "Feature file written" in result.output


class TestUIModule:
    """Test UI utilities module."""

    def test_success_message_imports(self):
        """Verify success_message function exists."""
        from antinode_norma.utils.ui import success_message

        assert callable(success_message)

    def test_error_message_imports(self):
        """Verify error_message function exists."""
        from antinode_norma.utils.ui import error_message

        assert callable(error_message)

    def test_warning_message_imports(self):
        """Verify warning_message function exists."""
        from antinode_norma.utils.ui import warning_message

        assert callable(warning_message)

    def test_info_message_imports(self):
        """Verify info_message function exists."""
        from antinode_norma.utils.ui import info_message

        assert callable(info_message)

    def test_section_header_imports(self):
        """Verify section_header function exists."""
        from antinode_norma.utils.ui import section_header

        assert callable(section_header)

    def test_progress_bar_imports(self):
        """Verify progress_bar function exists."""
        from antinode_norma.utils.ui import progress_bar

        assert callable(progress_bar)

    def test_error_context_imports(self):
        """Verify error_context function exists."""
        from antinode_norma.utils.ui import error_context

        assert callable(error_context)

    def test_prompt_user_choice_imports(self):
        """Verify prompt_user_choice function exists."""
        from antinode_norma.utils.ui import prompt_user_choice

        assert callable(prompt_user_choice)


class TestCLIVersionOption:
    """Test version option."""

    def test_version_flag_displayed(self):
        """Verify --version flag works."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        # Should display a version number


class TestCLICompletion:
    """Test shell completion generation."""

    def test_completion_command_outputs_script(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["completion", "bash"])
        assert result.exit_code == 0
        assert "complete" in result.output.lower()


class TestCLIParseCommand:
    """Test feature parsing CLI command."""

    def test_parse_help_includes_interactive_flag(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["parse", "--help"])
        assert result.exit_code == 0
        assert "--interactive" in result.output


class TestCLIErrorHandling:
    """Test improved error handling."""

    def test_generate_with_nonexistent_file_shows_error(self):
        """Verify helpful error when file doesn't exist."""
        runner = CliRunner()
        result = runner.invoke(cli, ["generate", "--file", "nonexistent_file.txt"])
        # Click's path validation should catch this
        assert result.exit_code != 0

    @patch("antinode_norma.cli.run_agent_from_raw")
    def test_generate_handles_exceptions_gracefully(self, mock_run):
        """Verify exceptions are caught and shown nicely."""
        mock_run.side_effect = RuntimeError("Test error")

        runner = CliRunner()
        result = runner.invoke(cli, ["generate", "As a user, I want to test"])

        assert result.exit_code == 1


class TestCLIQualityOutput:
    """Test improved quality output display."""

    @patch("antinode_norma.cli.run_agent_from_raw")
    def test_quality_check_shows_colored_score(self, mock_run):
        """Verify quality score output with color indicators."""
        mock_run.return_value = {"quality_score": 0.85, "passes_invest": True, "issues": []}

        runner = CliRunner()
        result = runner.invoke(cli, ["generate", "As a user, I want to log in", "--quality-only"])

        assert result.exit_code == 0
        assert "0.9" in result.output or "85" in result.output
        assert "Passes INVEST" in result.output

    @patch("antinode_norma.cli.run_agent_from_raw")
    def test_quality_issues_shown_with_bullets(self, mock_run):
        """Verify issues display with bullet points."""
        mock_run.return_value = {
            "quality_score": 0.5,
            "passes_invest": False,
            "issues": ["Missing acceptance criteria", "Story too large"],
        }

        runner = CliRunner()
        result = runner.invoke(cli, ["generate", "A large story", "--quality-only"])

        assert result.exit_code == 0
        assert "Quality issues found" in result.output
        # Should have bullet points
        assert "•" in result.output or "-" in result.output


class TestCLIIntegrationCommands:
    """Test new integration-related CLI commands."""

    @patch("antinode_norma.agent_tools.comment_on_jira")
    def test_jira_comment_command_invokes_tool(self, mock_comment):
        mock_comment.return_value = {"issue_key": "ABC-1", "status": "posted"}
        runner = CliRunner()
        result = runner.invoke(cli, ["jira-comment", "ABC-1", "Fix", "issue"])

        assert result.exit_code == 0
        assert '"status": "posted"' in result.output

    @patch("antinode_norma.agent_tools.upload_testrail_case")
    def test_testrail_case_command_invokes_tool(self, mock_upload):
        mock_upload.return_value = {"case_id": 123, "status": "created"}
        runner = CliRunner()
        result = runner.invoke(
            cli, ["testrail-case", "--section-id", "42", "--title", "Login flow"]
        )

        assert result.exit_code == 0
        assert '"status": "created"' in result.output

    @patch("antinode_norma.agent_tools.notify_slack")
    def test_notify_slack_command_invokes_tool(self, mock_notify):
        mock_notify.return_value = {"status": "sent", "response_code": 200}
        runner = CliRunner()
        result = runner.invoke(cli, ["notify-slack", "Build", "passed"])

        assert result.exit_code == 0
        assert '"response_code": 200' in result.output
