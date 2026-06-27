#!/usr/bin/env python
"""Command-line interface for antinode-norma."""

import asyncio
import sys
import os
import json
from pathlib import Path
import click
from dotenv import load_dotenv

from antinode_norma.runner import run_agent_from_raw
from antinode_norma.utils.ui import (
    success_message,
    error_message,
    warning_message,
    info_message,
    section_header,
    error_context,
    progress_bar,
)

load_dotenv()


def _print_json_result(result):
    if "error" in result:
        error_message(result["error"])
        if result.get("details"):
            click.echo(result["details"])
        sys.exit(1)
    success_message("Integration command completed successfully.")
    click.echo(json.dumps(result, indent=2))
    return result


@click.group()
@click.version_option()
def cli():
    """Antinode Norma – Transform user stories into Gherkin feature files.

    \b
    Quick start:
      anorm generate "As a user, I want to log in"
      anorm generate --file my_story.txt
      anorm learn --report-file test-results/report.json --show-suggestions
    """


@cli.command()
@click.argument("story_text", required=False)
@click.option("--file", "-f", type=click.Path(exists=True),
              help="Read story from file")
@click.option("--output-dir", "-o", default="features",
              help="Output directory for feature files")
@click.option("--quality-only", is_flag=True,
              help="Only check quality, do not generate")
@click.option("--dry-run", is_flag=True,
              help="Show what would be generated without writing files")
@click.option("--interactive", is_flag=True,
              help="Ask for help on unmapped steps")
def generate(story_text, file, output_dir, quality_only, dry_run, interactive):
    """Generate a feature file from a user story.

    \b
    Examples:
      anorm generate "As a user, I want to log in"
      anorm generate --file my_story.txt --output-dir my_features
      anorm generate --file my_story.txt --dry-run
      anorm generate --file my_story.txt --interactive
    """
    if file:
        try:
            with open(file, "r") as f:
                story_text = f.read()
            info_message(f"Loaded story from {file}")
        except IOError as e:
            error_context(e, f"Failed to read story file: {file}")
            sys.exit(1)

    if not story_text:
        error_message(
            "No story provided. Use --file or pass story text as argument.")
        click.echo("Run 'anorm generate --help' for usage examples.")
        sys.exit(1)

    os.environ["NORMA_OUTPUT_DIR"] = output_dir

    async def run():
        try:
            with progress_bar(description="Analyzing story...") as progress:
                task = progress.add_task("[cyan]Processing...", total=None)
                result = await run_agent_from_raw(story_text, quality_only=quality_only)
                progress.update(task, completed=True)

            if quality_only:
                section_header("Quality Assessment")
                score = result.get("quality_score", 0)
                score_color = "green" if score >= 0.8 else "yellow" if score >= 0.6 else "red"
                click.echo(
                    f"Quality score: [{score_color}]{score:.1%}[/{score_color}]")
                click.echo(f"Passes INVEST: {result['passes_invest']}")

                if result.get("issues"):
                    warning_message("Quality issues found:")
                    for issue in result["issues"]:
                        click.echo(f"  • {issue}")
                else:
                    success_message("Story meets INVEST criteria")
            else:
                if "error" in result:
                    error_message(f"Generation failed: {result['error']}")
                    if result.get("issues"):
                        click.echo("\nIssues found:")
                        for issue in result["issues"]:
                            click.echo(f"  • {issue}")
                    if interactive:
                        info_message(
                            "Interactive mode is enabled. You can retry with corrected story text."
                        )
                        if click.confirm(
                            "Would you like to retry with corrected story text?",
                                default=False):
                            corrected = click.prompt(
                                "Enter corrected story text", type=str)
                            result = await run_agent_from_raw(corrected, quality_only=quality_only)
                            if "error" in result:
                                error_message(
                                    f"Generation failed again: {
                                        result['error']}")
                                sys.exit(1)
                            if dry_run:
                                info_message("Dry-run mode: no files written")
                                section_header("Generated Feature File")
                                feature_path = result.get(
                                    "feature_path", "features/generated.feature")
                                click.echo(f"Would write to: {feature_path}")
                                click.echo(
                                    "\n(Content preview not available in this version)")
                            else:
                                success_message(
                                    f"Feature file written: {
                                        result['feature_path']}")
                            return result
                    sys.exit(1)
                else:
                    if dry_run:
                        info_message("Dry-run mode: no files written")
                        section_header("Generated Feature File")
                        feature_path = result.get(
                            "feature_path", "features/generated.feature")
                        click.echo(f"Would write to: {feature_path}")
                        click.echo(
                            "\n(Content preview not available in this version)")
                    else:
                        success_message(
                            f"Feature file written: {
                                result['feature_path']}")

            return result
        except Exception as e:
            error_context(e, "An unexpected error occurred during generation")
            sys.exit(1)

    asyncio.run(run())


@cli.command()
@click.argument("goal")
def agent(goal):
    """Run the autonomous BDD agent with a high‑level goal.

    \b
    Example:
      anorm agent "Generate login and password reset tests for our web app"
    """
    try:
        from .agent import BDDAgent
        from .agent_tools import AGENT_TOOLS

        info_message(f"Starting agent with goal: {goal}")

        llm_config = {
            "provider": os.getenv(
                "LLM_PROVIDER",
                "openrouter"),
            "api_key": os.getenv("OPENROUTER_API_KEY") or os.getenv("ANTHROPIC_API_KEY"),
        }

        if not llm_config["api_key"]:
            error_message(
                "LLM API key not configured. Set OPENROUTER_API_KEY or ANTHROPIC_API_KEY."
            )
            sys.exit(1)

        agent_instance = BDDAgent(llm_config, AGENT_TOOLS)

        with progress_bar(description="Agent running...") as progress:
            task = progress.add_task("[cyan]Processing...", total=None)
            result = agent_instance.run(goal)
            progress.update(task, completed=True)

        success_message("Agent completed")
        section_header("Result")
        click.echo(json.dumps(result, indent=2))

    except Exception as e:
        error_context(e, "Agent execution failed")
        sys.exit(1)


@cli.command("jira-search")
@click.option("--label", default="bdd-ready", help="JIRA label to search for.")
def jira_search(label):
    """Search JIRA issues by label."""
    from .agent_tools import search_jira_stories

    result = search_jira_stories(label=label)
    return _print_json_result(result)


@cli.command("jira-comment")
@click.argument("issue_key")
@click.argument("comment", nargs=-1)
def jira_comment(issue_key, comment):
    """Post a comment on a JIRA issue."""
    from .agent_tools import comment_on_jira

    result = comment_on_jira(
        issue_key=issue_key,
        comment=" ".join(comment).strip())
    return _print_json_result(result)


@cli.command("jira-transition")
@click.argument("issue_key")
@click.argument("transition_name", nargs=-1)
def jira_transition(issue_key, transition_name):
    """Transition a JIRA issue to a new status."""
    from .agent_tools import transition_jira_issue

    result = transition_jira_issue(
        issue_key=issue_key, transition_name=" ".join(transition_name).strip()
    )
    return _print_json_result(result)


@cli.command("jira-status")
@click.argument("issue_key")
@click.argument("status_name", nargs=-1)
def jira_status(issue_key, status_name):
    """Update a JIRA issue status by name."""
    from .agent_tools import update_jira_issue_status

    result = update_jira_issue_status(
        issue_key=issue_key, status_name=" ".join(status_name).strip()
    )
    return _print_json_result(result)


@cli.command("testrail-case")
@click.option("--section-id", required=True,
              type=int, help="TestRail section ID.")
@click.option("--title", required=True,
              help="Title for the TestRail test case.")
@click.option("--description", default="",
              help="Description for the test case.")
@click.option("--priority-id", default=2, type=int,
              help="Priority ID for the test case.")
def testrail_case(section_id, title, description, priority_id):
    """Upload a test case to TestRail."""
    from .agent_tools import upload_testrail_case

    result = upload_testrail_case(
        section_id=section_id,
        title=title,
        description=description,
        priority_id=priority_id,
    )
    return _print_json_result(result)


@cli.command("testrail-result")
@click.option("--test-id", required=True, type=int, help="TestRail test ID.")
@click.option("--status-id", required=True, type=int, help="Result status ID.")
@click.option("--comment", default="", help="Comment for the test result.")
def testrail_result(test_id, status_id, comment):
    """Add a result to a TestRail test case."""
    from .agent_tools import add_testrail_result

    result = add_testrail_result(
        test_id=test_id,
        status_id=status_id,
        comment=comment)
    return _print_json_result(result)


@cli.command("notify-slack")
@click.option("--webhook-url",
              help="Slack webhook URL. If omitted, uses SLACK_WEBHOOK_URL from environment.")
@click.argument("text", nargs=-1)
def notify_slack(webhook_url, text):
    """Send a Slack notification."""
    from .agent_tools import notify_slack as notify_slack_tool

    result = notify_slack_tool(
        webhook_url=webhook_url,
        text=" ".join(text).strip())
    return _print_json_result(result)


@cli.command("notify-teams")
@click.option("--webhook-url",
              help="Teams webhook URL. If omitted, uses TEAMS_WEBHOOK_URL from environment.")
@click.option("--title", required=True, help="Notification title.")
@click.option("--text", required=True, help="Notification body text.")
def notify_teams(webhook_url, title, text):
    """Send a Microsoft Teams notification."""
    from .agent_tools import notify_teams as notify_teams_tool

    result = notify_teams_tool(webhook_url=webhook_url, title=title, text=text)
    return _print_json_result(result)


@cli.command()
@click.option("--report-file",
              "report_file",
              required=True,
              type=click.Path(exists=True,
                              dir_okay=False),
              help="Path to a Playwright JSON report file produced with --reporter=json.",
              )
@click.option(
    "--db-file",
    "db_file",
    type=click.Path(dir_okay=False),
    help="Optional path to the local failure database file.",
)
@click.option("--show-recent", is_flag=True,
              help="Show recent stored failure examples after learning.")
@click.option("--show-suggestions", is_flag=True,
              help="Show suggested fixes for the learned failures.")
def learn(report_file, db_file, show_recent, show_suggestions):
    """Learn from Playwright test failures and persist failure patterns.

    \b
    Examples:
      anorm learn --report-file test-results/report.json
      anorm learn --report-file test-results/report.json --show-suggestions
      anorm learn --report-file test-results/report.json --db-file ~/.my_failures.db --show-recent
    """
    from antinode_norma.core.failure_analyzer import (
        get_failure_suggestions_for_step,
        get_recent_failures,
        set_db_file,
        store_test_failures,
    )

    if db_file:
        set_db_file(Path(db_file))
        info_message(f"Using custom database: {db_file}")

    try:
        section_header("Learning from Test Failures")

        with progress_bar(description="Processing test report...") as progress:
            task = progress.add_task("[cyan]Reading report...", total=None)
            failures = store_test_failures(Path(report_file))
            progress.update(task, completed=True)

        success_message(
            f"Stored {
                len(failures)} failure event(s) from {report_file}")

        if failures:
            section_header("Failure Summary")
            for i, failure in enumerate(failures[:10], 1):
                selector_info = failure.selector or "no selector"
                click.echo(f"  {i}. [{failure.test_title}] {selector_info}")

            if len(failures) > 10:
                info_message(f"... and {len(failures) - 10} more")

        if show_suggestions and failures:
            section_header("Suggested Fixes")
            for failure in failures[:10]:
                context = failure.step_text or failure.selector or failure.test_title
                suggestions = get_failure_suggestions_for_step(context)
                if suggestions:
                    header = failure.selector or failure.test_title
                    click.echo(f"\nSuggestions for {header}")
                    click.echo(f"  📍 {header}:")
                    for suggestion in suggestions:
                        click.echo(f"     ✓ {suggestion}")

        if show_recent:
            section_header("Recent Failure Records")
            recent = get_recent_failures(5)
            if recent:
                for i, failure in enumerate(recent, 1):
                    error_first_line = (
                        failure.error_message.splitlines()[0]
                        if failure.error_message
                        else "unknown"
                    )
                    click.echo(f"  {i}. {failure.test_title}")
                    click.echo(f"     Selector: {failure.selector or 'none'}")
                    click.echo(f"     Error: {error_first_line}")
            else:
                info_message("No prior failure records found.")

        success_message("Learning complete!")

    except Exception as exc:
        error_context(exc, "Failed to learn from report")
        sys.exit(1)


@cli.command()
@click.argument("shell",
                type=click.Choice(["bash",
                                   "zsh",
                                   "powershell"],
                                  case_sensitive=False))
def completion(shell):
    """Generate shell completion script for the given shell."""
    try:
        from click.shell_completion import get_completion_class

        completion_cls = get_completion_class(shell)
        completion = completion_cls(cli, {}, "anorm", "ANORM_COMPLETE")
        script = completion.source_template % completion.source_vars()
        click.echo(script)
    except Exception as e:
        error_context(e, "Shell completion generation failed")
        sys.exit(1)


@cli.command()
@click.option(
    "--feature-file",
    "feature_file",
    required=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Path to a Gherkin feature file to parse.",
)
@click.option("--interactive", is_flag=True,
              help="Prompt for unmapped step mappings during parse.")
def parse(feature_file, interactive):
    """Parse a feature file into mapped test steps."""
    try:
        from antinode_norma.codegen.parsers.gherkin_parser import GherkinParser
        from antinode_norma.codegen.models.test_model import ActionType

        def interactive_callback(
                step_text: str,
                error_message: str,
                suggestions: list[str] = None):
            warning_message(f"Unmapped step: {step_text}")
            if error_message:
                warning_message(error_message)
            click.echo(
                "Provide a mapping as ACTION|target|value (target/value optional)")
            raw = click.prompt("Mapping", type=str)
            if not raw:
                raise click.Abort("No mapping provided")
            parts = [part.strip() for part in raw.split("|")]
            action_name = parts[0].upper()
            if action_name not in ActionType.__members__:
                raise click.BadParameter(f"Unknown action: {action_name}")
            target = parts[1] if len(parts) > 1 and parts[1] else None
            value = parts[2] if len(parts) > 2 and parts[2] else None
            return ActionType[action_name], target, value, {}

        parser = GherkinParser(
            interactive_callback=interactive_callback if interactive else None)
        suite = parser.parse(Path(feature_file))
        section_header("Parsed Feature")
        for case in suite.cases:
            click.echo(f"Scenario: {case.name}")
            for step in case.steps:
                click.echo(
                    f"  - {step.description} -> {step.action.name} target={step.target} value={step.value}"
                )
    except Exception as e:
        error_context(e, "Failed to parse feature file")
        sys.exit(1)


@cli.command()
@click.option("--transport", default="stdio",
              help="MCP transport (stdio or sse)")
def serve(transport):
    """Start the Norma MCP server.

    \b
    Example:
      anorm serve --transport stdio
    """
    try:
        from antinode_norma.server.mcp_server import main as mcp_main

        info_message(f"Starting Norma MCP server on {transport}...")
        asyncio.run(mcp_main())
    except Exception as e:
        error_context(e, "MCP server startup failed")
        sys.exit(1)


def main():
    cli()


if __name__ == "__main__":
    cli()
