# Antinode Norma – Claude Desktop Plugin Documentation

This document explains how to build, install, configure, and use the **Antinode Norma** plugin for Claude Desktop.

---

## Overview

The Antinode Norma plugin brings BDD (Behavior-Driven Development) capabilities directly into Claude Desktop. It exposes **eight MCP tools** that allow Claude to:

- Submit user stories and receive an INVEST quality report (`submit_story`).
- Improve stories based on quality suggestions (`improve_story`).
- Generate Gherkin `.feature` files from validated stories (`generate_feature`).
- Run the autonomous BDD agent (`run_bdd_agent`).
- **Generate executable test scripts** from feature files (`generate_tests`).
- **Generate Page Object classes** (`generate_page_objects`).
- **Generate reusable step definitions** (`generate_step_defs`).
- **Validate feature files** for quality and completeness (`validate_feature`).

The plugin leverages your chosen LLM (OpenRouter, Anthropic, OpenAI, or local) and supports optional JIRA integration.

---

## Prerequisites

- **Node.js** (≥ 16) – required for the MCPB CLI and to run the plugin wrapper.
- **Python 3.9+** – required to run the `antinode-norma` package.
- **Claude Desktop** (latest version) – installed on your system.
- An API key for your chosen LLM provider (e.g., OpenRouter, Anthropic, OpenAI).

---

## Installation

### 1. Install the MCPB CLI

```bash
npm install -g @anthropic-ai/mcpb
```

### 2. Pack the Plugin

Navigate to the `claude-plugin/` directory inside your `antinode-norma` project and run:

```bash
cd claude-plugin
mcpb pack
```

This will create a file named `antinode-norma.mcpb` in the same directory.

### 3. Install in Claude Desktop

You can install the plugin using any of these methods:

- **Drag and drop** the `.mcpb` file into the Claude Desktop window.
- **File menu**: Go to **Developer → Extensions → Install Extension** and select the file.
- **Settings**: Navigate to **Settings → Extensions → Advanced settings → Install Extension…**.
- **Double-click** the `.mcpb` file (if Claude Desktop is the default application for `.mcpb` files).

After installation, you should see `antinode-norma` listed in Claude Desktop's Extensions panel.

---

## Configuration

### Environment Variables

The plugin requires certain environment variables to be set **before** launching Claude Desktop. The `manifest.json` references these variables using the `${VAR}` syntax, so they are resolved at runtime.

Create a `.env` file in the `claude-plugin/` directory (or anywhere, as long as they are exported in your shell) with the following content:

```env
# ============================================================
# Antinode Norma – Claude Desktop Plugin Configuration
# ============================================================
# LLM Provider (choose one: openrouter, anthropic, openai, local, mock)
LLM_PROVIDER=openrouter

# OpenRouter (recommended – free tier available)
OPENROUTER_API_KEY=sk-or-...

# Optional OpenRouter settings
# LLM_MODEL=openai/gpt-oss-120b:free
# LLM_BASE_URL=https://openrouter.ai/api/v1

# Anthropic (optional)
# ANTHROPIC_API_KEY=sk-...

# OpenAI (optional)
# OPENAI_API_KEY=sk-...

# Local LLM (optional)
# LLM_URL=http://localhost:8080/completions

# Common settings
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=1024

# JIRA (optional)
# JIRA_SERVER=https://your-domain.atlassian.net
# JIRA_TOKEN=your_personal_access_token
```

### Setting the Environment Variables

You can set these variables in several ways:

1. **Export in your shell** (easiest for testing):
   ```bash
   export $(cat claude-plugin/.env | xargs)
   ```
   Then launch Claude Desktop from the same terminal.

2. **Add to your `~/.bashrc` or `~/.zshrc`** for persistence.

3. **Use a `.env` file loaded by Claude Desktop** – currently, Claude Desktop does not auto‑load `.env` files, so you must export them before launching.

### Important Note for Plugin Packaging

> **Note for Plugin Packaging:**
> When you pack the plugin with `mcpb pack`, the `.env` file is **not** included in the bundle. This is by design to avoid shipping secrets. Users must set the required environment variables themselves. The `manifest.json` already references `${OPENROUTER_API_KEY}` and others, so they will be resolved from the environment when Claude Desktop starts. This approach is secure and follows best practices.

---

## Code Generation Tools

The plugin includes four additional MCP tools for test code generation:

### `generate_tests`

Generates executable test scripts from a `.feature` file.

**Parameters:**
| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `feature_path` | string | Yes | Path to the `.feature` file |
| `framework` | string | No | `playwright`, `cypress`, or `selenium` (default: `playwright`) |
| `output_dir` | string | No | Output directory (default: from config) |
| `use_page_objects` | boolean | No | Generate Page Objects (default: `false`) |
| `generate_step_defs` | boolean | No | Generate step definitions (default: `false`) |
| `verbose` | boolean | No | Enable verbose output (default: `false`) |

**Example Claude prompt:**
> "Generate Playwright tests with Page Objects for the feature file at `features/login.feature`."

### `generate_page_objects`

Generates Page Object classes only.

**Parameters:**
| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `feature_path` | string | Yes | Path to the `.feature` file |
| `framework` | string | No | `playwright`, `cypress`, or `selenium` (default: `playwright`) |
| `output_dir` | string | No | Output directory |

### `generate_step_defs`

Generates reusable step definitions only.

**Parameters:**
| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `feature_path` | string | Yes | Path to the `.feature` file |
| `framework` | string | No | `playwright`, `cypress`, or `selenium` (default: `playwright`) |
| `output_dir` | string | No | Output directory |

### `validate_feature`

Validates a Gherkin feature file for quality and completeness.

**Parameters:**
| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `feature_path` | string | Yes | Path to the `.feature` file |
| `check_invest` | boolean | No | Run INVEST quality check (default: `true`) |

**Example Claude prompt:**
> "Validate the feature file at `features/reset_password.feature` and tell me if it meets INVEST criteria."

### Output Quality Enhancements

When using `generate_tests` with `use_page_objects: true` or `generate_step_defs: true`, the generated code includes:

- **Page Object Model** – Clean separation of selectors and actions.
- **Reusable Step Definitions** – Common actions (fill, click, navigate) as functions.
- **Explicit Waits** – Robust `waitForSelector` before interactions.
- **Data‑Driven Testing** – Support for Scenario Outlines with Examples.
- **Code Formatting** – Auto‑formatting with Prettier or Black.
- **Linting** – Optional ESLint or flake8 with auto‑fix.

### Configuration for Code Generation

Add these variables to your `.env` file to control code generation defaults:

```bash
# Code Generation defaults
CODEGEN_DEFAULT_FRAMEWORK=playwright
CODEGEN_OUTPUT_DIR=generated_tests
CODEGEN_QUALITY_USE_PAGE_OBJECTS=true
CODEGEN_QUALITY_GENERATE_STEP_DEFS=true
CODEGEN_QUALITY_SELECTOR_STRATEGY=data-testid
CODEGEN_QUALITY_RUN_FORMATTER=true
CODEGEN_QUALITY_FORMATTER_TOOL=prettier
```

See the [Code Generation Module README](../antinode_norma/codegen/README.md) for full configuration options.

---

## Available Tools

After installation, the plugin registers an MCP server named `norma`. The tools are available in Claude Desktop with the prefix `mcp__plugin_antinode-norma_norma__`. You can invoke them by their short names; Claude will understand them naturally.

| Tool | Description | Input Parameters |
| :--- | :--- | :--- |
| `submit_story` | Submits a user story and returns an INVEST quality report. | `raw_text`, `role`, `action`, `benefit`, `acceptance_criteria` (list), `dependencies` (optional), `estimated_points` (optional) |
| `improve_story` | Requests an improved version of a story based on quality suggestions. | `story_id` (from `submit_story`), `suggestions` (list) |
| `generate_feature` | Generates a Gherkin `.feature` file from a previously submitted story. | `story_id` (from `submit_story`), `step_definitions` (optional list) |
| `run_bdd_agent` | Runs the autonomous BDD agent on a high-level goal. | `story` (string), `max_iterations` (integer, optional) |
| `generate_tests` | Generates executable test scripts from a feature file. | `feature_path`, `framework`, `output_dir`, `use_page_objects`, `generate_step_defs`, `verbose` |
| `generate_page_objects` | Generates Page Object classes from a feature file. | `feature_path`, `framework`, `output_dir` |
| `generate_step_defs` | Generates reusable step definitions from a feature file. | `feature_path`, `framework`, `output_dir` |
| `validate_feature` | Validates a Gherkin feature file for quality and completeness. | `feature_path`, `check_invest` |

The standalone code generation tools can be used directly from Claude Desktop when you already have a `.feature` file available. They can also be invoked from within the agent workflow as part of a larger BDD generation process.

---

## Usage Examples in Claude Desktop

Once the plugin is installed, you can ask Claude to use these tools in natural language.

### Example 1: Submit a story

> "Use the submit_story tool with this user story: As a user, I want to reset my password via email so that I can regain access. Acceptance criteria: the system should send a reset link, the user can set a new password, invalid tokens show an error."

Claude will call the tool and return the quality report.

### Example 2: Generate a feature file

> "Using the story ID from the previous step, generate a feature file."

Claude will call `generate_feature` and provide the path to the generated `.feature` file.

### Example 3: Improve a story

> "The quality check failed for story abc-123. Can you improve it based on the suggestions?"

Claude will call `improve_story` with the story ID and suggestions, returning an improved version.

---

## Troubleshooting

| Problem | Likely Cause & Solution |
| :--- | :--- |
| **"ModuleNotFoundError: No module named 'antinode_norma'"** | The plugin cannot find the Python package. Ensure the `antinode-norma` package is installed (`pip install -e .` in the parent directory) and that the `PYTHONPATH` includes the parent directory. The `index.js` wrapper sets this automatically. |
| **"OPENROUTER_API_KEY not set"** | The environment variable is missing. Export it before launching Claude Desktop. See configuration section above. |
| **Plugin does not appear in Extensions** | The `.mcpb` file may be corrupt. Re‑pack it and re‑install. Ensure you're using the latest Claude Desktop version. |
| **"Python not found"** | The `index.js` wrapper assumes `python` is in your PATH. Use an absolute path if needed (modify `index.js`). |
| **Rate limit errors** | OpenRouter free tier has limits. Wait a moment and retry, or upgrade to a paid model. |

---

## Development & Updating

If you modify the plugin or the underlying `antinode-norma` code, re‑pack and re‑install:

```bash
mcpb pack
# Then re-install the new .mcpb file in Claude Desktop
```

You do not need to restart Claude Desktop; it will reload the plugin automatically after installation.

---

## License

This plugin is licensed under the same MIT License as the main `antinode-norma` project.

---

## Support

For issues, open a GitHub issue at [https://github.com/antinodelabs/antinode-norma/issues](https://github.com/antinodelabs/antinode-norma/issues).

Built with ❤️ by [Antinode Labs](https://antinodelabs.com/).
