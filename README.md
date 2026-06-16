# Antinode Norma

BDD feature file generator with an INVEST quality gate.  
Transform raw user stories into validated Gherkin `.feature` files.  
Built with a data-centric, functional philosophy – inspired by Rich Hickey.

Works with **any LLM** (Claude, GPT, local) and integrates via **MCP** (Model Context Protocol) for tool-based orchestration.

---

## Quick Start

```bash
# Install
git clone https://github.com/antinodelabs/antinode-norma.git
cd antinode-norma
pip install -e .

# Configure
cp .env.example .env
# Edit .env with your API keys

# Generate a feature file
anorm generate "As a user, I want to reset my password so that I can regain access."
```

---

## Features

- INVEST quality assessment – Checks stories against Independent, Negotiable, Valuable, Estimable, Small, Testable.
- Automatic Gherkin generation – Uses your preferred LLM to produce feature files.
- MCP server – Exposes tools (submit_story, improve_story, generate_feature) for integration with connectors (JIRA, GitHub, etc.).
- Provider-agnostic LLM – Switch between Anthropic, OpenAI, or local models via configuration.
- CLI and library – Use as a command-line tool or import into your own system.
- Quality-first – Rejects stories that don't meet INVEST criteria, with actionable suggestions.
- Pure-core design – Business logic is side-effect free, easy to test and extend.

---

## Installation

```bash
git clone https://github.com/antinodelabs/antinode-norma.git
cd antinode-norma
pip install -e .
```

---

## Configuration

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env`:

```ini
# LLM Configuration
LLM_PROVIDER=anthropic   # anthropic, openai, local, mock
ANTHROPIC_API_KEY=sk-...
# OPENAI_API_KEY=sk-...
# LLM_MODEL=claude-3-5-sonnet-20241022
# LLM_TEMPERATURE=0.2
# LLM_MAX_TOKENS=1024

# JIRA (optional)
JIRA_SERVER=https://your-domain.atlassian.net
JIRA_TOKEN=your_personal_access_token
```

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
├── .env.example
├── README.md
├── requirements.txt
├── setup.py
└── pyproject.toml
```

---

## LLM Provider Support

Set `LLM_PROVIDER` in `.env`:

| Provider  | Required Env Vars               |
|-----------|---------------------------------|
| anthropic | `ANTHROPIC_API_KEY`             |
| openai    | `OPENAI_API_KEY`                |
| local     | `LLM_URL` (local server endpoint) |
| mock      | None (for testing)              |

---

## Testing

Run tests (once added):

```bash
pytest tests/
```

---

## Contributing

We welcome contributions! For major changes, please open an issue first.

---

## License

This project is licensed under the MIT License.

---

## Philosophy

Named after the Latin word for *rule* or *standard*, Norma ensures that every specification meets a baseline of quality before becoming executable. It is designed with simplicity, data-orientation, and functional purity – principles championed by Rich Hickey.

Built with ❤️ by Antinode Labs.
