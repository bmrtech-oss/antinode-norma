# Client Usage Guide for Antinode Norma

This guide walks you through setting up and testing **Antinode Norma** using a **free JIRA Cloud account** and **OpenRouter's free model** (`openai/gpt-oss-120b:free`). By the end, you'll have a working BDD generation pipeline that pulls user stories from JIRA and produces validated Gherkin feature files.

## ✅ Prerequisites

- Python 3.9+ installed on your system.
- A **free JIRA Cloud account** (sign up at [atlassian.com](https://www.atlassian.com)).
- An **OpenRouter account** (free tier works) – sign up at [openrouter.ai](https://openrouter.ai).
- Basic familiarity with the command line.

---

## 1. Clone & Install

```bash
git clone https://github.com/antinodelabs/antinode-norma.git
cd antinode-norma
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -e .
```

---

## 2. Configure Environment Variables

Copy the example configuration file and edit it:

```bash
cp .env.example .env
```

Open `.env` in your editor and set the following values:

```ini
# ----- LLM Provider: OpenRouter -----
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-...   # Your OpenRouter API key
LLM_MODEL=openai/gpt-oss-120b:free
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=1024

# ----- JIRA Configuration -----
JIRA_SERVER=https://your-company.atlassian.net   # Your JIRA domain
JIRA_TOKEN=your_api_token_here                    # Generate from Atlassian account

# ----- TestRail Configuration -----
TESTRAIL_URL=https://yourcompany.testrail.io
TESTRAIL_USER=your-email@example.com
TESTRAIL_TOKEN=your_api_token_here

# ----- Notification Webhooks -----
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T/123/ABC
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/...
```

## 2.1 Optional Integration CLI Commands

Use the new CLI commands to invoke integrations directly from the terminal.

```bash
anorm jira-search --label bdd-ready
anorm jira-comment ABC-123 "Adding validation notes after feature generation"
anorm jira-transition ABC-123 "In Progress"
anorm jira-status ABC-123 Done
anorm testrail-case --section-id 42 --title "Login flow" --description "Verify login succeeds"
anorm testrail-result --test-id 128 --status-id 1 --comment "Passed on CI"
anorm notify-slack --text "Build passed: all tests succeeded"
anorm notify-teams --title "CI Status" --text "All checks passed"
```

### 2.1 Generate a JIRA API Token

1. Log in to your Atlassian account.
2. Go to [https://id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens).
3. Click **Create API token**, give it a label (e.g., "Norma"), and copy the token.
4. Paste it into `JIRA_TOKEN` in your `.env`.

### 2.2 Get an OpenRouter API Key

1. Log in to [openrouter.ai](https://openrouter.ai).
2. Go to your **API Keys** page and create a new key.
3. Copy the key and paste it into `OPENROUTER_API_KEY` in your `.env`.

---

## 3. Test the OpenRouter Integration

We provide a small test script to verify OpenRouter works.

Create `openrouter_test.py` in the project root with:

```python
#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from antinode_norma.utils.llm_factory import create_llm_callable

load_dotenv()

config = {
    "provider": "openrouter",
    "api_key": os.getenv("OPENROUTER_API_KEY"),
    "model": os.getenv("LLM_MODEL", "openai/gpt-oss-120b:free"),
    "base_url": os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1"),
    "temperature": float(os.getenv("LLM_TEMPERATURE", "0.2")),
    "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "1024")),
    "extra_body": {"provider": {"require_parameters": True}}
}

llm = create_llm_callable(config)
response = llm("What is the capital of France?")
print("OpenRouter test response:", response)
```

Run it:

```bash
python openrouter_test.py
```

Expected output:
```
OpenRouter test response: The capital of France is Paris.
```

If you see this, your LLM integration is working.

---

## 4. Create a Test User Story in JIRA

1. Log in to your JIRA Cloud instance.
2. Navigate to your project and click **Create**.
3. **Issue Type:** `Story`
4. **Summary:**
   `As a registered user, I want to reset my password via email so that I can regain access to my account.`
5. **Description:** (paste the following)
   ```
   As a registered user,
   I want to reset my password via email
   so that I can regain access to my account.

   Acceptance criteria:
   - User clicks "Forgot password" on the login page.
   - System sends a password reset link to the registered email address.
   - The reset link expires after 30 minutes.
   - User can set a new password after clicking the link.
   - An error message is shown if the link is invalid or expired.
   ```
6. **Labels:** Add `bdd-ready` (critical for the connector to pick it up).
7. Click **Create**. Note the issue key (e.g., `PROJ-123`).

---

## 5. Test the CLI (Direct Generation)

Before testing the JIRA connector, try generating a feature file directly:

```bash
anorm generate "As a user, I want to reset my password so that I can regain access. Acceptance criteria: click forgot password, receive email, set new password."
```

You should see:

```
Feature file written: features/reset_password.feature
```

Open `features/reset_password.feature` – it should contain a valid Gherkin scenario.

To preview output without writing a feature file:

```bash
anorm generate --dry-run "As a user, I want to reset my password so that I can regain access. Acceptance criteria: click forgot password, receive email, set new password."
```

To retry a failed story interactively:

```bash
anorm generate --interactive "As a user, I want to reset my password so that I can regain access. Acceptance criteria: click forgot password, receive email, set new password."
```

To generate shell completion and parse features:

```bash
anorm completion bash > ~/.bashrc
anorm parse --feature-file features/reset_password.feature
anorm parse --feature-file features/reset_password.feature --interactive
```

---

## 6. Generating Executable Tests from Feature Files

Once you have validated `.feature` files, you can use the code generation module to turn them into executable test scripts.

### 6.1 CLI – Generate Tests

```bash
python -m antinode_norma.codegen.cli.commands generate -f features/login.feature -fw playwright
```

**Options:**
- `-f, --feature` – Path to the `.feature` file (required).
- `-o, --output` – Output directory (overrides config).
- `-fw, --framework` – Target framework: `playwright`, `cypress`, or `selenium`.
- `-c, --config-file` – Optional YAML configuration file.

### 6.2 Generate Tests with Quality Enhancements

Enable Page Objects and step definitions for production‑ready code:

```bash
python -m antinode_norma.codegen.cli.commands generate -f features/login.feature -fw playwright
```

With the following `codegen.yaml` in your project root:

```yaml
default_framework: playwright
quality:
  use_page_objects: true
  generate_step_defs: true
  selector_strategy: "data-testid"
  run_formatter: true
  formatter_tool: "prettier"
```

This generates:
- `generated_tests/playwright/login.spec.ts` – The test file.
- `generated_tests/playwright/pages/login.page.ts` – Page Object class.
- `generated_tests/playwright/steps/common_steps.ts` – Reusable step functions.

### 6.3 Python API – Code Generation

```python
from antinode_norma.codegen import Orchestrator
from antinode_norma.codegen.config import load_config

# Load configuration (auto‑discovers codegen.yaml and .env)
config = load_config()

# Create orchestrator with quality settings
orchestrator = Orchestrator()

# Generate tests
orchestrator.generate(
    feature_path="features/login.feature",
    output_dir=config.get_output_dir("playwright"),
    framework="playwright"
)
```

### 6.4 Available Code Generation Tools via MCP

If you're using the MCP server or Claude Desktop plugin, the following tools are available:

| Tool | Description |
| :--- | :--- |
| `generate_tests` | Generate full test scripts from a feature file |
| `generate_page_objects` | Generate Page Object classes only |
| `generate_step_defs` | Generate reusable step definitions only |
| `validate_feature` | Validate a feature file for quality |

**Example MCP tool call:**

```json
{
  "name": "generate_tests",
  "arguments": {
    "feature_path": "features/login.feature",
    "framework": "playwright",
    "use_page_objects": true,
    "generate_step_defs": true
  }
}
```

### 6.5 Configuration Reference

Create a `codegen.yaml` file in your project root:

```yaml
# codegen.yaml
default_framework: playwright
feature_dir: features
output_dir: generated_tests
verbose: false

quality:
  use_page_objects: true
  generate_step_defs: true
  selector_strategy: "data-testid"
  add_explicit_waits: true
  enable_scenario_outlines: true
  run_formatter: true
  formatter_tool: "prettier"
  page_object_dir: "pages"
  step_def_dir: "steps"
  wait_timeout: 10000
  retry_count: 2
```

Or use environment variables in your `.env`:

```bash
CODEGEN_DEFAULT_FRAMEWORK=playwright
CODEGEN_OUTPUT_DIR=generated_tests
CODEGEN_QUALITY_USE_PAGE_OBJECTS=true
CODEGEN_QUALITY_GENERATE_STEP_DEFS=true
CODEGEN_QUALITY_RUN_FORMATTER=true
```

### 6.6 Next Steps: Run the Generated Tests

**Playwright:**
```bash
npx playwright test generated_tests/playwright/login.spec.ts
```

**Playwright — Visual Testing (Phase 4)**

The code generator can inject `expect(page).toHaveScreenshot()` assertions when you enable visual testing. To create baseline PNGs run the Playwright test runner with `--update-snapshots`.

```bash
# Install dependencies and browsers (once)
npm install
npx playwright install --with-deps

# Run all generated Playwright tests and write baseline snapshots
npx playwright test generated_tests/playwright --project=chromium --update-snapshots
```

**Playwright — Learning from Failures (Phase 5)**

After running a supported test runner with a JSON or JUnit report, you can import failure data into Norma and persist it for future test generation.

```bash
npx playwright test generated_tests/playwright --project=chromium --reporter=json > test-report.json
python -m antinode_norma.cli learn --report-file test-report.json --show-recent --show-suggestions
```

This stores failure patterns in a local SQLite database and provides the generator with negative examples to avoid flakier step mappings. The `--show-suggestions` flag also prints healing recommendations for selectors and step mappings derived from the learned failures.

Notes:
- The generator accepts two CLI flags: `--enable-visual-testing` and `--visual-snapshot-dir` (relative to the emitter output dir).
- Playwright may write snapshots into per-spec folders like `your.spec.ts-snapshots/` and/or into the path used by the emitted `toHaveScreenshot()` call (for example `visual-snapshots/`).
- To review/approve baselines, run the above command in a local branch and commit the snapshot PNGs once verified.

**Cypress:**
```bash
npx cypress run --spec generated_tests/cypress/login.cy.js
```

**Selenium (pytest):**
```bash
pytest generated_tests/selenium/login_test.py
```

---

## 7. Test the JIRA Connector

The connector will fetch all issues with label `bdd-ready`, submit them to the agent, and print quality reports.

Run:

```bash
python -m antinode_norma.connectors.jira_connector
```

Expected output (example):

```
Submitted PROJ-123: {
  "story_id": "a1b2c3d4-...",
  "quality_score": 0.92,
  "passes_invest": true,
  "issues": [],
  "suggestions": []
}
```

If the story fails quality, you'll see suggestions for improvement.

> **Note:** The connector currently only submits the story – it does **not** automatically generate the feature file. To generate, you can either:
> - Use the CLI manually after fetching the story text, or
> - Extend the connector to call the `generate_feature` MCP tool (advanced).

---

## 8. Test the MCP Server (Advanced)

To test the full tool‑based workflow:

**Terminal 1 – Start the MCP server:**

```bash
anorm serve
```

**Terminal 2 – Use a simple client (or modify the connector) to call tools.**

You can create a quick script `test_mcp.py`:

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="anorm",
        args=["serve"]
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "submit_story",
                arguments={
                    "role": "User",
                    "action": "Reset password",
                    "benefit": "Regain access",
                    "acceptance_criteria": [
                        "Click forgot password",
                        "Receive email",
                        "Set new password"
                    ]
                }
            )
            print("Submit result:", result)
            # Now generate feature
            story_id = result.content[0].text.split('"story_id": "')[1].split('"')[0]
            feature = await session.call_tool(
                "generate_feature",
                arguments={"story_id": story_id}
            )
            print("Feature result:", feature)

asyncio.run(main())
```

Run it:

```bash
python test_mcp.py
```

You should see the feature file path printed.

---

## 9. Troubleshooting

| Issue | Likely Cause & Solution |
| :--- | :--- |
| `OPENROUTER_API_KEY` not set | Ensure `.env` is loaded and the key is correct. Run `source .env` or reload your shell. |
| JIRA `401 Unauthorized` | Check `JIRA_SERVER` and `JIRA_TOKEN`. The token must be a valid API token from Atlassian. |
| `No issues found with label 'bdd-ready'` | Verify the label is exactly `bdd-ready` in JIRA, or change the query in `jira_connector.py`. |
| Validation fails for generated Gherkin | The LLM may produce incomplete Gherkin. Try adjusting the prompt in `gherkin_generator.py` or lowering temperature. |
| Rate limits on OpenRouter free model | The free model has limits. If you hit a 429, wait a few seconds and retry. |

---

## 10. Next Steps

- **Automate with CI/CD:** Run the JIRA connector in a GitHub Action on a schedule.
- **Add issue feedback:** Use the new JIRA comment API to post summaries or validation results back to your issue.
- **Improve Quality Rules:** Customize `quality.py` to match your team's INVEST interpretation.
- **Connect to Other Sources:** Write connectors for GitHub Issues, Azure DevOps, or Trello.
- **Deploy as a Service:** Run the MCP server permanently to expose tools to multiple clients.

---

## 11. Conclusion

You now have a fully functional **Antinode Norma** setup that:
- Pulls stories from a free JIRA Cloud account.
- Uses OpenRouter's free LLM to parse and generate Gherkin.
- Checks quality against INVEST criteria.
- Produces a `.feature` file ready for your BDD suite.

For more details, see the [README.md](../README.md) and the [project documentation](../docs/).
