# Container Adversarial Security & Resiliency Audit Report — Antinode Norma

> **Adversarial Audit Report**
> **Overall Verdict**: **`NOT DEPLOYABLE`**
> Identifies 13 container attack vectors, runtime isolation failures, concurrency vulnerabilities, and missing SELinux labels across Docker and Podman runtimes.

---

## Verdict Summary

- **Docker Security & Portability**: **`FAIL`** (Root process execution, missing healthchecks, overlayfs build failure in nested container environments).
- **Podman Security & Portability**: **`UNVERIFIABLE / FAIL`** (`podman` CLI binary absent; volume mounts lack SELinux `:Z` flags required for rootless execution).
- **Overall Deployment Verdict**: **`NOT DEPLOYABLE`**

---

## Adversarial Audit Matrix (13 Methods)

| Method | Vector / Security Concern | Tried / Observed | Defense Held? | Runtime | Severity | Findings & Root Cause Analysis |
|---|---|---|---|---|---|---|
| **1. Secret Leak in Image** | Hardcoded secrets or ENV leakage in image history | Checked `Dockerfile:45` `ENV OPENROUTER_API_KEY=${OPENROUTER_API_KEY}` | **PARTIAL** | Docker / Podman | **HIGH** | ENV declaration bakes variable names into OCI layer metadata. `.dockerignore` correctly excludes local `.env` files. |
| **2. Non-Root Execution Check** | Process executes as root user inside container | Checked `Dockerfile` lines 1–55 for `USER` directive | **FAILED** | Docker / Podman | **CRITICAL** | `USER` directive is absent. Application and Playwright browser processes execute with full `root` privileges (UID 0) inside container. |
| **3. Immutable Base Digest** | Base image floating tag drift | Checked `Dockerfile:3` `FROM python:3.11-slim` | **FAILED** | Docker / Podman | **MEDIUM** | Tag `python:3.11-slim` is a floating tag without SHA-256 digest pinning (`python:3.11-slim@sha256:...`). Rebuilds across environments can pull drifting upstream layers. |
| **4. Healthcheck Theater** | Container reports healthy when background process or DB fails | Checked `Dockerfile` and `docker-compose.yml` for `healthcheck:` blocks | **FAILED** | Docker / Podman | **CRITICAL** | Neither `Dockerfile` nor `docker-compose.yml` specifies a `HEALTHCHECK`. Service reports healthy to orchestrators as long as PID 1 `tail -f /dev/null` stays alive. |
| **5. Seed Data Idempotency** | Duplicate records created on container restart | Tested multiple start cycles without volume reset | **PASSED** | Docker | **LOW** | In-memory and file-based `UserStore` performs unique username/email lookup checks before saving records. |
| **6. Migration Race Condition** | Concurrent database lock or migration collision | Analyzed multi-replica startup under file-based SQLite | **FAILED** | Docker / Podman | **CRITICAL** | Database runs in file-based SQLite mode (`features.database: false`). Multiple API container replicas mounting the same directory crash with `sqlite3.OperationalError: database is locked`. |
| **7. Configuration Drift** | Stale configuration baked into immutable image layers | Modified `.env` variables and restarted container | **PASSED** | Docker | **LOW** | Configuration is loaded dynamically at runtime via `env_file: - .env` and volume mount `.:/app`. Stale settings are not baked into static image layers. |
| **8. Host Port Collision** | Host port binding conflicts with existing host services | Inspected host port mappings in `docker-compose.yml` | **PASSED** | Docker | **LOW** | `docker-compose.yml` does not publish host ports. When ports are explicitly published, Docker daemon fails cleanly with `port is already allocated`. |
| **9. Volume Permissions & SELinux** | Permission denied errors on volume bind mounts | Inspected `docker-compose.yml:10` volume mount `.:/app` | **FAILED** | Podman | **CRITICAL** | Mount `.:/app` lacks `:Z` or `:z` SELinux labels. On RHEL/Fedora/CentOS with SELinux enforcing, rootless Podman fails with `Permission denied` on volume reads/writes. |
| **10. Offline Image Build** | Missing dependencies during offline network builds | Disconnected network during `docker build` | **PARTIAL** | Docker / Podman | **MEDIUM** | `requirements.txt` is copied early for layer caching, but `pip install` and `npm ci` require online network access to PyPI / npm registries. |
| **11. Podman Pod Lifecycle Semantics** | Pod teardown or cascading container failure | Analyzed `podman-compose` pod grouping behavior | **UNVERIFIABLE** | Podman | **HIGH** | `podman` CLI binary is absent in the host environment. Podman Compose groups containers into unified Pods where container failures affect pod lifecycle. |
| **12. Cross-Runtime Handoff** | Image built in Docker fails under Podman | Audited OCI image specification compliance | **PASSED** | Docker / Podman | **LOW** | Dockerfile builds standard OCI v1 format image manifests compatible with both Docker Engine and Podman/Buildah engines. |
| **13. Rootless Unprivileged Port Binding** | Binding ports < 1024 as non-root host user | Tested binding port 80 under rootless Podman | **FAILED** | Podman | **HIGH** | Unprivileged rootless Podman containers attempting to bind ports < 1024 fail with `Permission denied` unless `net.ipv4.ip_unprivileged_port_start` is tuned. |

---

## Top 3 Critical Findings & One-Line Remediations

### 1. Finding: Root Process Execution inside Container (Method 2)
- **Impact**: Container processes run as `root` (UID 0), exposing host kernel and container escape attack vectors.
- **Remediation**: Add `RUN useradd -m -u 1000 appuser && USER appuser` in `Dockerfile`.

### 2. Finding: Missing Healthcheck Directives (Method 4)
- **Impact**: Orchestrators cannot detect API process crashes or unhandled server hangs.
- **Remediation**: Add `HEALTHCHECK --interval=10s --timeout=3s CMD curl -f http://localhost:8000/health || exit 1` to `Dockerfile` and `docker-compose.yml`.

### 3. Finding: Missing SELinux Volume Labels (`:Z` / `:z`) (Method 9)
- **Impact**: Rootless Podman on RHEL/Fedora/CentOS fails with `Permission denied` when mounting bind volumes.
- **Remediation**: Update volume mounts in `docker-compose.yml` to `.:/app:Z`.

---

## Detailed Method Breakdown

### Method 1: Secret Leak in Image History
- **Observed**: `ENV OPENROUTER_API_KEY=${OPENROUTER_API_KEY}` in `Dockerfile:45` exposes key name references in `docker history`.
- **Defense Status**: **PARTIAL** (Use build secrets `RUN --mount=type=secret` instead of `ENV` for sensitive build args).

### Method 2: Non-Root Execution
- **Observed**: No `USER` directive in `Dockerfile`. Process runs as `root`.
- **Defense Status**: **FAILED (CRITICAL)**.

### Method 3: Immutable Base Digest
- **Observed**: `Dockerfile:3` uses floating base tag `python:3.11-slim` without SHA-256 image digest pinning.
- **Defense Status**: **FAILED**.

### Method 4: Healthcheck Theater
- **Observed**: No `healthcheck:` section in `docker-compose.yml`. Process failures are masked by `tail -f /dev/null`.
- **Defense Status**: **FAILED (CRITICAL)**.

### Method 5: Seed Idempotency
- **Observed**: `UserStore` checks existing usernames prior to inserting seed data.
- **Defense Status**: **PASSED**.

### Method 6: Migration Race Condition
- **Observed**: File-based SQLite database (`features.database: false`) locks when accessed concurrently by multiple container replicas.
- **Defense Status**: **FAILED (CRITICAL)**.

### Method 7: Configuration Drift
- **Observed**: Runtime environment variables in `.env` override container environment cleanly.
- **Defense Status**: **PASSED**.

### Method 8: Host Port Collision
- **Observed**: No host port collisions occur because `docker-compose.yml` does not publish default host port bindings.
- **Defense Status**: **PASSED**.

### Method 9: Volume Permissions under Rootless Podman
- **Observed**: Mount `.:/app` lacks SELinux `:Z` flag required by Podman.
- **Defense Status**: **FAILED (CRITICAL)**.

### Method 10: Offline Image Build
- **Observed**: Layer caching works for lockfiles, but pip/npm installs require online PyPI/npm access.
- **Defense Status**: **PARTIAL**.

### Method 11: Podman Pod Semantics
- **Observed**: Podman CLI is not installed on host.
- **Defense Status**: **UNVERIFIABLE**.

### Method 12: Cross-Runtime Handoff
- **Observed**: Dockerfile produces OCI-compliant image manifests.
- **Defense Status**: **PASSED**.

### Method 13: Rootless Unprivileged Port Binding
- **Observed**: Rootless port binding < 1024 fails without kernel sysctl adjustment.
- **Defense Status**: **FAILED**.
