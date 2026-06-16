# Antinode Norma – Agent Usage Guide

This guide explains how to use the **autonomous BDD agent** built into **Antinode Norma**. The agent can plan and execute multi‑step workflows to transform user stories into validated Gherkin feature files – with optional integration with JIRA, test runners, and pull request creation.

---

## 1. What Is the Agent?

The agent is a **ReAct‑style (Reason + Act) autonomous system** that:

- Ingests a **high‑level goal** (e.g., *“Generate a feature file for JIRA‑123 and run tests”*).
- Plans a sequence of actions using an LLM.
- Executes tools (submit story, generate feature, run tests, create PR, etc.).
- Observes results and adapts its plan.
- Iterates until the goal is achieved or a stopping condition is met.

It leverages the same **pure core** (quality checks, parser, generator) as the CLI, but adds orchestration, memory, and tool‑calling capabilities.

---

## 2. Prerequisites

Before using the agent, ensure you have:

- **Antinode Norma installed** (as described in the main README).
- An **LLM API key** (OpenRouter, Anthropic, or OpenAI) set in your environment (`.env` file).
- (Optional) **JIRA credentials** if you want to fetch stories directly from JIRA.
- (Optional) **Behave** or **Cucumber** if you want to run tests via the agent.

---

## 3. Installation & Setup

The agent is part of the `antinode-norma` package. After installation:

```bash
git clone https://github.com/bmrtech-oss/antinode-norma.git
cd antinode-norma
pip install -e .
```

Configure your `.env` file:

```ini
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-...
# Or use anthropic/openai
```

---

## 4. Using the Agent via CLI

The simplest way to invoke the agent is through the `anorm agent` command.

### Basic Usage

```bash
anorm agent "Generate a feature file for: As a user, I want to reset my password."
```

The agent will:

1. Submit the story.
2. Run INVEST quality checks.
3. If quality fails, it will try to improve the story.
4. Generate a Gherkin `.feature` file.
5. (Optionally) run tests and create a PR.

### With a JIRA Issue

```bash
anorm agent "Generate feature for JIRA-123 and create a PR if tests pass."
```

The agent will:

1. Fetch the JIRA issue (using `fetch_jira_story`).
2. Submit the story.
3. Generate the feature.
4. Run tests (if `behave` is installed).
5. If tests pass, create a PR (if `gitpython` is installed).

### Quality‑Only Check

If you only want the agent to check quality and report issues without generating a file:

```bash
anorm agent "Check quality of story: As a user, I want to reset my password."
```

---

## 5. Using the Agent via MCP Tools

The agent is also exposed as an MCP tool called `run_bdd_agent`. This allows you to invoke it from Claude Desktop or any MCP‑compatible client.

### MCP Tool Definition

- **Name:** `run_bdd_agent`
- **Description:** Run the autonomous BDD agent with a high‑level goal.
- **Input:** `goal` (string) – the high‑level objective.
- **Output:** JSON with the agent’s final state (story_id, feature_path, test_results, pr_url, etc.).

### Example (Using MCP Client in Python)

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(command="anorm", args=["serve"])
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("run_bdd_agent", {
                "goal": "Generate feature for JIRA-123 and create a PR."
            })
            print(result)

asyncio.run(main())
```

### Using with Claude Desktop

Once the plugin is installed (as described in the [Claude Plugin Guide](claude-plugin/README.md)), you can simply ask:

> *“Use the BDD agent to generate a feature file for story: As a user, I want to reset my password.”*

Claude will call the MCP tool and return the result.

---

## 6. How the Agent Works (Internals)

### The ReAct Loop

1. **Plan**: The agent’s internal LLM (the planner) receives the goal, the history of past actions, and a list of available tools. It decides on the next action.
2. **Act**: The agent executes the chosen tool (e.g., `submit_story`, `generate_feature`).
3. **Observe**: The tool’s result is appended to the history.
4. **Repeat**: The agent continues until the planner decides the goal is complete.

### Available Tools

| Tool | Description |
| :--- | :--- |
| `fetch_jira_story` | Fetches a JIRA issue by key and returns its raw text. |
| `submit_story` | Submits a story for quality checking (INVEST). Returns score, issues, suggestions. |
| `improve_story` | Improves a story based on suggestions using the LLM. |
| `generate_feature` | Generates a Gherkin `.feature` file from a submitted story. |
| `run_tests` | Runs Behave/Cucumber tests on a feature file. |
| `fix_feature` | Fixes Gherkin validation errors using the LLM. |
| `create_pr` | Creates a pull request (requires gitpython and GitHub/GitLab API). |
| `comment_on_jira` | Posts a comment to a JIRA issue. |

### State & Memory

The agent maintains a **state** object that tracks:

- The current goal.
- The entire history (actions and results).
- The current story ID.
- The generated feature file path.
- Test results (if any).
- The PR URL (if created).

This state is passed to the planner on each iteration, allowing the agent to adapt based on past outcomes.

---

## 7. Configuration

The agent respects the same environment variables as the rest of Antinode Norma:

| Variable | Purpose |
| :--- | :--- |
| `LLM_PROVIDER` | `openrouter`, `anthropic`, `openai`, `local`, `mock` |
| `OPENROUTER_API_KEY` / `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` | The API key for the chosen provider. |
| `LLM_MODEL` | Model name (defaults: `openai/gpt-oss-120b:free` for OpenRouter). |
| `LLM_TEMPERATURE`, `LLM_MAX_TOKENS` | Sampling parameters. |
| `JIRA_SERVER`, `JIRA_TOKEN` | Optional JIRA credentials. |

---

## 8. Example End‑to‑End Scenarios

### Scenario 1: Generate Feature from a Simple Story

**Goal:** *“Generate a feature file for: As a user, I want to reset my password.”*

1. The planner calls `submit_story` with the story text.
2. Quality returns `passes_invest: False` (e.g., missing acceptance criteria).
3. The planner calls `improve_story` with the story and the suggestions.
4. The improved story passes quality.
5. The planner calls `generate_feature` with the story ID.
6. The agent returns the path to the `.feature` file.

### Scenario 2: JIRA‑Driven Workflow with Tests

**Goal:** *“Generate feature for JIRA‑123 and create a PR if tests pass.”*

1. `fetch_jira_story` retrieves the issue and returns the story text.
2. `submit_story` returns quality report.
3. If quality fails, `improve_story` is called.
4. `generate_feature` writes the `.feature` file.
5. `run_tests` executes Behave on the file.
6. If tests pass, `create_pr` creates a pull request.
7. `comment_on_jira` posts a summary comment.

### Scenario 3: Fixing Validation Errors

If `generate_feature` produces invalid Gherkin, the agent can call `fix_feature` with the errors, and then re‑run the tests.

---

## 9. Troubleshooting

| Issue | Solution |
| :--- | :--- |
| **Agent loops infinitely** | Check the planner prompt; ensure the agent has a way to decide “finish”. If quality fails repeatedly, the agent should eventually force generation or report failure. You can adjust the prompt to limit iterations. |
| **Tool fails with missing arguments** | All tools now accept `**kwargs` and try multiple parameter names (`raw_text`, `story`, `title`). If you still see errors, ensure the planner is using the correct parameter names (use `raw_text` for story content). |
| **No tool is called, and agent stops** | The planner may have decided the goal is impossible. Check the reason in the final output (the `"done"` state). Try rephrasing the goal more explicitly. |
| **JIRA connector fails** | Verify your `.env` contains `JIRA_SERVER` and `JIRA_TOKEN`. Ensure the JIRA issue has the correct label (`bdd-ready`). |

---

## 10. Extending the Agent

You can add new tools by:

1. Defining a new function in `agent_tools.py` that accepts `**kwargs`.
2. Adding it to the `AGENT_TOOLS` dictionary.
3. Optionally, updating the planner prompt to describe the new tool (the prompt can be modified in `agent.py`).

The agent is designed to be extensible – you can integrate with your own internal systems by adding appropriate tools.

---

## 11. Next Steps

- Try the agent with your own stories.
- Integrate with your CI/CD pipeline.
- Extend the toolset to cover your team’s specific workflow.

For more details, see the [Project README](../README.md) and the [Testing Guide](TESTING.md).

---

*Last updated: 2026-06-16*