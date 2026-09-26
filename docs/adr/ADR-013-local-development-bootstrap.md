# ADR-013: Local Development Bootstrap and Configurable Runtime Modes

**Single-file architecture decision record. Version 1.1. Revised after architecture review.**

---

## Metadata

| Field | Value |
|---|---|
| **ADR ID** | ADR-013 |
| **Title** | Make a complete local Norma environment reproducible for new test engineers |
| **Status** | In progress — P13-BOOT-07 partial; release review pending |
| **Date** | 2026-09-25 |
| **Deciders** | Engineering Lead, QA Architect, UX Lead, Security Lead |
| **Related** | ADR-002 (`docs/adr/ADR-002-platfrom-hardening.md`), ADR-003 (`docs/adr/ADR-003-AEGIS.md`), ADR-009 (`docs/adr/ADR-009-frontend-quality-and-theming.md`) |
| **Target Duration** | 2–4 working days |
| **Release Profile** | Local development and test bootstrap only |
| **Approval Required** | Yes; changes Docker/Podman startup, database initialization, and seed behavior |
---

## 1. Context

A new test engineer should be able to clone the repository, start the complete
local application, and begin testing without reconstructing undocumented setup
steps. The current repository has useful ingredients but no single supported
bootstrap path:

- `.env.docker.example` selects the mock LLM provider and avoids provider keys.
- `examples/seed/` contains a sample story and a local feature fixture.
- `docker-compose.yml` builds an `app` container but leaves it running with
  `tail -f /dev/null`.
- The Dockerfile defaults to `anorm --help` and only comments the MCP command.
- The API and MCP server are separate runtime entrypoints.
- ADR-002 §H2-T01, §H2-T02, §H3-T03, and §14 already require migration,
  backup/restore, database readiness, Docker/Podman parity, and SELinux-safe
  bind mounts. ADR-013 must build on those decisions rather than describe the
  database as an entirely future concern.

This creates avoidable onboarding friction and makes local UI, API, MCP, and
approval workflows depend on manual state preparation.

## 2. Decision

Create one supported local bootstrap contract with these properties:

1. **One command:** `docker compose --profile local up --build` starts the
   complete local test environment.
2. **Safe defaults:** local mode uses `LLM_PROVIDER=mock`, local-only example
   credentials, deterministic seed data, and no external provider calls.
3. **Idempotent seed:** a dedicated `anorm seed-local` command or equivalent
   bootstrap script creates or refreshes all test fixtures without duplicating
   records when run repeatedly.
4. **Explicit runtime mode:** the application runtime is selected by
   `NORMA_RUNTIME_MODE`, with supported values:
   - `http`: start FastAPI/Uvicorn;
   - `mcp`: start the MCP stdio server;
   - `all`: start HTTP and MCP using explicitly documented process/container
     topology, not shell backgrounding hidden inside the image.
5. **Compose service modes:** Compose exposes named profiles/services for HTTP
   and MCP so a test engineer can choose either interface without rebuilding:
   - `docker compose --profile http up app-http`
   - `docker compose --profile mcp run --rm app-mcp`
   - `docker compose --profile local up` for the complete local stack.
6. **Seeded fixtures:** the seed package includes representative:
   - CSV and XLSX inputs;
   - Gherkin features and generated-test examples;
   - pending, approved, and rejected approval records;
   - audit events with a valid hash chain;
   - traceability mappings and at least one uncovered requirement;
  - plugin, notification, analytics, and execution-history examples;
  - four deterministic users: `admin`, `reviewer`, `generator`, and `viewer`;
   - mock-provider configuration and example `norma.config.yml`.
7. **Visible readiness:** HTTP mode exposes `/health`; Compose healthchecks and
   seed completion state must be visible in logs. MCP mode must print a clear
   startup failure when the server cannot initialize.
8. **No secrets in seed data:** fixture values are synthetic, `.env` remains
   ignored, and seed output must redact tokens, keys, cookies, and passwords.

## 3. Runtime Contract

The image must accept an overridable command and mode rather than embedding a
single default service choice:

```text
NORMA_RUNTIME_MODE=http  -> uvicorn antinode_norma.server.api:app --host 0.0.0.0 --port 8000
NORMA_RUNTIME_MODE=mcp   -> python -m antinode_norma.server.mcp_server
NORMA_RUNTIME_MODE=all   -> documented supervisor/process topology
```

The preferred deployment shape is separate Compose services for HTTP and MCP.
This keeps HTTP healthchecks and MCP stdio transport independent, makes logs
and restart behavior unambiguous, and avoids running two long-lived processes
through shell tricks in one container.

## 4. Database, Migration, and Seed Contract

The seed command must be safe to rerun:

```text
anorm seed-local --reset
```

Required behavior:

- `--reset` removes only local development state under the configured local
  data directory.
- Without `--reset`, existing records are upserted by stable fixture IDs.
- The command reports counts by fixture family and never prints secrets.
- The command writes a machine-readable completion marker, for example
  `.runtime/local-seed-complete.json`, which is ignored by Git.
- Test fixtures can be loaded without network access or a real LLM key.
- Database migrations run before seed loading and the application waits for the
  database healthcheck. SQLite is supported for single-node local mode;
  PostgreSQL is the multi-process/Compose-compatible mode required by ADR-002.

The seed command uses the same migration and persistence adapters as the
application. File-backed and in-memory stores remain valid for components that
do not yet have database adapters, but the runbook must identify each store and
its reset behavior. Stable fixture IDs must survive a future backend migration.

## 5. Configuration

Commit safe templates, not secrets:

```text
.env.example              # general development template
.env.docker.example       # mock-provider container template
norma.config.example.yml  # runtime and feature defaults
examples/seed/             # deterministic source fixtures
examples/seed/manifest.yml # fixture IDs, versions, and expected counts
```

The bootstrap must document the precedence order:

```text
defaults -> norma.config.yml -> environment -> CLI/runtime override
```

The local profile must default to:

```text
LLM_PROVIDER=mock
NORMA_RUNTIME_MODE=http
NORMA_FEATURE_UNIFIED_AGENT=false
NORMA_FEATURE_GOVERNANCE_AUDIT=false
NORMA_FEATURE_GOVERNANCE_APPROVAL=false
NORMA_FEATURE_EXECUTION_CLOUD=false
```

## 6. Container and Runtime Contract

The implementation must satisfy ADR-002 §14:

- Docker and Podman are supported and verified.
- Bind mounts use `:Z` where required for SELinux-capable Podman hosts.
- Every long-running service has a healthcheck.
- Compose uses `depends_on: condition: service_healthy` for database and API
  readiness dependencies.
- The image uses an exec-form entrypoint or command wrapper with explicit
  `NORMA_RUNTIME_MODE`; it must not hide two daemons behind shell background
  processes.
- `.dockerignore` excludes `.env`, `.git`, caches, local databases, and test
  output.
- `docs/CONTAINER_RUNTIME.md`, `scripts/verify-runtime.sh`, and Make targets
  document Docker and Podman parity.

The preferred topology is:

```text
db -> migrate/seed -> app-http -> ui/browser tests
                    app-mcp  -> MCP client tests
```

`app-http` and `app-mcp` may share the image but must be separate Compose
services so health, logs, restart policy, and stdio transport remain explicit.

## 7. Implementation Plan

| Task | Deliverable | Owner | Approval | Verification |
|---|---|---|---|---|
| P13-BOOT-01 | `anorm seed-local` with stable fixture IDs and reset/upsert behavior | QA Architect | Yes | **Implemented:** `tests/unit/test_local_seed.py`; Fedora smoke command |
| P13-BOOT-02 | Compose profiles/services for HTTP, MCP, DB, migration, and complete local mode | Engineering Lead | Yes | **Implemented:** Fedora 44/Podman local-profile build, PostgreSQL health, migration, seed, HTTP health, and MCP stdio handshake verified; observability is opt-in |
| P13-BOOT-03 | Configurable Docker/Podman runtime command/mode | Engineering Lead | Yes | **Implemented:** shared image built on Fedora/Podman; HTTP and MCP modes verified, including MCP initialize/tools/list over stdio |
| P13-BOOT-04 | Complete synthetic fixture catalog, four users, and example config | QA Architect | No | **Implemented:** `examples/seed/manifest.yml`, `norma.config.example.yml`, `tests/unit/test_local_seed.py` |
| P13-BOOT-05 | New-engineer runbook and container-runtime guide | QA Architect | No | **Implemented:** `docs/CONTAINER_RUNTIME.md`; Fedora/Podman onboarding and smoke commands |
| P13-BOOT-06 | CI/local bootstrap regression | QA Architect | No | **Implemented:** `tests/integration/test_adr013_bootstrap.py`; seed and Compose contract checks |
| P13-BOOT-07 | Database migration and seed persistence adapter | Engineering Lead | Yes | **Partial:** SQLite/PostgreSQL-compatible schema, migration command, seed upserts, import/generation, governance, cost, flake history, and artifact metadata persistence are implemented; other artifact stores need migration |

The first database-backed slice is now implemented for seed records, tenants,
users/roles, audit events, approval requests, comments, execution history, and
LLM cost events. `antinode_norma.database` creates those tables, and Compose
orders `db -> local-migrate -> local-seed -> app-http/app-mcp`. Import and
generation jobs now use the shared SQLite/PostgreSQL boundary, including
portable result upserts and SQLite WAL initialization. Execution-artifact
metadata is indexed in the shared database while binary payloads remain on the
filesystem. Codegen feedback, failure analysis, generated fixture files, and
other remaining stores still use mixed file-backed/SQLite/in-memory persistence.

## 8. Security and Data Boundaries

- Never copy `.env` into the image or commit it.
- Never use real provider credentials in local fixtures or default Compose
  values.
- Redact secrets in seed summaries and startup logs.
- Use synthetic users, tenants, audit data, and approval records.
- Keep cloud execution and real notification channels disabled by default.
- A seed reset must not delete files outside the configured local data root.

## 9. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation / release gate |
|---|---|---|---|
| Seed data diverges from schemas | Medium | High | Versioned manifest, migration-first seed, fixture count checks |
| Duplicate seed records | Medium | Medium | Stable IDs, upsert semantics, reset test, second-run test |
| HTTP/MCP process drift | Medium | High | Separate Compose services, explicit commands, independent healthchecks |
| Podman/SELinux mount failure | Medium | High | `:Z` labels, Podman verification script, documented host prerequisites |
| Local credentials leak | Low | Critical | Mock defaults, `.env` ignore rules, gitleaks, redacted seed output |
| SQLite/PostgreSQL behavior differs | Medium | High | Test both modes where supported; migration and row-count checks |
| Seed reset deletes unintended data | Low | High | Configured data-root boundary and destructive reset test |
| New engineer follows stale docs | Medium | Medium | One canonical runbook, smoke command, last-reviewed date |

## 10. Alternatives Considered

| Alternative | Decision |
|---|---|
| Keep `tail -f /dev/null` and document manual commands | Rejected; it is not a runnable application contract |
| One image with hidden background HTTP and MCP processes | Rejected; unclear health, logs, and restart semantics |
| Require a real LLM provider key for onboarding | Rejected; unsafe and excludes offline testing |
| Seed only one feature file | Rejected; it does not exercise governance, API, MCP, or UI workflows |
| Wait for a relational database before adding bootstrap | Rejected; ADR-002 already defines migration and database readiness work |

## 11. Definition of Done

- [ ] ADR-013 implementation tasks have explicit owners and approval status.
- [ ] Docker and Podman cold-start checks pass with SELinux-safe mounts.
- [ ] Migrations complete before seed and application startup.
- [ ] Seed is idempotent, reset-scoped, and secret-free.
- [ ] HTTP, MCP, and complete local profiles have independent smoke checks.
- [ ] New-engineer runbook succeeds from a clean clone.
- [ ] Backend, UI, MCP, and seed regression tests pass.
- [ ] Rollback/fallback is documented and tested.
- [ ] Release evidence includes commands, fixture version, runtime, and commit.

## 12. Acceptance Criteria

- A new engineer can start the local stack from a clean clone using documented
  commands and no provider credentials.
- HTTP mode serves the UI and `/health` successfully.
- MCP mode starts independently with the documented transport.
- The complete local profile starts all required services and reaches readiness.
- Seed execution is idempotent and populates every listed fixture family.
- UI, API, MCP, approval, audit, traceability, notification, plugin, and
  analytics smoke checks pass against the seeded environment.
- Re-running seed with `--reset` produces the same stable fixture IDs.
- No secrets are committed, printed, or embedded in the image.
- The setup guide states clearly which data is file-backed/in-memory versus
  database-backed.

## 13. Rollback

- Keep the current Docker command available through an explicit `legacy` or
  development override during migration.
- Disable automatic seeding with `NORMA_LOCAL_SEED_ENABLED=false`.
- Revert Compose profile and entrypoint changes independently from fixture
  content.
- Local seed state is disposable and must never be used as production data.

---

**Status:** Proposed for approval. P13-BOOT-01 through P13-BOOT-06 are
implemented as marked above. P13-BOOT-07 remains partial while remaining
artifact stores are migrated; local Fedora/Podman build and runtime smoke checks
are complete. This local bootstrap is for development and QA, not production.

## 14. Revision History

| Version | Date | Change |
|---|---|---|
| v1.0 | 2026-09-25 | Initial bootstrap and runtime-mode proposal |
| **v1.1** | **2026-09-25** | **Corrected ADR references; aligned database/migration assumptions with ADR-002; added Docker/Podman and SELinux requirements; expanded Compose topology, fixture users, risks, DoD, and release gates.** |
| **v1.2** | **2026-09-25** | **Recorded Fedora 44/Podman profile smoke verification and MCP stdio compatibility fix; made observability opt-in and documented remaining persistence scope.** |
| **v1.3** | **2026-09-26** | **Added shared-database execution-artifact metadata persistence while retaining filesystem binary payloads; verified SQLite and PostgreSQL round trips.** |
