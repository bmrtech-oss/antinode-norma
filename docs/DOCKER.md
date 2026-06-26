# Docker and Local Development

This project is fully containerized so new developers can run the entire system locally using Docker or Podman.

## Overview

The repository includes:

- `Dockerfile` — builds a development image with Python, Node.js, and Playwright dependencies.
- `docker-compose.yml` — starts the local app container and exposes the project workspace.
- `.dockerignore` — excludes temporary artifacts from the build context.

## Prerequisites

- Docker or Podman installed locally
- `docker compose` or `podman compose` / `podman-compose`
- A `.env` file based on `.env.example` or `.env.docker.example`

## Build the image

From the repository root:

```bash
docker compose build
```

If using Podman:

```bash
podman compose build
```

If your Podman installation uses the legacy wrapper:

```bash
podman-compose build
```

## Local development mode

For a fully local containerized workflow, copy `.env.docker.example` to `.env` and use the seeded local configuration:

```bash
cp .env.docker.example .env
```

This configuration uses `LLM_PROVIDER=mock` and enables the code generation defaults needed for a local demo.

You can also explore the local seed example in `examples/seed/README.md`.

## Run the CLI inside the container

To execute the CLI from the container:

```bash
docker compose run --rm app anorm generate "As a user, I want to reset my password so that I can regain access."
```

For Podman:

```bash
podman-compose run --rm app anorm generate "As a user, I want to reset my password so that I can regain access."
```

## Run the test suite

### Fast unit tests

```bash
docker compose run --rm app pytest -m "not integration"
```

### Full tests

```bash
docker compose run --rm app pytest
```

### Run a specific Python file

```bash
docker compose run --rm app pytest tests/unit/codegen/test_cli_commands.py
```

## Use an interactive shell

If you want to inspect the container or run commands interactively:

```bash
docker compose run --rm app bash
```

## External connector notes

The containerized local workflow covers the core application, code generation, and test generation paths. Optional connectors such as JIRA, TestRail, Slack, and Teams still require real service endpoints and credentials if you want to exercise those connector flows.

For local development without external services, set `LLM_PROVIDER=mock` and use the project’s core CLI and codegen commands.

## Notes

- The `docker-compose.yml` mounts the repository into `/app`, so file changes on the host are immediately visible inside the container.
- The `.env` file is loaded automatically by `docker compose` via `env_file`.
- The development image installs Python dependencies, development dependencies, Node.js dependencies, and Playwright browsers.

## Troubleshooting

If Docker or Podman cannot install Playwright browsers, verify the container platform and available disk space. On WSL, use the Linux Docker engine and run the commands from the project root.
