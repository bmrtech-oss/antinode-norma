# Antinode Norma Tutorial

This tutorial walks through a complete Phase 8 demo of Antinode Norma using markdown steps instead of a video.

## What you will learn

- How to install and configure Antinode Norma
- How to generate Gherkin from user stories
- How to generate executable Playwright tests
- How to use JIRA, TestRail, and Slack integrations
- How to contribute to the project

## 1. Prerequisites

- Python 3.10+ installed
- `pip` available
- Optional API credentials for:
  - OpenRouter, OpenAI, or Anthropic
  - JIRA Cloud
  - TestRail
  - Slack webhook

## 2. Install the project

```bash
git clone https://github.com/antinodelabs/antinode-norma.git
cd antinode-norma
pip install -e .
pip install -r requirements-dev.txt
```

## 3. Configure environment variables

Copy the sample environment file:

```bash
cp .env.example .env
```

Open `.env` and configure your credentials:

```ini
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-...
LLM_MODEL=openai/gpt-oss-120b:free
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=1024

JIRA_SERVER=https://your-domain.atlassian.net
JIRA_TOKEN=your_api_token_here

TESTRAIL_URL=https://yourcompany.testrail.io
TESTRAIL_USER=your-email@example.com
TESTRAIL_TOKEN=your_api_token_here

SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T/123/ABC
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/...
```

## 3.1 Initialize Norma configuration

Once your `.env` file is ready, run:

```bash
anorm init
```

The wizard interactively creates `norma.config.yml` in the current directory. It asks for:

- LLM provider (`openrouter`, `anthropic`, `openai`, or `local`)
- default test framework (`playwright`, `cypress`, or `selenium`)
- output directory for generated tests
- whether to generate Page Objects and reusable step definitions
- whether to run a formatter on generated code and which tool to use

If you already have a configuration file and want to regenerate it, use:

```bash
anorm init --force
```

## 4. Generate a feature file from a user story

Use the CLI to generate a Gherkin feature file from natural language:

```bash
anorm generate "As a user, I want to reset my password so that I can regain access." --dry-run
```

This preview mode shows what would be generated without writing files.

To write the file:

```bash
anorm generate "As a user, I want to reset my password so that I can regain access."
```

## 5. Generate executable tests

Once you have a `.feature` file, generate executable tests:

```bash
python -m antinode_norma.codegen.cli.commands generate -f features/reset_password.feature -fw playwright
```

The generated tests will appear under `generated_tests/playwright/`.

## 6. Use integration helpers

Antinode Norma can connect with external tools using CLI commands and the internal tool registry.

### Search JIRA stories

```bash
anorm jira-search --label bdd-ready
```

## 7. Batch generation for large feature suites

Use the `--feature` option multiple times to generate tests for several feature files in one command.

```bash
anorm generate -f features/login.feature -f features/checkout.feature --workers 4
```

This runs generation in parallel across the requested number of worker threads, speeding up large test suites.

## 8. Verify the integrations

If you have valid API credentials, the commands above will return JSON responses and confirm the action.

### Post a JIRA comment

```bash
anorm jira-comment ABC-123 "Feature generation complete. Ready for review."
```

### Transition a JIRA issue

```bash
anorm jira-transition ABC-123 "In Progress"
```

### Create a TestRail case

```bash
anorm testrail-case --section-id 42 --title "Login flow" --description "Verify login succeeds"
```

### Send a Slack notification

```bash
anorm notify-slack "Build passed: all tests succeeded"
```

## 7. Verify the integrations

If you have valid API credentials, the commands above will return JSON responses and confirm the action.

If an integration is not configured, the CLI will return a helpful error message.

## 8. Contribute to the project

The repository already includes a `CONTRIBUTING.md` guide and issue templates.

### Suggested first contributions

- Improve documentation and examples
- Add new connector modules
- Enhance prompt templates and quality checks
- Add tests for new workflows

## 9. Where to get help

- Open a GitHub issue when you find a bug
- Request a feature using feature requests
- Submit a pull request for documentation improvements

## 10. Next steps

For deeper exploration, read:

- [Client Usage Guide](CLIENT_USAGE.md)
- [End‑to‑End Workflow Guide](E2E_WORKFLOW.md)
- [Advanced Integrations](ADVANCED_INTEGRATIONS.md)
- [Testing Guide](TESTING.md)
