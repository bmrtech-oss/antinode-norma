# Container Runtime Guide

This guide is the local runtime companion to ADR-013. Fedora 44 under WSL2 is
supported through rootless Podman. Docker Desktop is optional and is not
required on Windows.

## Clean-Clone Onboarding

A new test engineer can use this sequence from a clean checkout. It uses the
mock provider and does not require an API key.

From Windows PowerShell:

```powershell
wsl.exe -l -v
wsl.exe -d FedoraLinux-44
```

Inside Fedora, from the repository root:

```bash
sudo dnf install -y python3-pip python3-devel gcc-c++ make
podman --version
podman compose version
podman compose --profile local config
podman compose --profile local up --build
```

In another Fedora terminal, verify the running application:

```bash
curl --fail http://localhost:8000/health
test -f .runtime/local-seed-complete.json
python3 -m antinode_norma.cli seed-local
```

Open `http://localhost:8000/` in a browser to use the seeded UI. The local
seed contains four users (`admin`, `reviewer`, `generator`, `viewer`), three
approval states, three feature files, audit/traceability/analytics fixtures,
execution history, plugin metadata, and notification examples. The current
application reads these seed artifacts from `.runtime/local-seed`; it does not
yet claim that every fixture is persisted through PostgreSQL.

To exercise MCP separately, stop the local stack or use a second checkout
terminal and run:

```bash
podman compose --profile http build app-http  # only needed before first MCP-only run
podman compose --profile mcp run --rm app-mcp
```

MCP uses stdio and should be invoked by an MCP client. A terminal that appears
idle is expected; inspect stderr for startup failures.

To reset local state:

```bash
podman compose --profile local down
rm -rf .runtime/local-seed .runtime/local-seed-complete.json
```

Do not commit `.env`, `.runtime/`, generated tests, or container output.

## Fedora WSL2 with Podman

From PowerShell, verify the distro and enter it:

```powershell
wsl.exe -l -v
wsl.exe -d FedoraLinux-44
```

Inside Fedora, verify Podman and Compose:

```bash
sudo dnf install -y python3-pip python3-devel gcc-c++ make
podman --version
podman compose version
```

The repository's Python dependencies are installed inside the image by the
Compose build. For direct host-side Python commands, create an environment and
install the project requirements first:

```bash
python3 -m venv .venv-fedora
. .venv-fedora/bin/activate
python -m pip install -e . -r requirements-dev.txt
```

The `sudo dnf` step is a one-time Fedora prerequisite. The application and
seed commands themselves do not require root privileges.

The repository bind mounts use `:Z` so SELinux relabeling works for private
container mounts. Do not remove those labels on Fedora/Podman hosts.

## Local Profiles

From the repository root inside Fedora:

```bash
podman compose --profile local config
podman compose --profile local up --build
```

The local profile contains:

- `db`: PostgreSQL 16 with a healthcheck and named local volume;
- `local-seed`: deterministic, mock-provider seed data;
- `app-http`: FastAPI and the compiled UI on port `8000`;
- `app-mcp`: the MCP stdio server;
- optional services from the `observability` profile.

For one interface only:

```bash
podman compose --profile http up --build
podman compose --profile http build app-http  # first MCP-only run from a clean checkout
podman compose --profile mcp run --rm app-mcp
```

Start observability separately with `podman compose --profile observability
up -d`.

Check HTTP readiness:

```bash
curl http://localhost:8000/health
```

## Direct Seed

The seed command is safe to rerun and uses no provider credentials:

```bash
python3 -m antinode_norma.cli seed-local --reset
python3 -m antinode_norma.database migrate --database-url sqlite:///.runtime/norma.db
python3 -m antinode_norma.cli seed-local --database-url sqlite:///.runtime/norma.db
```

Seed output is written beneath `.runtime/local-seed/`, which is ignored by Git.
When `DATABASE_URL` is supplied, seed records, users/roles, audit events,
approvals, comments, execution history, costs, import/generation jobs, and flake
history use the shared SQLite/PostgreSQL schema. Fixture files and generated or
binary execution artifacts still live in `.runtime/` or their configured output
directories; PostgreSQL does not store those files. The seed includes synthetic
users, tenant/role records, approvals, feature fixtures, traceability, audit,
analytics, execution, plugin, and notification examples.

## Runtime Modes

The container entrypoint accepts:

```text
NORMA_RUNTIME_MODE=http  # FastAPI/Uvicorn
NORMA_RUNTIME_MODE=mcp   # MCP stdio server
```

HTTP and MCP are separate Compose services by design. Do not run two long-lived
processes through shell backgrounding in one container.

## Troubleshooting

- **Permission denied on bind mounts:** confirm `:Z` labels and restart the
  Podman machine/container after relabeling.
- **Missing Python dependencies:** run the image build from Fedora; do not use
  the Windows virtual environment inside the container.
- **MCP exits immediately:** MCP stdio is a client-driven process; run it with
  an MCP client or `podman compose --profile mcp run --rm app-mcp`.
- **External provider errors:** local mode must use `LLM_PROVIDER=mock`; do not
  add real API keys to the seed environment.
