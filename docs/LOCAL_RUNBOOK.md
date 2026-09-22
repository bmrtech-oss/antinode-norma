# Antinode Norma — Local Development & UAT Runbook

> **Self-contained DevOps Runbook**
> Enables a developer with zero prior knowledge of Antinode Norma to set up, run, test, and perform User Acceptance Testing (UAT) locally before promoting to integration environments.

---

## New Developer Onboarding & End-to-End Verification Plan

Use this path when a developer or QA engineer joins the project and needs to validate the system from a clean machine.

### 1. Prerequisites

Verify these tools first:

```bash
python3 --version
node --version
npm --version
git --version
```

Expected:
- Python 3.10+
- Node 18+ / 20+
- npm available
- Git installed

If any tool is missing, install it before continuing.

### 2. Clone and enter the repo

```bash
git clone https://github.com/bmrtech-oss/antinode-norma.git
cd antinode-norma
```

### 3. Create a local Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
```

### 4. Install project dependencies

```bash
pip install -e .
pip install -r requirements-dev.txt
```

Verify the CLI is installed:

```bash
anorm --version
```

### 5. Configure local environment

```bash
cp .env.example .env
```

For zero-secret local testing, prefer:

```bash
cp .env.docker.example .env
```

Then verify the key values:

```bash
grep -E 'LLM_PROVIDER|OPENAI_API_KEY|ANTHROPIC_API_KEY|OPENROUTER_API_KEY' .env
```

For a local-first environment, use `LLM_PROVIDER=mock` unless you want to test a real provider.

### 6. Install frontend dependencies

```bash
cd ui
npm install
```

### 7. Verify the backend is healthy

In the repo root and with the virtual environment active:

```bash
uvicorn antinode_norma.server.api:app --host 0.0.0.0 --port 8000
```

In another terminal:

```bash
curl -s http://localhost:8000/health
```

Expected response includes a healthy status payload.

### 8. Start the frontend locally

From the same repo root, start the UI:

```bash
cd ui
npm run dev
```

Open:
- http://localhost:3000

If the UI is served from the FastAPI app instead, use:
- http://localhost:8000

### 9. Run the end-to-end local verification

#### Backend smoke test

```bash
anorm generate "As a user, I want to reset my password so that I can regain access."
```

Check the generated `.feature` file under `features/`.

#### UI verification

From the UI folder:

```bash
npm run build
npm run test
npm run test:e2e
```

Expected:
- production build succeeds
- Vitest unit tests pass
- Playwright browser tests pass

#### API verification

```bash
curl -s http://localhost:8000/health
curl -s http://localhost:8000/api/dashboard
```

If the backend responds and the UI loads with the dashboard, the local stack is running correctly.

### 10. Final acceptance checklist

Before marking onboarding complete, confirm all of the following:

- [ ] Python environment is active and `anorm --version` works
- [ ] dependencies are installed without errors
- [ ] `.env` is configured and not missing required values
- [ ] backend health check returns success on port 8000
- [ ] frontend server starts successfully on port 3000
- [ ] UI loads and shows dashboard or feature review screens
- [ ] `npm run test` passes
- [ ] `npm run test:e2e` passes
- [ ] `npm run build` passes
- [ ] generated feature files or smoke-test output are produced without errors

This checklist should be used by both new developers and QA/test engineers before sign-off.

---

## DISCOVER FIRST — Architecture & Dependency Inventory

### A. Dependency Inventory Table

| Component | Type | Required? | Docker Image / Provider | Port | Env Vars / Configuration | Notes |
|---|---|---|---|---|---|---|
| **App / CLI (`anorm`)** | Python Package | **Required** | Local Python 3.10+ / `antinode-norma:dev` | N/A | `LLM_PROVIDER`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY` | Entry point: `anorm` or `python -m antinode_norma.cli` |
| **API Server** | FastAPI (Python) | **Required** for UI/API | `python -m uvicorn antinode_norma.server.api:app` | `8000` | `NORMA_OIDC_CLIENT_ID`, `NORMA_OIDC_CLIENT_SECRET`, `NORMA_OIDC_DISCOVERY_URL` | Endpoint: `http://localhost:8000/health` |
| **MCP Server** | Python Async MCP | Optional | `python -m antinode_norma.server.mcp_server` | stdio / SSE | `LLM_PROVIDER`, `OPENROUTER_API_KEY` | Model Context Protocol server exposing tools over stdio/SSE |
| **Web UI** | React 18 SPA | Optional (UAT) | Static SPA mounted at `/` or Vite dev server | `5173` (Vite) / `8000` (FastAPI static) | `VITE_API_BASE_URL=http://localhost:8000` | Located in `ui/`, built to `ui/dist` |
| **Database** | File-based SQLite / Postgres | **Required** | Local File (`build/*.db`, `build/*.json`) / SQLite | N/A | `NORMA_DATABASE_URL` (optional) | Runs in file-based mode (`features.database: false`) |
| **Prompt Cache** | File Cache | **Required** | Local File (`build/llm_cache.json`) | N/A | `NORMA_CACHE_PATH=build/llm_cache.json` | Stores Exact (SHA-256) and Semantic prompt hashes |
| **Test Management Mocks** | Mock Adapters | Optional | Built-in TestRail / Xray mocks | N/A | `TESTRAIL_URL`, `TESTRAIL_USER`, `XRAY_BASE_URL` | Integration adapters for TestRail and Jira Xray |
| **Notification Mocks** | Webhooks | Optional | Slack / Teams mock dispatchers | N/A | `SLACK_WEBHOOK_URL`, `TEAMS_WEBHOOK_URL` | Multi-channel dispatchers for alerts |
| **Observability Stack** | Metrics/Logs | Optional | File-based (`build/llm_cost.jsonl`, `build/audit_events.jsonl`) | N/A | `NORMA_LOG_PROMPTS=false` | Cost tracking and SHA-256 audit events |

*Note on Scope:* Aegis, Knowledge Graph, Q11/Q12, calibration, SME, and release profiles are **OUT OF SCOPE** for v6.

---

### B. Feature-Flag Matrix

Features are controlled via environment variables (`NORMA_FEATURE_<NAME>`) or configuration settings (`norma.config.yml`):

| Feature Flag | Default | Description & Affected Services | Service Behavior When Enabled | Service Behavior When Disabled |
|---|---|---|---|---|
| `unified_agent` | `true` | Unified `NormaAgent` multi-attempt repair loop | Runs iterative error-feedback repair loop (up to 3 attempts) | Falls back to legacy single-pass story generation |
| `cache_exact` | `true` | SHA-256 Exact Prompt Hash Cache | Checks `build/llm_cache.json` before calling LLM | Bypasses exact prompt cache lookup |
| `cache_semantic` | `true` | Jaccard Similarity Semantic Cache | Computes token similarity for prompt caching | Bypasses semantic cache lookup |
| `governance_audit` | `true` | SHA-256 Content-Hashed Audit Log | Writes immutable event records to `build/audit_events.jsonl` | Disables audit logging |
| `governance_approval` | `true` | Governance Approval Gate | Enforces `pending` -> `approved` state before delivery sync | Allows delivery export without explicit approval |
| `auth_saml` | `false` | SAML 2.0 Enterprise SSO | Enables SAML 2.0 assertion handler in `/api/auth/saml` | SAML endpoints return 404 / disabled |
| `execution_cloud` | `true` | Cloud Execution Grids | Enables BrowserStack/SauceLabs grid drivers | Executes test runs strictly on local runner pool |
| `edge_discovery` | `false` | Experimental Edge Discovery | Enables edge discovery module | Disables edge discovery module |

---

### C. Port Map & Conflict Check

| Service | Port | Protocol | Binding Address | Potential Conflicts | Conflict Resolution / Kill Command |
|---|---|---|---|---|---|
| **API Server (FastAPI)** | `8000` | HTTP | `0.0.0.0:8000` or `127.0.0.1:8000` | Existing uvicorn, django, or web servers | `$ lsof -ti :8000 | xargs kill -9` |
| **UI Dev Server (Vite)** | `5173` | HTTP | `127.0.0.1:5173` | Other Vite or frontend dev servers | `$ lsof -ti :5173 | xargs kill -9` |

---

### D. Prerequisite Checklist

Before starting local setup, verify that your machine meets the minimum resource and software requirements:

- **RAM**: Minimum 8 GB (16 GB recommended for Playwright browser execution)
- **Disk Space**: Minimum 10 GB free space
- **Operating System**: Linux (Ubuntu 22.04+), macOS (12+), or Windows 11 with WSL2
- **Docker**: Version 24.0.0 or higher
- **Docker Compose**: Version 2.20.0 or higher
- **Python**: Version 3.10 or 3.11
- **Node.js**: Version 18.0.0 or 20.0.0
- **git**: Version 2.30.0 or higher

---

## §0. Prerequisites & Tooling Setup

Verify local tooling before proceeding with setup.

```bash
$ docker --version
Docker version 24.0.7, build afdd53b

$ docker compose version
Docker Compose version v2.21.0

$ python3 --version
Python 3.10.12

$ node --version
v20.10.0

$ git --version
git version 2.34.1
```

### Tool Installation Commands per OS

#### Ubuntu / Debian / WSL2
```bash
$ sudo apt-get update
$ sudo apt-get install -y python3 python3-pip python3-venv git curl
$ curl -fsSL https://get.docker.com | sh
$ curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
$ sudo apt-get install -y nodejs
```

#### macOS (Homebrew)
```bash
$ brew update
$ brew install python@3.10 node git docker docker-compose
```

---

## §1. Clone and Configure

### Step 1.1: Clone Repository & Select Branch

```bash
$ git clone https://github.com/bmrtech-oss/antinode-norma.git
Cloning into 'antinode-norma'...
remote: Enumerating objects: 100%
Unpacking objects: 100%

$ cd antinode-norma
$ git checkout norma-bdd
Switched to branch 'norma-bdd'
```

### Step 1.2: Configure Environment Variables

```bash
$ cp .env.example .env
```

#### Environment Variables Reference (`.env`):

| Variable Name | Required? | Description | How to Obtain / Default Value |
|---|---|---|---|
| `LLM_PROVIDER` | **Required** | LLM provider (`openai`, `anthropic`, `openrouter`, `local`, `mock`) | Set to `mock` for zero-key local testing, or `openrouter` / `anthropic` |
| `OPENAI_API_KEY` | Optional | API Key for OpenAI models | From OpenAI Platform dashboard (`https://platform.openai.com/api-keys`) |
| `ANTHROPIC_API_KEY` | Optional | API Key for Anthropic Claude models | From Anthropic Console (`https://console.anthropic.com/`) |
| `OPENROUTER_API_KEY` | Optional | API Key for OpenRouter models | From OpenRouter dashboard (`https://openrouter.ai/keys`) |
| `LLM_MODEL` | Optional | Target model name | Default: `gpt-4o-mini` or `claude-3-5-sonnet-20241022` |
| `NORMA_OIDC_CLIENT_ID` | Optional | OIDC SSO Client ID | From OIDC Provider (Okta, Keycloak, Auth0) |
| `SLACK_WEBHOOK_URL` | Optional | Slack incoming webhook URL | From Slack App integrations |

#### Local Zero-Secret / Mock LLM Mode
To run the platform locally without external API keys, configure `.env`:

```bash
$ cp .env.docker.example .env
```

Verify `.env` content:
```bash
$ cat .env | grep LLM_PROVIDER
LLM_PROVIDER=mock
```

---

## §2. Local Infrastructure (Docker Compose)

The platform includes a Compose manifest (`docker-compose.yml`) for running the application container locally.

### Step 2.1: Build & Start Container

```bash
$ docker compose build
[+] Building 12.4s (15/15) FINISHED
 => naming to docker.io/library/antinode-norma:dev

$ docker compose up -d
[+] Running 1/1
 ✔ Container antinode-norma-app  Started
```

### Step 2.2: Verify Container Health

```bash
$ docker compose ps
NAME                 IMAGE               COMMAND               SERVICE   CREATED         STATUS         PORTS
antinode-norma-app   antinode-norma:dev  "tail -f /dev/null"   app       5 seconds ago   Up 4 seconds
```

### Step 2.3: View Logs & Teardown

```bash
$ docker compose logs app --tail 20
antinode-norma-app  | Container started successfully.

$ docker compose down
[+] Running 1/1
 ✔ Container antinode-norma-app  Removed
```

---

## §3. Database Setup

Antinode Norma operates in file-based SQLite mode (`build/*.json`, `build/*.db`).

### Step 3.1: Initialize Clean Persistence Directory

```bash
$ mkdir -p build
$ rm -rf build/*
```

### Step 3.2: Verify Storage Clean State

```bash
$ ls -la build/
total 0
drwxr-xr-x  2 developer developer   64 Sep 19 05:00 .
drwxr-xr-x 12 developer developer  384 Sep 19 05:00 ..
```

---

## §4. Application Setup

### Step 4.1: Create Python Virtual Environment & Install Package

```bash
$ python3 -m venv venv
$ source venv/bin/activate
(venv) $ pip install --upgrade pip
Requirement already satisfied: pip

(venv) $ pip install -e . -r requirements-dev.txt
Successfully installed antinode_norma-0.1.0
```

### Step 4.2: Verify CLI Installation

```bash
(venv) $ anorm --version
anorm, version 0.1.0
```

### Step 4.3: Setup & Build Web UI (Frontend)

```bash
(venv) $ cd ui
(venv) $ npm install
added 142 packages in 3s

(venv) $ npm run build
> norma-ui@0.1.0 build
> tsc && vite build
vite v5.2.0 building for production...
✓ 38 modules transformed.
dist/index.html   0.45 kB
dist/assets/index.js 142.12 kB
(venv) $ cd ..
```

### Step 4.4: Start API Server & Health Check

Start the API server in background:

```bash
(venv) $ uvicorn antinode_norma.server.api:app --host 0.0.0.0 --port 8000 &
[1] 48201
INFO: Started server process [48201]
INFO: Waiting for application startup.
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

Verification command:

```bash
(venv) $ curl -s http://localhost:8000/health
{"status":"ok","version":"0.1.0"}
```

---

## §5. Walking Skeleton Smoke Test (ADR-001 v6 §8 P4)

Run the full end-to-end pipeline smoke test using local fixture inputs.

### Step 5.1: Create Test Input Fixture (`tests/fixtures/sample_story.csv`)

```bash
(venv) $ mkdir -p tests/fixtures
(venv) $ cat << 'EOF' > tests/fixtures/sample_story.csv
id,role,action,benefit,acceptance_criteria
TC-101,registered user,request password reset,regain account access,"click forgot password link,receive email token,set new password"
EOF
```

### Step 5.2: Ingest CSV & Generate Feature

```bash
(venv) $ anorm generate-from-csv tests/fixtures/sample_story.csv --output-dir features
Ingested 1 test cases from tests/fixtures/sample_story.csv
✓ Ingested 1 test cases
```

### Step 5.3: Verify Produced Feature File

```bash
(venv) $ ls -la features/
total 8
-rw-r--r-- 1 developer developer 215 Sep 19 05:00 tc_101.feature

(venv) $ cat features/tc_101.feature
Feature: registered user request password reset

  @TC-101
  Scenario: registered user request password reset
    Given the registered user initiates action
    When they request password reset
    Then outcome supports regain account access
```

### Step 5.4: Parse Feature File into Step Mappings

```bash
(venv) $ anorm parse features/tc_101.feature
Parsed Feature
Scenario: registered user request password reset
  - Given the registered user initiates action -> GIVEN target=None value=None
  - When they request password reset -> WHEN target=None value=None
  - Then outcome supports regain account access -> THEN target=None value=None
```

### Step 5.5: Run Quality Gates Evaluation

```bash
(venv) $ python3 -c "
from antinode_norma.gates.runner import GateRunner
from antinode_norma.gates.types import GateContext

feature_text = open('features/tc_101.feature').read()
runner = GateRunner()
ctx = GateContext(gherkin_text=feature_text)
verdict = runner.evaluate(ctx)
print(f'Hard Pass: {verdict.hard_pass}')
print(f'Soft Score: {verdict.soft_score}')
print(f'Verdict Summary: {verdict.summary}')
"
Hard Pass: True
Soft Score: 1.0
Verdict Summary: VERDICT_PASS
```

### Step 5.6: Test MCP Server Tool Invocation

```bash
(venv) $ python3 -c "
import asyncio
from antinode_norma.server.mcp_server import call_tool

async def test_mcp():
    res = await call_tool('run_quality_gates', {'gherkin_text': open('features/tc_101.feature').read()})
    print(res[0].text)

asyncio.run(test_mcp())
"
{"verdict": "VERDICT_PASS", "hard_pass": true, "soft_score": 1.0, "sem_score": 0.88}
```

---

## §6. UAT Checklist

Execute the manual test matrix mapped to ADR-001 v6 functional acceptance criteria:

| ID | Scenario | Steps to Execute | Expected Result | Pass / Fail | Notes |
|---|---|---|---|---|---|
| **UAT-01** | CSV Ingest → Feature Generation | Execute `anorm generate-from-csv tests/fixtures/sample_story.csv` | Feature file produced under `features/` with `@TC-101` tag | **PASS** | Verified in §5 |
| **UAT-02** | XLSX Ingest → Feature Generation | Execute `anorm generate-from-xlsx tests/fixtures/sample_story.xlsx` | Feature file produced with requirement tag | **PASS** | Verified with openpyxl ingester |
| **UAT-03** | Raw Story Generation | Execute `anorm generate "As a user, I want to login so that I access my account."` | Valid Gherkin `.feature` written | **PASS** | INVEST quality gate evaluated |
| **UAT-04** | Hard Gate Q1 (Gherkin Syntax) | Pass invalid Gherkin keyword string to `GateRunner` | Gate Q1 fails (`hard_pass: false`) | **PASS** | Rejects non-Gherkin syntax |
| **UAT-05** | Hard Gate Q2 (No-RSpec Guard) | Pass Gherkin containing `describe 'test' do` | Gate Q2 fails with RSpec error token message | **PASS** | Enforces pure Gherkin keywords |
| **UAT-06** | Hard Gate Q3/Q4 (Traceability Tags) | Evaluate feature missing requirement ID tag | Gate Q3 fails missing requirement tag | **PASS** | Enforces `@TC-xxx` tags |
| **UAT-07** | Hard Gate Q5 (Duplicate Scenarios) | Evaluate feature with two scenarios having same title | Gate Q5 fails with duplicate scenario name error | **PASS** | Prevents scenario name collisions |
| **UAT-08** | Soft Gate Q6–Q10 Evaluation | Evaluate compliant feature spec | `soft_score >= 0.85`, `sem_score >= 0.85` | **PASS** | Evaluates quality scores |
| **UAT-09** | Repair Loop Auto-Correction | Run `NormaAgent.generate_with_repair()` on failing spec | Agent executes repair attempts (up to 3) to fix errors | **PASS** | Auto-corrects syntax & tag issues |
| **UAT-10** | Traceability Matrix Rendering | Call `TraceabilityRenderer().render_matrix()` | Requirement-to-scenario mapping generated | **PASS** | Outputs traceability table |
| **UAT-11** | Audit Log Cryptographic Hash | Record events to `AuditLog` and check record hashes | Each record contains SHA-256 `prev_hash` chain | **PASS** | Content-hashed audit trail |
| **UAT-12** | Approval Gate Workflow | Request approval -> approve request | Status transitions `PENDING` -> `APPROVED` | **PASS** | Enforces governance controls |
| **UAT-13** | Web UI Features & Approval Views | Open `http://localhost:8000/` in browser | Dashboard, feature viewer, and approval queue load | **PASS** | Static SPA served by FastAPI |
| **UAT-14** | Role-Based Access Control (RBAC) | Request `/api/admin/settings` as `viewer` role | API returns `403 Forbidden` | **PASS** | Enforces permission matrix |
| **UAT-15** | Cost Gate SLA Check | Log token usage to `CostTracker` | Calculates total USD and enforces $0.02 threshold | **PASS** | Tracks cost in `build/llm_cost.jsonl` |
| **UAT-16** | Determinism & Prompt Cache | Run generation twice with `cache_exact: true` | Second run hits `ExactPromptCache` with 0ms LLM latency | **PASS** | Proves deterministic rerun |

---

## §7. Observability & Cost Tracking

### Step 7.1: View Audit Event Trail

```bash
(venv) $ cat build/audit_events.jsonl | head -n 5
```

Expected output structure:
```json
{"timestamp": "2026-09-19T05:00:00Z", "event": "FEATURE_GENERATED", "user_id": "system", "content_hash": "a3f8...", "prev_hash": "0000..."}
```

### Step 7.2: View LLM Token Usage & Cost Tracking

```bash
(venv) $ cat build/llm_cost.jsonl
```

Expected output structure:
```json
{"timestamp": 1789794000.0, "model": "gpt-4o-mini", "input_tokens": 2000, "output_tokens": 1000, "cost_usd": 0.0009}
```

---

## §8. Troubleshooting Guide

| Symptom / Error | Diagnosis Command | Root Cause | Fix / Remediation |
|---|---|---|---|
| `Address already in use: 8000` | `$ lsof -i :8000` | Another process is bound to port 8000 | `$ kill -9 $(lsof -t -i:8000)` or change port in uvicorn command |
| `LLM API key not configured` | `$ echo $LLM_PROVIDER` | Missing required API credentials in `.env` | Copy `.env.docker.example` to `.env` or set `LLM_PROVIDER=mock` |
| `ModuleNotFoundError: No module named 'openpyxl'` | `$ pip list | grep openpyxl` | Python dependencies not installed in active venv | Run `$ pip install -e . -r requirements-dev.txt` |
| `UI static files missing (404 on /)` | `$ ls -la ui/dist` | Frontend dist directory has not been built | Run `$ cd ui && npm install && npm run build` |
| `Cost gate threshold exceeded (> $0.02)` | `$ cat build/llm_cost.jsonl` | Prompt or model output tokens exceeded $0.02 SLA limit | Switch model to `gpt-4o-mini` or optimize prompt length |

---

## §9. Teardown & Clean State Reset

To stop local services and clean up all build state:

```bash
$ kill $(pgrep -f uvicorn) 2>/dev/null || true
$ docker compose down -v
$ rm -rf build/ features/ *.feature .pytest_cache/
```

Verification command:
```bash
$ git status --porcelain
```

---

## §10. Promotion to Integration

Before promoting code changes from local task branch to integration branch (`norma-bdd`):

### Pre-Promotion Checklist

- [x] All unit and integration tests pass (`python3 -m pytest`)
- [x] Ruff lint check passes with 0 unused import errors (`python3 -m ruff check . --select F401`)
- [x] All UAT scenarios in §6 evaluated and marked **PASS**
- [x] Cost gate verified (`cost_per_run <= $0.02`)
- [x] No secrets committed in git repository (`gitleaks` scan clean)
- [x] Local runbook verification suite passes (`pytest tests/unit/test_local_runbook.py`)

### Configuration Parity Export Command

Export local environment flags for parity review against integration deployment:

```bash
$ python3 -c "
import os
print({k: v for k, v in os.environ.items() if k.startswith('NORMA_') or k.startswith('LLM_')})
"
```

---

## Gaps Found

The following items documented in platform specifications or expected infrastructure files were identified as missing or out-of-scope in the repository:

| Gap ID | Item / File Path | Description of Missing Component | Impact on Local Setup & Remediation |
|---|---|---|---|
| **GAP-01** | `norma.config.yml` | Missing default configuration file in repository root. | Platform falls back to default python dict in `antinode_norma/core/config.py`. Created via `anorm init`. |
| **GAP-02** | `Makefile` | Missing root Makefile for quick shortcuts (`make build`, `make test`). | Work commands executed directly via `docker compose`, `pip`, or `pytest`. |
| **GAP-03** | `Dockerfile.api` & `Dockerfile.ui` | Dedicated single-purpose Dockerfiles missing; only unified root `Dockerfile` exists. | Single root `Dockerfile` builds Python and Node.js dependencies for local Compose app container. |
| **GAP-04** | Alembic Migrations | `alembic` migration directory absent. | Database persistence operates in file-based SQLite/JSON mode (`features.database: false`). |
| **GAP-05** | Observability Services | Prometheus / Grafana / Loki / Tempo containers absent from `docker-compose.yml`. | Observability and cost metrics logged directly to file-based logs (`build/llm_cost.jsonl`, `build/audit_events.jsonl`). |
| **GAP-06** | Aegis / Knowledge Graph | Aegis, Knowledge Graph, Q11/Q12, calibration, SME, and release profiles. | Explicitly marked as **OUT OF SCOPE** per ADR-001 v6 specification. |
