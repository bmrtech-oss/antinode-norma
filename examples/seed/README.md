# Local Seed Example

This folder contains a minimal seed story and instructions for running the full application flow locally using Docker/Podman.

## What is included

- `story.md` – a sample user story and acceptance criteria.
- `features/local_seed.feature` – a simple feature file for local code generation.

## Local run instructions

1. Copy the Docker seed env file:

```bash
cp .env.docker.example .env
```

1. Build the development container:

```bash
docker compose build
```

1. Run the CLI in the container to generate feature output or validate a story:

```bash
docker compose run --rm app anorm generate "As a user, I want to reset my password so that I can regain access."
```

1. Generate executable tests from the local seed feature:

```bash
docker compose run --rm app python -m antinode_norma.codegen.cli.commands generate -f features/local_seed.feature -fw playwright
```

1. Run the unit test suite inside the container:

```bash
docker compose run --rm app pytest -m "not integration"
```

## Notes

- The local seed environment uses `LLM_PROVIDER=mock`, so it does not require API keys.
- The seed feature is intentionally simple and designed to exercise the end-to-end flow.
- If you want to use a real LLM provider, update `.env` and provide the appropriate API keys.
