# End-to-End Workflow: From User Story to Executable Tests

This guide walks you through the entire BDD lifecycle using Antinode Norma:

1. Write a user story.
2. Validate and improve the story (INVEST quality).
3. Generate a Gherkin `.feature` file.
4. Generate executable test scripts (Playwright/Cypress/Selenium).
5. Run the tests.

You can use either the CLI, the Python API, or the MCP server (e.g., via Claude Desktop).

---

## Prerequisites

- Python 3.9+
- Git
- (Optional) Node.js/npm for Playwright/Cypress
- (Optional) Docker or Podman

> For a fully contained local developer experience, see [Docker and Local Development](DOCKER.md).

---

## 1. Installation

```bash
git clone https://github.com/antinodelabs/antinode-norma.git
cd antinode-norma
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -e .
```

This single command installs **all dependencies** defined in `pyproject.toml`, including:

- Gherkin parsing (`gherkin-official`)
- CLI (`click`)
- YAML configuration (`PyYAML`)
- Templating (`Jinja2`)
- Environment variable loading (`python-dotenv`)

All done – no extra installs needed.

---

## 2. Configuration

Copy the environment template:

```bash
cp .env.example .env
```

Edit `.env` with your LLM provider and API keys. For example, using OpenRouter:

```ini
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-...
LLM_MODEL=openai/gpt-oss-120b:free
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=1024
```

For JIRA integration (optional):

```ini
JIRA_SERVER=https://your-domain.atlassian.net
JIRA_TOKEN=your_personal_access_token
```

For code generation defaults (optional), add:

```ini
CODEGEN_DEFAULT_FRAMEWORK=playwright
CODEGEN_OUTPUT_DIR=generated_tests
CODEGEN_QUALITY_USE_PAGE_OBJECTS=true
CODEGEN_QUALITY_GENERATE_STEP_DEFS=true
CODEGEN_QUALITY_RUN_FORMATTER=true
CODEGEN_QUALITY_FORMATTER_TOOL=prettier
```

You can also create a `codegen.yaml` file in the project root for more advanced settings (see [Code Generation Module README](../antinode_norma/codegen/README.md)).

---

## 3. Write a User Story

Create a text file, e.g., `story.txt`:

```
As a registered user, I want to reset my password so that I can regain access to my account.

Acceptance Criteria:
- I click on "Forgot Password" on the login page.
- I enter my registered email address.
- I receive a password reset email.
- I click the reset link and set a new password.
- I can then log in with the new password.
```

---

## 4. Validate and Improve the Story

### Using the CLI

```bash
anorm generate --quality-only "$(cat story.txt)"
```

This will output an INVEST quality report. If the story fails any criteria, you can improve it.

You can also preview the generated output without writing files:

```bash
anorm generate --dry-run "$(cat story.txt)"
```

If the story needs refining, use interactive retry mode:

```bash
anorm generate --interactive "$(cat story.txt)"
```

### Using the MCP Server (Claude Desktop)

If you have the MCP plugin installed, you can ask Claude:

> "Submit this story for INVEST quality assessment: [paste story]"

Claude will call `submit_story` and provide feedback.

---

## 5. Generate the Gherkin Feature File

### Using the CLI

```bash
anorm generate "$(cat story.txt)"
```

This will create `features/reset_password.feature` (or a custom path if specified). The file will contain Gherkin scenarios derived from your story and acceptance criteria.

Preview generation without writing a feature file:

```bash
anorm generate --dry-run "$(cat story.txt)"
```

Use interactive retry mode when the generated output is too vague:

```bash
anorm generate --interactive "$(cat story.txt)"
```

### Using the MCP Server

> "Generate a feature file for this story: [paste story]"

Claude will call `generate_feature` and save the file.

### Using the JIRA Connector

If you have JIRA issues labelled `bdd-ready`, you can run:

```bash
python -m antinode_norma.connectors.jira_connector
```

This will fetch issues and generate feature files automatically.

---

## 6. Validate the Generated Feature File

Before generating tests, ensure the feature file is valid and meets INVEST criteria.

### Using the CLI (codegen)

```bash
python -m antinode_norma.codegen.cli.commands validate -f features/reset_password.feature
```

### Using the MCP Server

> "Validate the feature file at `features/reset_password.feature`"

Claude will call `validate_feature` and report any issues.

---

## 7. Generate Executable Tests

Now that you have a validated `.feature` file, you can generate test scripts for your preferred framework.

### Using the CLI

```bash
python -m antinode_norma.codegen.cli.commands generate -f features/reset_password.feature -fw playwright
```

This will generate:

- `generated_tests/playwright/reset_password.spec.ts`
- (If `quality.use_page_objects=true`) `generated_tests/playwright/pages/...`
- (If `quality.generate_step_defs=true`) `generated_tests/playwright/steps/...`

### Using the MCP Server

> "Generate Playwright tests with Page Objects for `features/reset_password.feature`"

Claude will call `generate_tests` with the appropriate parameters.

### Customizing Output

You can override settings via CLI flags:

```bash
python -m antinode_norma.codegen.cli.commands generate \
    -f features/reset_password.feature \
    -fw cypress \
    -o ./custom_output
```

Or by editing `codegen.yaml` or `.env` (see [Configuration](#2-configuration)).

---

## 8. Run the Generated Tests

### Playwright

Install Playwright (if not already):

```bash
npm init playwright@latest
```

Run the test:

```bash
npx playwright test generated_tests/playwright/reset_password.spec.ts
```

### Cypress

Install Cypress:

```bash
npm install cypress
```

Run the test:

```bash
npx cypress run --spec generated_tests/cypress/reset_password.cy.js
```

### Selenium (pytest)

Install Selenium and the webdriver:

```bash
pip install selenium pytest
```

Run the test:

```bash
pytest generated_tests/selenium/reset_password_test.py
```

---

## 9. Optional: Automating with the Agent

The autonomous BDD agent can orchestrate the entire workflow:

```bash
anorm agent "Take JIRA-123, generate a feature file, validate it, and generate Playwright tests with Page Objects."
```

The agent will:

1. Fetch the JIRA story (if JIRA is configured).
2. Assess and improve the story.
3. Generate the `.feature` file.
4. Validate the feature.
5. Generate tests with all quality enhancements.

---

## 10. Full MCP Integration (Claude Desktop)

If you're using the MCP server with Claude Desktop, you can perform the entire workflow conversationally:

1. **Submit story** – "Submit this story for INVEST quality: [paste]"
2. **Improve story** – "Improve the story based on the quality issues."
3. **Generate feature** – "Generate a feature file for the improved story."
4. **Validate feature** – "Validate `features/reset_password.feature`."
5. **Generate tests** – "Generate Playwright tests with Page Objects for `features/reset_password.feature`."

All steps use the same MCP tools, and Claude will call them sequentially.

---

## 11. Troubleshooting

| Issue | Solution |
| :--- | :--- |
| `ModuleNotFoundError` for `gherkin` | Install: `pip install gherkin-official` |
| `No rule matches step` | Extend the rule engine in `engine/rules.py` |
| Generated tests not formatted | Check `quality.run_formatter` and `formatter_tool` settings |
| MCP tools not appearing | Ensure the MCP server is running and the plugin is correctly configured |

---

## 12. Next Steps

- Customise the rule engine for your step definitions.
- Add support for additional frameworks.
- Integrate with your CI/CD pipeline.
- Explore advanced quality configurations (Page Objects, Scenario Outlines, etc.).

---

**Happy testing! 🧪**
