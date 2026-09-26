# Local Development Command Reference

Last updated: 2026-09-25

Copy-paste commands for engineers and QA. The native Windows path is suited to
Python/UI development and tests. Use Fedora WSL2 with Podman when validating
the containerized PostgreSQL, HTTP, or MCP setup. Local startup uses the mock
LLM provider and does not need API credentials.

For onboarding details and troubleshooting, see
[Container Runtime Guide](CONTAINER_RUNTIME.md) and [Local Runbook](LOCAL_RUNBOOK.md).

## Windows: Python and UI

Run from the repository root in PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e . -r requirements-dev.txt
```

Seed deterministic local examples (safe to repeat):

```powershell
$env:LLM_PROVIDER = "mock"
.\.venv\Scripts\python.exe -m antinode_norma.cli seed-local --reset
```

Start the API in one terminal:

```powershell
$env:LLM_PROVIDER = "mock"
.\.venv\Scripts\python.exe -m uvicorn antinode_norma.server.api:app --host 127.0.0.1 --port 8000 --reload
```

Start the UI in a second terminal:

```powershell
Set-Location ui
npm install
npm run dev
```

Open `http://localhost:3000`. The Vite dev server proxies `/api` and `/health`
to the API at port `8000`. Check readiness with:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

## Fedora WSL2: Podman Stack

Enter the Fedora distribution from PowerShell, then run these commands inside
the repository checkout in Fedora:

```bash
podman --version
podman compose version
podman compose --profile local config
podman compose --profile local up --build -d
podman compose ps
curl --fail http://localhost:8000/health
```

The local profile starts PostgreSQL, applies migrations, seeds fixtures, and
starts the HTTP and MCP services. Visit `http://localhost:8000/` for the
container-served UI. Useful operations:

```bash
podman compose logs -f app-http
podman compose logs local-seed local-migrate
podman compose --profile mcp run --rm app-mcp
podman compose --profile local down
```

For an MCP-only first run from a clean checkout, build the shared image first:

```bash
podman compose --profile http build app-http
podman compose --profile mcp run --rm app-mcp
```

Observability containers are excluded from the normal local stack. Start them
only when needed with `podman compose --profile observability up -d`.

To delete the local PostgreSQL volume as well as stop the stack, use
`podman compose --profile local down -v`. This removes all database data for
this Compose project. For Docker, replace `podman compose` with `docker compose`.

## QA and Regression Checks

From the repository root, using the Windows virtual environment:

```powershell
# Full Python suite
.\.venv\Scripts\python.exe -m pytest -q --no-cov

# Structured import and generation API tests
.\.venv\Scripts\python.exe -m pytest tests/unit/test_import_api.py -q --no-cov

# Bootstrap, seed, and Compose contract checks
.\.venv\Scripts\python.exe -m pytest tests/integration/test_adr013_bootstrap.py -q --no-cov

# Inspect available CLI commands
.\.venv\Scripts\python.exe -m antinode_norma.cli --help
```

Run UI checks from `ui/`:

```powershell
npm run lint
npm run typecheck
npm test
npm run build
npm run ci:ui
```

`ci:ui` includes the UI quality Playwright tests. Install browsers if the local
Playwright environment asks for them:

```powershell
npx playwright install
```

## Reset Local Files

The seed output and SQLite import/job store live under `.runtime/` by default.
To remove generated local fixtures and files from PowerShell:

```powershell
Remove-Item -Recurse -Force .runtime\local-seed -ErrorAction SilentlyContinue
Remove-Item -Force .runtime\local-seed-complete.json -ErrorAction SilentlyContinue
```

For the container database, use the Compose volume removal command above.
Never put real credentials in the mock local environment or commit `.env`,
`.runtime/`, or generated test artifacts.