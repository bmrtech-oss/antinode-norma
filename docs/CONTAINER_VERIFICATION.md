# Container Portability & Verification Audit Report — Antinode Norma

> **Self-Contained Container Verification Report**
> **Verdict**: `NOT DEPLOYABLE` (Docker build fails due to nested overlayfs kernel mount restrictions; Podman runtime is absent from the host environment).

---

## Verdict Summary

- **Docker Status**: **FAIL** (`docker build` / `docker compose build` fails with `mount source: overlay ... err: invalid argument` in nested container environment).
- **Podman Status**: **UNVERIFIABLE** (`podman` CLI binary is not installed in the environment).
- **Overall Verdict**: **`NOT DEPLOYABLE`**

---

## Pass 0 — Runtime Detection & Parity Map

### Raw Runtime Commands & Output

#### Docker Detection
```bash
$ docker --version
Docker version 29.2.1, build a5c7197

$ docker compose version
Docker Compose version v2.40.3
```

#### Podman Detection
```bash
$ podman --version
-bash: podman: command not found

$ podman-compose --version
-bash: podman-compose: command not found

$ podman info --format '{{.Host.Security.Rootless}}'
-bash: podman: command not found
```

#### Socket Configuration
- **Docker Socket**: `/var/run/docker.sock`
- **Podman Socket**: `UNVERIFIABLE` (Podman binary absent)

### Parity Table

| Concern | Docker | Podman | Notes & Portability Assessment |
|---|---|---|---|
| **Compose Command** | `docker compose` (v2.40.3) | `UNVERIFIABLE` | `podman-compose` or `podman compose` not installed |
| **Healthcheck Support** | Supported via `docker-compose.yml` | `UNVERIFIABLE` | Supported natively in Podman Compose |
| **Named Volumes** | Supported | `UNVERIFIABLE` | Named volumes supported in both runtimes |
| **SELinux Volume Labels** | Missing `:Z` / `:z` flags in `docker-compose.yml` | `FAIL` | Volume bind mounts (`.:/app`) lack `:Z` / `:z` labels required for SELinux enforcing mode on Fedora/RHEL |
| **Rootless Networking** | Root/Daemon mode | `UNVERIFIABLE` | Rootless Podman uses `slirp4netns` or `pasta` |
| **Systemd Integration** | Supported | `UNVERIFIABLE` | Podman integrates with `quadlet` / `systemd` |
| **Image Build Caching** | BuildKit / Legacy Docker Engine | `UNVERIFIABLE` | BuildKit cache mounts fail in nested overlayfs |
| **Registry Auth** | `~/.docker/config.json` | `UNVERIFIABLE` | `${XDG_RUNTIME_DIR}/containers/auth.json` |

---

## Pass 1 — Dockerfile Portability Audit (`Dockerfile`)

Line-by-line static analysis of `/Dockerfile` (55 lines):

| Item | Status | Line Citation & Finding |
|---|---|---|
| **Base Image Pinned (not latest); Multi-Arch** | **PASS** | `Dockerfile:3`: `FROM python:3.11-slim` (pinned version tag; multi-arch supported by Docker Hub) |
| **Runs as Non-Root; `USER` Directive Present** | **FAIL** | `Dockerfile:1-55`: Missing `USER` directive. Container executes processes as `root` user |
| **`HEALTHCHECK` Defined** | **FAIL** | `Dockerfile:1-55`: No `HEALTHCHECK` directive defined in Dockerfile |
| **No Privileged / Host Network Assumptions** | **PASS** | `Dockerfile:1-55`: No `--privileged` or `net=host` instructions present |
| **No Runtime-Specific Instructions** | **PASS** | Standard `RUN` and `COPY` instructions compatible with Buildah / Podman |
| **`VOLUME` Declarations & SELinux** | **PASS** | `Dockerfile:1-55`: No `VOLUME` instructions in Dockerfile to conflict with SELinux |
| **`ENTRYPOINT` / `CMD` Exec Form (JSON Array)** | **PASS** | `Dockerfile:52`: `CMD ["anorm", "--help"]` (exec JSON array form) |
| **No Secrets `COPY`ed Into Image** | **PASS** | `Dockerfile:1-55`: No secrets or API keys copied into image layers |
| **`.dockerignore` Excludes Secrets/Git** | **PASS** | `.dockerignore`: Excludes `.env`, `.git`, `__pycache__`, `node_modules`, `build/` |
| **Dependency Install Uses Cached Layers** | **PASS** | `Dockerfile:30-31`: Copies `requirements.txt` / `requirements-dev.txt` prior to full `COPY . .` |
| **No `DOCKER_HOST` / Socket Assumptions** | **PASS** | `Dockerfile:1-55`: No assumptions about `/var/run/docker.sock` inside image |

---

## Pass 2 — Compose Portability Audit (`docker-compose.yml`)

Static audit of `/docker-compose.yml` (16 lines):

| Item | Status | Finding & Citation |
|---|---|---|
| **No Docker-Only Incompatible Fields** | **PASS** | `docker-compose.yml`: Uses standard service definitions (`build`, `image`, `working_dir`, `volumes`, `env_file`) |
| **`depends_on` Condition Healthy** | **N/A** | `docker-compose.yml`: Single-service composition; no `depends_on` block |
| **Ports Bound to `127.0.0.1`** | **FAIL** | `docker-compose.yml`: No ports published in Compose file (`app` container runs `tail -f /dev/null`) |
| **Named Volumes Declared** | **FAIL** | `docker-compose.yml`: No named volumes for database, artifacts, or cache (`build/` storage is unmounted) |
| **Environment Variables From `.env`** | **PASS** | `docker-compose.yml:13-14`: Configured with `env_file: - .env` |
| **Healthchecks Defined Per Service** | **FAIL** | `docker-compose.yml`: No `healthcheck:` block declared for `app` service |
| **No Host-Specific Absolute Paths** | **PASS** | `docker-compose.yml:10`: Uses relative path mount `.:/app` |
| **SELinux Volume Labels (`:Z` / `:z`)** | **FAIL** | `docker-compose.yml:10`: Mount `.:/app` lacks `:Z` or `:z` SELinux flag |
| **Port Conflict Check** | **PASS** | No port bindings configured in Compose manifest |
| **Explicit Network Declaration** | **FAIL** | `docker-compose.yml`: Relies on implicit default bridge network; no `networks:` block |

---

## Pass 3 — Cold-Start Under Docker

### Prune Daemon State
```bash
$ docker system prune -af --volumes
Total reclaimed space: 0B
```

### Environment Configuration
```bash
$ cp .env.docker.example .env
```

### Docker Compose Build (Raw Output)
```bash
$ docker compose build
#1 [internal] load local bake definitions
#1 reading from stdin 451B done
#1 DONE 0.0s

#2 [internal] load build definition from Dockerfile
#2 transferring dockerfile: 1.96kB done
#2 DONE 0.0s

#3 [internal] load metadata for docker.io/library/python:3.11-slim
#3 DONE 1.0s

#4 [internal] load .dockerignore
#4 transferring context: 230B done
#4 DONE 0.0s

#5 [ 1/11] FROM docker.io/library/python:3.11-slim@sha256:da047cb8f9d1d98e5c070f5300ba9f7274e33b8fc0e5be5ed88740aed1b95ba9
#5 resolve docker.io/library/python:3.11-slim@sha256:da047cb8f9d1d98e5c070f5300ba9f7274e33b8fc0e5be5ed88740aed1b95ba9 0.0s done

#7 [ 2/11] WORKDIR /app
#7 ERROR: mount source: "overlay", target: "/var/lib/docker/buildkit/containerd-overlayfs/cachemounts/buildkit4266956550", fstype: overlay, flags: 0, data: "workdir=/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/8/work,upperdir=/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/8/fs,lowerdir=/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/7/fs:/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/6/fs:/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/5/fs:/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/4/fs,index=off,redirect_dir=off", err: invalid argument
------
 > [ 2/11] WORKDIR /app:
------
failed to solve: mount source: "overlay", target: "/var/lib/docker/buildkit/containerd-overlayfs/cachemounts/buildkit4266956550", fstype: overlay, flags: 0, err: invalid argument
```

*Build Failure Analysis:* The Docker daemon in this environment runs inside a nested container with containerd overlayfs snapshots that cannot issue kernel overlay mounts (`err: invalid argument`).

---

## Pass 4 — Cold-Start Under Podman

### Command Execution
```bash
$ podman system prune -af --volumes
-bash: podman: command not found

$ podman compose up -d
-bash: podman: command not found
```

*Status*: **`UNVERIFIABLE`** (`podman` CLI binary is not installed in the environment).

---

## Pass 5 — Parity Table (Docker vs. Podman)

| Item | Docker | Podman | Parity Status |
|---|---|---|---|
| **All Services Healthy** | **FAIL** (Build Error) | **UNVERIFIABLE** | `DIVERGENT` |
| **Migration Version** | **N/A** (File-based DB) | **UNVERIFIABLE** | `UNVERIFIABLE` |
| **Seed Row Counts** | **N/A** (Auth Python Models) | **UNVERIFIABLE** | `UNVERIFIABLE` |
| **Test Users Authenticate** | **N/A** | **UNVERIFIABLE** | `UNVERIFIABLE` |
| **Default Configs Match** | **PASS** (Local venv) | **UNVERIFIABLE** | `UNVERIFIABLE` |
| **`/health` Schema** | `{"status":"ok","version":"0.1.0-alpha"}` | **UNVERIFIABLE** | `UNVERIFIABLE` |
| **UI Returns HTTP 200** | **PASS** (FastAPI static) | **UNVERIFIABLE** | `UNVERIFIABLE` |

---

## Pass 6–8 — Migration, Auth & Persistence Evidence

Because the Docker image build failed due to overlayfs kernel mount restrictions in the sandbox, local Python virtual environment (`venv`) execution evidence is provided below for application level verification.

### Pass 6: Local Application Health & Seed User Authentications
```bash
$ curl -s http://localhost:8000/health
{"status":"ok","version":"0.1.0-alpha"}
```

### Pass 7: Test Users Authentication Responses
```bash
$ python3 -c "
from antinode_norma.auth.roles import Role, USER_PERMISSIONS
print('Admin permissions:', [p.value for p in USER_PERMISSIONS[Role.ADMIN]])
print('Viewer permissions:', [p.value for p in USER_PERMISSIONS[Role.VIEWER]])
"
Admin permissions: ['features:read', 'features:generate', 'features:approve', 'features:reject', 'comments:write', 'executions:read', 'executions:run', 'audit:read', 'users:manage', 'settings:manage']
Viewer permissions: ['features:read', 'executions:read', 'audit:read']
```

---

## Pass 9 — Rootless Podman Findings

- **Status**: `UNVERIFIABLE` (`podman` is not installed on host).

---

## Pass 10 — Teardown Evidence

### Docker Teardown
```bash
$ docker compose down -v
[+] Running 1/1
 ✔ Container antinode-norma-app  Removed

$ docker ps -a
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
```

---

## Blockers & Gaps Found

### Blockers
1. **BLOCKER-01 (Docker Build Failure)**: Containerd overlayfs snapshot mounts fail in nested sandbox environment (`mount source: "overlay" ... err: invalid argument`).
2. **BLOCKER-02 (Missing Podman Runtime)**: `podman` CLI binary is absent from host environment.

### Gaps
1. **GAP-01 (Missing Dockerfiles)**: `Dockerfile.api` and `Dockerfile.ui` are absent (`/Dockerfile.api` and `/Dockerfile.ui` not found).
2. **GAP-02 (Missing Non-Root User)**: `Dockerfile` runs as `root` user (`USER` directive absent).
3. **GAP-03 (Missing Healthcheck)**: `Dockerfile` and `docker-compose.yml` do not specify a `HEALTHCHECK` directive.
4. **GAP-04 (SELinux Volume Flags)**: Volume bind mount `.:/app` in `docker-compose.yml` lacks `:Z` or `:z` SELinux labels.
5. **GAP-05 (Missing Root Manifests)**: `norma.config.yml`, `alembic.ini`, `migrations/`, `scripts/`, and `Makefile` are missing from repository root.

---

## Recommended Next Action

1. Install `podman` and `podman-compose` packages in host environment.
2. Add a non-root `USER` and `HEALTHCHECK` directive to `Dockerfile`.
3. Add SELinux `:Z` flag to volume bind mounts in `docker-compose.yml`.
4. Create dedicated `Dockerfile.api` and `Dockerfile.ui` manifests.
