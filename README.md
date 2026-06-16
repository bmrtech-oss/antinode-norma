# Antinode Norma

[![CI](https://github.com/antinodelabs/antinode-norma/actions/workflows/ci.yml/badge.svg)](https://github.com/antinodelabs/antinode-norma/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP](https://img.shields.io/badge/MCP-compatible-9B59B6)](https://github.com/modelcontextprotocol)

BDD feature file generator with an INVEST quality gate.  
Transform raw user stories into validated Gherkin `.feature` files.  
Built with a data-centric, functional philosophy – inspired by Rich Hickey.

Works with **any LLM** (Claude, GPT, OpenRouter, local) and integrates via **MCP** (Model Context Protocol) for tool-based orchestration.

---

## 📚 Documentation

- [Client Usage Guide](docs/CLIENT_USAGE.md) – Step-by-step setup with JIRA and OpenRouter.
- [Testing Guide](docs/TESTING.md) – How to run and extend the test suite.
- [Contributing Guide](CONTRIBUTING.md) – Guidelines for contributors.

---

## Quick Start

```bash
# Install
git clone https://github.com/antinodelabs/antinode-norma.git
cd antinode-norma
pip install -e .

# Configure
cp .env.example .env
# Edit .env with your API keys (see Configuration below)

# Generate a feature file
anorm generate "As a user, I want to reset my password so that I can regain access."
```

---

## Features

- **INVEST quality assessment** – Checks stories against Independent, Negotiable, Valuable, Estimable, Small, Testable.
- **Automatic Gherkin generation** – Uses your preferred LLM to produce feature files.
- **MCP server** – Exposes tools (`submit_story`, `improve_story`, `generate_feature`) for integration with connectors (JIRA, GitHub, etc.).
- **Provider-agnostic LLM** – Switch between Anthropic, OpenAI, OpenRouter, or local models via configuration.
- **CLI and library** – Use as a command-line tool or import into your own system.
- **Quality-first** – Rejects stories that don't meet INVEST criteria, with actionable suggestions.
- **Pure-core design** – Business logic is side-effect free, easy to test and extend.
- **Comprehensive test suite** – Unit and integration tests with `pytest`.
- **OpenRouter support** – Use free/open models via OpenRouter with the official OpenAI SDK.

---

## Installation

```bash
git clone https://github.com/antinodelabs/antinode-norma.git
cd antinode-norma
pip install -e .
```

For development, install additional test dependencies:

```bash
pip install -r requirements-dev.txt
```

---

## Configuration

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` with your preferred LLM provider:

```ini
# LLM Configuration
# Supported providers: anthropic, openai, openrouter, local, mock
LLM_PROVIDER=openrouter

# For Anthropic:
ANTHROPIC_API_KEY=sk-...

# For OpenAI:
OPENAI_API_KEY=sk-...

# For OpenRouter (uses OpenAI SDK with custom base URL):
OPENROUTER_API_KEY=sk-or-...
LLM_MODEL=openai/gpt-oss-120b:free
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=1024

# JIRA (optional – for the connector)
JIRA_SERVER=https://your-domain.atlassian.net
JIRA_TOKEN=your_personal_access_token
```

> **Note:** OpenRouter uses the `extra_body={"provider": {"require_parameters": True}}` to track reasoning tokens automatically.

---

## Usage

### CLI – Generate a feature file

```bash
anorm generate "As a user, I want to reset my password so that I can regain access. Acceptance criteria: click forgot password, receive email, set new password."
```

Output:

```
Feature file written: features/reset_password.feature
```

### CLI – Check quality only

```bash
anorm generate --quality-only "My story..."
```

This returns the INVEST quality score and any issues without generating a file.

### CLI – Read from file

```bash
anorm generate --file story.txt
```

### MCP Server

Start the Norma MCP server:

```bash
anorm serve
```

This exposes the tools over stdio (or SSE with `--transport sse`).

### JIRA Connector

Run the JIRA connector (fetches issues labelled `bdd-ready` and submits them):

```bash
python -m antinode_norma.connectors.jira_connector
```

### Python API

```python
import asyncio
from antinode_norma.runner import run_agent_from_raw

async def main():
    result = await run_agent_from_raw("User story...")
    print(result["feature_path"])

asyncio.run(main())
```

For detailed step-by-step instructions with JIRA and OpenRouter, see the [Client Usage Guide](docs/CLIENT_USAGE.md).

---

## Architecture

```text
+-----------------+      +-----------------+
|  JIRA Connector |      |  GitHub Issues  |
+-----------------+      +-----------------+
         |                        |
         +------------+-----------+
                      |
                      v
            +---------------------+
            |  MCP Transport       |
            |  (stdio / SSE)       |
            +---------------------+
                      |
                      v
            +---------------------+
            |  Norma MCP Server    |
            |  (exposes tools)     |
            +---------------------+
                      |
                      v
            +---------------------+
            |  Pure Core (no I/O)  |
            |  - parse_story       |
            |  - compute_quality   |
            |  - generate_gherkin  |
            |  - validate_gherkin  |
            +---------------------+
                      |
                      v
            +---------------------+
            |  Effects             |
            |  (file, LLM)         |
            +---------------------+
```

---

## Project Structure

```text
antinode-norma/
├── antinode_norma/          # Python package
│   ├── core/                # Pure business logic
│   │   ├── schemas.py       # Data schemas
│   │   ├── quality.py       # INVEST quality checks
│   │   ├── parser.py        # Story -> structured data
│   │   ├── gherkin_generator.py
│   │   └── validator.py     # Gherkin validation
│   ├── server/              # MCP server
│   │   └── mcp_server.py
│   ├── connectors/          # External integrations
│   │   └── jira_connector.py
│   ├── utils/               # Helpers
│   │   ├── llm_factory.py   # LLM provider abstraction
│   │   └── file_writer.py
│   ├── cli.py               # Click CLI
│   └── runner.py            # Orchestration
├── bin/
│   └── anorm                # CLI wrapper
├── docs/                    # Documentation
│   ├── CLIENT_USAGE.md      # Client setup guide
│   └── TESTING.md           # Testing guide
├── tests/                   # Test suite
│   ├── unit/                # Fast unit tests
│   ├── integration/         # Tests with real LLM calls
│   └── connectors/          # Connector tests (mocked)
├── .env.example
├── README.md
├── requirements.txt
├── requirements-dev.txt
├── setup.py
├── pyproject.toml
└── pytest.ini
```

---

## LLM Provider Support

Set `LLM_PROVIDER` in `.env`:

| Provider  | Required Env Vars               | Notes |
|-----------|---------------------------------|-------|
| `anthropic` | `ANTHROPIC_API_KEY`             | Uses Claude models |
| `openai`    | `OPENAI_API_KEY`                | Uses GPT models |
| `openrouter`| `OPENROUTER_API_KEY`            | Free/open models via OpenRouter (uses OpenAI SDK) |
| `local`     | `LLM_URL` (local server endpoint) | For self-hosted models |
| `mock`      | None                            | For testing without real LLM |

---

## Testing

The project uses `pytest` with a comprehensive test suite.

Install test dependencies:

```bash
pip install -r requirements-dev.txt
```

Run all tests (unit + integration):

```bash
pytest
```

Run only unit tests (fast, no external calls):

```bash
pytest -m "not integration"
```

Run integration tests (requires `OPENROUTER_API_KEY` set):

```bash
pytest -m integration
```

Generate coverage report:

```bash
pytest --cov=antinode_norma --cov-report=html
```

For detailed testing instructions, see the [Testing Guide](docs/TESTING.md).

---

## Using the Dockerfile

### Build the image

```bash
docker build -t antinode-norma .
```

### Run the CLI

```bash
docker run --rm -e OPENROUTER_API_KEY=sk-or-... antinode-norma anorm generate "Your story..."
```

### Run the MCP server (requires stdio mapping)

For the MCP server, you need to run the container in interactive mode with stdio redirection. This is more complex and typically not needed; the CLI is the main use case.

### Run tests inside the container

```bash
docker run --rm antinode-norma pytest -m "not integration"
```

---

## Docker Compose (Optional)

If you want to include a multi-container setup (e.g., with JIRA mock or database), you can add a `docker-compose.yml`. For this project, a simple Dockerfile suffices.

---

## License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.

---

## Philosophy

Named after the Latin word for *rule* or *standard*, **Norma** ensures that every specification meets a baseline of quality before becoming executable. It is designed with simplicity, data-orientation, and functional purity – principles championed by Rich Hickey.

Built with ❤️ by [Antinode Labs](https://antinodelabs.com/).
