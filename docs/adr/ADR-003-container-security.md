# ADR-003: Container Security, Portability, and Concurrency Remediation

**Single-file architecture decision record. Version 1 — PROPOSED.**

**Status:** Proposed
**Date:** 2026-09-19
**Deciders:** Engineering Lead, Security Lead, DevOps Lead, QA Architect
**Predecessor:** ADR-001 v6 (implemented); ADR-002 v3 (proposed)
**Trigger:** Adversarial Container Security & Resiliency Audit — verdict `NOT DEPLOYABLE`
**Nature:** Targeted remediation. No architectural change.
**New tasks:** 14, across 4 phases (C1–C4)
**Duration:** 2–3 weeks
**Sequencing:** Executes **in parallel with ADR-002 H1–H3**, converging before ADR-002 H4.

---

## 1. Context

### 1.1 Trigger

An adversarial container audit on branch `task/P0-T01-secrets-strategy-12288361790416289109` returned an overall verdict of **`NOT DEPLOYABLE`**. The audit exercised 13 attack vectors across Docker and Podman runtimes. Five failed critically; three failed at high or medium severity; one was unverifiable due to the absence of a Podman host in the audit environment.

The audit is recorded in `docs/audits/CONTAINER_ADVERSARIAL_AUDIT_2026-09-19.md`.

### 1.2 Failure Summary

| # | Finding | Severity | Runtime |
|---|---|---|---|
| 2 | Application and Playwright run as root (UID 0) | **CRITICAL** | Docker / Podman |
| 4 | No HEALTHCHECK; PID 1 `tail -f /dev/null` masks crashes | **CRITICAL** | Docker / Podman |
| 6 | File-based SQLite locks under concurrent replicas | **CRITICAL** | Docker / Podman |
| 9 | Volume mount `.:/app` lacks SELinux `:Z` | **CRITICAL** | Podman (RHEL/Fedora) |
| 1 | `ENV OPENROUTER_API_KEY` leaks key name in image history | HIGH | Docker / Podman |
| 11 | Podman pod semantics unverified | HIGH | Podman |
| 13 | Rootless port binding < 1024 fails | HIGH | Podman |
| 3 | `python:3.11-slim` floating tag | MEDIUM | Docker / Podman |
| 10 | Offline build fails on pip/npm network dependency | MEDIUM | Docker / Podman |

Four methods passed (seed idempotency, config drift, port collision, cross-runtime handoff) and require no action.

### 1.3 Why Now

Three reasons:

1. **Enterprise buyers** run their own container audits before any paid pilot. These findings would fail that audit.
2. **Podman portability** was added as a hard requirement (per ADR-002 §14). The current image violates that requirement on any SELinux-enforcing host.
3. **The concurrency failure (Method 6)** is a latent production bug, not a container-only concern. It will manifest in any multi-replica deployment.

### 1.4 Relationship to ADR-002

ADR-003 **does not replace** ADR-002. The two run in parallel:

- ADR-002 owns the enterprise-readiness layer (DR, observability, API versioning, migration, cache FPR, plugin security).
- ADR-003 owns the container layer (root user, healthchecks, SELinux, concurrency, build resilience).

They converge before ADR-002 H4 (operational maturity). The combined release is v2.1.0.

---

## 2. Decision

**We will remediate all critical and high container findings through 14 additive tasks across 4 phases (C1–C4), delivered in 2–3 weeks, in parallel with ADR-002 H1–H3.**

1. **Critical findings are non-negotiable.** Methods 2, 4, 6, and 9 must be fixed before any deployable verdict.
2. **No re-architecture.** The container topology (single API image, optional UI image, SQLite or Postgres) is preserved.
3. **Docker and Podman parity is a hard requirement.** Any fix that works on Docker but not Podman is a failure.
4. **Runtime-agnostic verification.** Every fix is verified under both runtimes on a clean daemon.
5. **Security-first build.** Secrets are never baked into image layers; base images are digest-pinned.
6. **Concurrency correctness.** SQLite is replaced as the default multi-replica backend; Postgres becomes the default for any environment with more than one API replica.

---

## 3. Consequences

### Positive

- **Audit passes:** Overall verdict moves from `NOT DEPLOYABLE` to `DEPLOYABLE` under both runtimes.
- **Kernel-hardening:** Non-root execution eliminates the container-escape attack surface.
- **Enterprise-ready:** SELinux, healthchecks, and digest-pinned bases satisfy first-pass security review.
- **Concurrency-safe:** Multi-replica deployments no longer corrupt or lock the database.
- **Build reproducibility:** Digest pinning and offline-friendly builds produce identical images across environments.
- **Podman-verified:** Portability claim moves from unverified to validated.

### Negative

- **Requires a Postgres container** for multi-replica deployment (adds an infra dependency).
- **Requires a rebuild of the base image layer** (digest pinning invalidates existing caches).
- **Root-user migration** may break plugins or scripts that assume root filesystem access.
- **+14 tasks, +2–3 weeks** added to the schedule; converges before ADR-002 H4.

### Neutral

- Single-replica development mode still works with SQLite.
- CLI remains the primary automation interface.
- ADR-001 v6 and ADR-002 v3 decisions unchanged.

---

## 4. Remediation Phase Plan

Four phases. 14 tasks. 2–3 weeks.

### Phase C1 — Critical Security Fixes
**Duration:** Week 1 (4–5 days)
**Goal:** Remove root execution, add healthchecks, eliminate secret leakage.

| Task | Title | Audit Method | Approval |
|---|---|---|---|
| **C1-T01** | Non-root execution in all Dockerfiles | 2 | Yes |
| **C1-T02** | HEALTHCHECK in Dockerfile and compose | 4 | Yes |
| **C1-T03** | Remove secrets from image layers | 1 | Yes |
| **C1-T04** | Digest-pin base images | 3 | Yes |

**C1-T01 — Non-Root Execution**
Every `Dockerfile` (Dockerfile, Dockerfile.api, Dockerfile.ui) gains:
- `RUN useradd -m -u 1000 -s /bin/bash appuser`
- `RUN chown -R appuser:appuser /app`
- `USER appuser` before `ENTRYPOINT`
- Playwright browser install runs as `appuser` with `PLAYWRIGHT_BROWSERS_PATH=/home/appuser/.cache/ms-playwright`
- Verification: `docker compose exec api whoami` returns `appuser` under both runtimes.

**Rationale:** Method 2 flagged UID 0 as a container-escape vector. Non-root is the single highest-impact fix.

**C1-T02 — HEALTHCHECK**
Every service in `docker-compose.yml` gains:
- `healthcheck:` block with `interval: 10s`, `timeout: 3s`, `retries: 3`, `start_period: 30s`
- API: `curl -f http://localhost:8000/health || exit 1`
- UI: `curl -f http://localhost:3000/ || exit 1`
- DB: `pg_isready` (Postgres) or `sqlite3 :memory: 'select 1'` (SQLite)
- `depends_on` conditions updated to `service_healthy`

**Rationale:** Method 4 found that `tail -f /dev/null` masks crashes. Without healthchecks, `depends_on: service_started` does not guarantee downstream readiness.

**C1-T03 — Remove Secrets from Image Layers**
- Remove `ENV OPENROUTER_API_KEY=${OPENROUTER_API_KEY}` from `Dockerfile:45`
- Use BuildKit build secrets: `RUN --mount=type=secret,id=openrouter_key ...`
- Runtime secrets injected only via `env_file` (already present) or orchestrator secret store
- Add `docker history --no-trunc <image> | grep -i -E 'api_key|token|secret|password'` to CI as a gate
- Verification: no key name appears in `docker history`.

**Rationale:** Method 1 flagged `ENV` leakage. Even the variable *name* in layer metadata is an information disclosure that fails enterprise audits.

**C1-T04 — Digest-Pin Base Images**
- Replace `FROM python:3.11-slim` with `FROM python:3.11-slim@sha256:<digest>`
- Same for `node:20-alpine`, `postgres:16-alpine`, `nginx:1.27-alpine`
- Add `docs/BASE_IMAGE_DIGESTS.md` with the resolved digest and the date it was captured
- Add a quarterly task to review and refresh digests (tracked in `docs/SCHEDULE.md`)
- Verification: two consecutive builds produce identical image digests.

**Rationale:** Method 3 flagged floating tags as a supply-chain risk. Digest pinning is the OCI-recommended defense.

**Exit criteria:** All four fixes verified under both runtimes; CI gate added for secret scanning of image history.

---

### Phase C2 — Podman Parity
**Duration:** Week 2 (3–4 days)
**Goal:** Make the stack work identically under rootless Podman on SELinux-enforcing hosts.

| Task | Title | Audit Method | Approval |
|---|---|---|---|
| **C2-T01** | SELinux labels on volume mounts | 9 | Yes |
| **C2-T02** | Rootless port binding strategy | 13 | Yes |
| **C2-T03** | Podman pod semantics documentation | 11 | Yes |

**C2-T01 — SELinux Labels**
- Update all bind mounts in `docker-compose.yml` from `.:/app` to `.:/app:Z` (private) or `:z` (shared)
- Document in `docs/CONTAINER_RUNTIME.md` which mounts use `:Z` vs `:z` and why
- Add a CI check that fails if any bind mount lacks a label
- Verification: `podman compose up -d` succeeds on Fedora 40 with SELinux enforcing; no `ausearch -m avc` denials.

**Rationale:** Method 9 flagged that `.:/app` fails on any SELinux-enforcing host. This is the single most common Podman failure in enterprise environments.

**C2-T02 — Rootless Port Binding**
- Change default API port from 8000 to a configurable `NORMA_API_PORT` (default 8000)
- Change default UI port from 3000 to `NORMA_UI_PORT` (default 3000)
- Document the sysctl override for ports < 1024: `sysctl net.ipv4.ip_unprivileged_port_start=0`
- Add a preflight check in `scripts/verify-runtime.sh` that fails fast with a clear message if a privileged port is requested under rootless Podman
- Verification: rootless Podman binds 8000 and 3000 without sysctl changes; binding 80 gives a clear error.

**Rationale:** Method 13 flagged the failure. The fix is not to require sysctl changes — it is to default to unprivileged ports and document the override for users who need < 1024.

**C2-T03 — Podman Pod Semantics**
- Install Podman in the CI matrix (Fedora runner or Ubuntu with Podman repo)
- Run the full cold-start and teardown sequence under `podman compose`
- Document observed differences: pod grouping, `podman pod ps` output, restart semantics, teardown behavior
- Add `docs/CONTAINER_RUNTIME.md` section "Docker vs Podman behavioral differences"
- Verification: full UAT checklist passes under both runtimes.

**Rationale:** Method 11 was `UNVERIFIABLE` because Podman was absent. Without a Podman CI runner, portability is a claim, not a fact.

**Exit criteria:** `podman compose up -d` reaches a healthy stack on a clean Fedora host with SELinux enforcing.

---

### Phase C3 — Concurrency Correctness
**Duration:** Week 2 (2–3 days)
**Goal:** Eliminate the SQLite lock under concurrent replicas.

| Task | Title | Audit Method | Approval |
|---|---|---|---|
| **C3-T01** | Postgres as default for multi-replica | 6 | Yes |
| **C3-T02** | SQLite retained for single-replica dev | 6 | No |
| **C3-T03** | Migration serialization (advisory lock) | 6 | Yes |

**C3-T01 — Postgres Default for Multi-Replica**
- Add `postgres:16-alpine` service to `docker-compose.yml` (digest-pinned)
- Change `norma.config.yml` default: `features.database: true` when `NORMA_ENV=production`
- Keep `features.database: false` only when `NORMA_ENV=development` and `replicas=1`
- Add a preflight check in `scripts/verify-runtime.sh` that fails if `replicas > 1` and `database: false`
- Update `docs/CONFIGURATION.md` with the deployment matrix
- Verification: `docker compose up -d --scale api=3` succeeds and all three replicas pass healthchecks.

**Rationale:** Method 6 flagged file-based SQLite as a hard failure under multi-replica. Postgres is the standard answer and is already supported by the codebase.

**C3-T02 — SQLite Retained for Dev**
- Document the single-replica constraint in `docs/CONFIGURATION.md`
- Add a warning log at startup: `SQLite backend detected; multi-replica not supported`
- Keep SQLite as the default for `norma init` and local dev
- Verification: single-replica dev stack still uses SQLite and starts in under 30 seconds.

**Rationale:** Removing SQLite entirely would slow local development. The constraint must be documented, not eliminated.

**C3-T03 — Migration Serialization**
- Wrap Alembic migration in a Postgres advisory lock: `SELECT pg_advisory_lock(<migration_id>)`
- On SQLite, use a file lock (`flock`)
- Make the migration step idempotent (already verified for seed; extend to migrations)
- Verification: start two API replicas simultaneously; exactly one runs migrations; the other waits and proceeds.

**Rationale:** Even with Postgres, concurrent migrations cause race conditions. The advisory lock pattern is standard.

**Exit criteria:** Three API replicas start cleanly against one Postgres; migrations run exactly once.

---

### Phase C4 — Build Resilience and Verification
**Duration:** Week 3 (2–3 days)
**Goal:** Make builds reproducible and offline-capable; verify all fixes.

| Task | Title | Audit Method | Approval |
|---|---|---|---|
| **C4-T01** | Offline-capable build | 10 | Yes |
| **C4-T02** | Container CI matrix (Docker + Podman) | — | Yes |
| **C4-T03** | Cold-start verification script | — | Yes |
| **C4-T04** | Post-remediation audit re-run | — | Yes |

**C4-T01 — Offline-Capable Build**
- Add `pip download -r requirements.txt -d vendor/pip` and `npm ci --prefer-offline --cache vendor/npm` stages
- Support `--build-arg OFFLINE=true` to skip network fetches
- Document the offline build path in `docs/CONTAINER_RUNTIME.md`
- Verification: build succeeds with network disabled when `vendor/` is populated.

**Rationale:** Method 10 flagged offline builds as `PARTIAL`. For air-gapped enterprise deployments, offline build is a hard requirement.

**C4-T02 — Container CI Matrix**
- Add GitHub Actions matrix: `runtime: [docker, podman]` × `os: [ubuntu-22.04, fedora-40]`
- Run cold-start, healthcheck wait, UAT smoke, and teardown under each combination
- Fail the job on any divergence between runtimes
- Verification: CI is green on all four combinations.

**Rationale:** Method 11 was unverifiable because Podman was absent from CI. Portability requires continuous verification, not a one-time audit.

**C4-T03 — Cold-Start Verification Script**
- `scripts/verify-runtime.sh`: detects Docker or Podman, runs cold-start, waits for health, verifies migrations, verifies seed, verifies test users, tears down
- Single command: `make verify-both`
- Exit code 0 only if all checks pass
- Verification: script passes on a clean daemon for both runtimes.

**Rationale:** A repeatable script is the difference between a one-time fix and a maintained capability.

**C4-T04 — Post-Remediation Audit Re-run**
- Re-run the full adversarial audit (13 methods) against the remediated branch
- Publish `docs/audits/CONTAINER_ADVERSARIAL_AUDIT_v2.md`
- Target verdict: `DEPLOYABLE` under both runtimes
- Verification: all 13 methods report `PASSED` or `UNVERIFIABLE` (no `FAILED`).

**Rationale:** The audit is the acceptance test for ADR-003. Without re-running it, the fix is unverified.

**Exit criteria:** CI matrix green; verification script passes; audit v2 published with `DEPLOYABLE` verdict.

---

## 5. Timeline

```text
Week:  1     2     3
C1     ██████
C2           ██████
C3           ████
C4                 ██████
```

**Critical path:** C1-T01 → C2-T01 → C3-T01 → C4-T04.

**Convergence with ADR-002:**

| ADR-002 phase | ADR-003 phase | Shared surface |
|---|---|---|
| H1 (score/timeline docs) | — | Independent |
| H2 (DR, observability, API versioning) | C3 (Postgres default) | Shared DB config |
| H3 (plugin security, cache FPR) | C1 (non-root), C2 (SELinux) | Shared Dockerfile |
| H4 (regression gate, release) | C4 (CI matrix, verification) | Shared CI |

ADR-003 must complete C1–C3 before ADR-002 H4 begins.

---

## 6. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Non-root migration breaks Playwright browser install | Medium | High | Pre-build browser cache as `appuser`; test under both runtimes in CI |
| Postgres default increases local dev startup time | Medium | Low | Keep SQLite for `NORMA_ENV=development`; document trade-off |
| SELinux labels break Docker volume permissions | Low | Medium | `:Z` is honored by Docker as a no-op when SELinux is disabled |
| Digest pinning causes stale base images | Medium | Low | Quarterly review task; documented in `docs/BASE_IMAGE_DIGESTS.md` |
| Podman CI runner unavailable | Low | High | Use Fedora container or GitHub's `ubuntu-latest` with Podman PPA |
| Plugin compatibility breaks under non-root | Medium | Medium | Test plugin SDK under `appuser`; document filesystem expectations |
| Offline build increases image size | Low | Low | `vendor/` is a build-stage-only layer; not copied to final image |
| Migration advisory lock not supported on SQLite | Low | Medium | Fall back to `flock`; test both paths |
| Audit v2 still finds failures | Medium | High | Treat as release blocker; iterate before shipping v2.1.0 |

---

## 7. Definition of Done (ADR-003 additions)

- [ ] `docker compose exec <service> whoami` returns `appuser` under both runtimes
- [ ] Every service has a HEALTHCHECK and reports healthy within 120s
- [ ] `docker history --no-trunc <image>` contains no key, token, or secret names
- [ ] All base images are digest-pinned; two builds produce identical digests
- [ ] All bind mounts carry SELinux `:Z` or `:z` labels
- [ ] Rootless Podman cold-start succeeds without sysctl changes
- [ ] Three API replicas start cleanly against one Postgres; migrations run exactly once
- [ ] Offline build succeeds with network disabled when `vendor/` is populated
- [ ] CI matrix green on Docker + Podman, Ubuntu + Fedora
- [ ] Audit v2 published with `DEPLOYABLE` verdict

---

## 8. Score Impact

ADR-003 does not change the ADR-002 score model. It ensures the container layer does not block the score.

| Dimension | ADR-002 Target | ADR-003 Impact |
|---|---|---|
| Enterprise readiness | 9.5 | **Required to reach 9.5** — DR and observability depend on a deployable container |
| Determinism | 9.5 | Unchanged |
| All others | Unchanged | Unchanged |

**Published statement:** ADR-003 is a prerequisite for ADR-002's enterprise-readiness target. Without it, the platform cannot be deployed to any environment with a security review, so the enterprise-readiness dimension cannot exceed 6.0.

---

## 9. Alternatives Considered

| Alternative | Why rejected |
|---|---|
| Fix only the four CRITICAL findings | HIGH and MEDIUM findings (secret leakage, digest drift, Podman parity) fail the next audit |
| Replace SQLite entirely with Postgres | Breaks local dev speed; SQLite is appropriate for single-replica dev |
| Require `sysctl` change for rootless ports | Host-level change is not acceptable for a containerized product; unprivileged defaults are |
| Defer Podman support to a later release | Podman was declared a hard requirement in ADR-002 §14; deferral invalidates that decision |
| Sandbox via gVisor / Kata | Overkill for v2.1.0; non-root + healthchecks + SELinux cover the audit findings |
| Rebuild the Dockerfiles from scratch | Existing structure is sound; targeted fixes are cheaper and less risky |

---

## 10. Status Tracking

| Phase | Tasks | Status | Blocked By |
|---|---|---|---|
| C1 — Critical Security Fixes | 4 | Not started | — |
| C2 — Podman Parity | 3 | Not started | C1 |
| C3 — Concurrency Correctness | 3 | Not started | C1 |
| C4 — Build Resilience & Verification | 4 | Not started | C2, C3 |
| **Total** | **14** | **0/14** | — |

---

## 11. Relationship to Other ADRs

| ADR | Relationship |
|---|---|
| ADR-001 v6 | Container topology unchanged; ADR-003 fixes defects in the delivered implementation |
| ADR-002 v3 | Runs in parallel; converges before ADR-002 H4 |
| Aegis v15.2 | Blocked until ADR-003 and ADR-002 complete |

**Sequencing:** ADR-003 (2–3 weeks) ∥ ADR-002 (5–6 weeks) → v2.1.0 release → Aegis v15.2 P0.

---

## 12. Approval

| Role | Name | Decision | Date |
|---|---|---|---|
| Engineering Lead | — | Pending | — |
| Security Lead | — | Pending | — |
| DevOps Lead | — | Pending | — |
| QA Architect | — | Pending | — |

Upon approval, C1-T01 is opened as a task branch and ADR-003 enters execution.

---

## 13. Changelog

| Version | Date | Change |
|---|---|---|
| **v1** | **2026-09-19** | **Initial ADR. 14 tasks across 4 phases. Addresses 9 of 13 audit methods (4 passed, no action). PROPOSED.** |

---

**End of ADR-003 v1.**

**Total tasks: 14.**
**Total phases: 4 (C1–C4).**
**Duration: 2–3 weeks.**
**Verdict target: DEPLOYABLE under both Docker and Podman.**
**Sequencing: parallel with ADR-002; converges before ADR-002 H4.**

**Execution begins at C1-T01 upon approval.**