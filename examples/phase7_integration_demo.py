#!/usr/bin/env python3
"""Phase 7 integration demo for Antinode Norma.

This script demonstrates a simple end-to-end workflow:
1. Search JIRA issues by label using the CLI command.
2. Generate a feature file from the first returned story.
3. Send a Slack notification when the demo completes.

Environment variables:
- JIRA_SERVER
- JIRA_TOKEN
- OPENROUTER_API_KEY or ANTHROPIC_API_KEY
- SLACK_WEBHOOK_URL

Run from the repository root with:
Python:
  python examples/phase7_integration_demo.py

If JIRA or Slack is not configured, the script will skip only those steps
and still show how the CLI commands are wired together.
"""

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

PYTHON = sys.executable
CLI_MODULE = "-m"
CLI_ENTRY = "antinode_norma.cli"


def run_cli_command(arguments):
    command = [PYTHON, CLI_MODULE, CLI_ENTRY, *arguments]
    print("\n$ " + " ".join(shlex.quote(v) for v in command))
    result = subprocess.run(
        command, capture_output=True, text=True, cwd=Path(__file__).resolve().parents[1]
    )
    if result.returncode != 0:
        raise RuntimeError(f"Command failed (exit {result.returncode}):\n{result.stderr.strip()}")
    return result.stdout.strip()


def parse_json_output(output):
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise ValueError("Expected JSON output from CLI command, but got:\n" + output) from exc


def search_jira(label="bdd-ready"):
    if not os.getenv("JIRA_SERVER") or not os.getenv("JIRA_TOKEN"):
        print("Skipping JIRA search because JIRA_SERVER or JIRA_TOKEN is not configured.")
        return []

    output = run_cli_command(["jira-search", "--label", label])
    payload = parse_json_output(output)
    return payload.get("issues", [])


def generate_feature(story):
    if not story:
        raise ValueError("No story text provided for feature generation.")

    print("\nGenerating a feature using the existing CLI command...")
    output = run_cli_command(["generate", story, "--dry-run"])
    print(output)
    return output


def send_slack_notification(text):
    if not os.getenv("SLACK_WEBHOOK_URL"):
        print("Skipping Slack notification because SLACK_WEBHOOK_URL is not configured.")
        return None

    output = run_cli_command(["notify-slack", "--text", text])
    print(output)
    return output


def main():
    print("=== Antinode Norma Phase 7 Integration Demo ===")

    issues = search_jira("bdd-ready")
    if issues:
        first = issues[0]
        story_text = f"{first['summary']}\n{first['description']}"
        print(f"Found JIRA issue {first['issue_key']}, using it as the input story.")
    else:
        story_text = (
            "As a customer, I want to reset my password so that I can access my account "
            "when I forget my credentials."
        )
        print("No JIRA issues found or JIRA not configured. Using a fallback story.")

    try:
        generate_feature(story_text)
    except RuntimeError as exc:
        print(f"Feature generation failed: {exc}")
        sys.exit(1)

    notification_text = (
        "Antinode Norma Phase 7 demo completed. " "A feature was generated from the selected story."
    )
    send_slack_notification(notification_text)


if __name__ == "__main__":
    main()
