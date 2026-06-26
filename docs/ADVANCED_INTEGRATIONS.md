# Advanced Integrations

Antinode Norma now supports richer workflows for external tools and automation.

## JIRA

The JIRA connector can now:
- Fetch issues by label with `search_jira_stories`
- Post comments with `comment_on_jira`
- Transition issue status with `transition_jira_issue`
- Update workflow status with `update_jira_issue_status`

Environment variables:
- `JIRA_SERVER` – your JIRA Cloud URL
- `JIRA_TOKEN` – your Atlassian API token
- `JIRA_TRANSITION_ON_PASS` – optional transition name for passed tests
- `JIRA_TRANSITION_ON_FAIL` – optional transition name for failed tests

Example usage in agent tooling:
```python
from antinode_norma.agent_tools import update_jira_issue_status

result = update_jira_issue_status(issue_key="JIRA-123", status_name="Done")
```

## TestRail

A new TestRail connector supports creating cases, recording test results, and creating runs.

Environment variables:
- `TESTRAIL_URL` – base URL for TestRail, e.g. `https://yourcompany.testrail.io`
- `TESTRAIL_USER` – TestRail username or email
- `TESTRAIL_TOKEN` – TestRail API token or password

Example:
```python
from antinode_norma.agent_tools import upload_testrail_case

upload_testrail_case(section_id=42, title="Login flow", description="Verify login succeeds")
```

## Notifications

Notification helpers are available for Slack and Microsoft Teams.

Environment variables:
- `SLACK_WEBHOOK_URL`
- `TEAMS_WEBHOOK_URL`

Example:
```python
from antinode_norma.agent_tools import notify_slack

notify_slack(text="Build passed: all tests succeeded")
```

### CLI Integration Commands

Use the CLI to invoke integrations directly:
```bash
anorm jira-search --label bdd-ready
anorm jira-comment ABC-123 "Feature generation complete"
anorm jira-transition ABC-123 "In Progress"
anorm testrail-case --section-id 42 --title "Login flow" --description "Verify login succeeds"
anorm notify-slack --text "Build passed: all tests succeeded"
```

### Phase 7 Demo Script

A small demo script is available at `examples/phase7_integration_demo.py`.
It searches JIRA, generates a feature file with `anorm generate`, and sends a Slack notification if the webhook is configured.

## CI/CD Templates

This project includes a GitHub Actions workflow in `.github/workflows/ci.yml`, an optional Phase 7 integrations workflow in `.github/workflows/phase7-integrations.yml`, and a GitLab CI template in `.gitlab-ci.yml`.

The pipelines install dependencies, run unit tests, and optionally run integration tests when the relevant secrets are available.
