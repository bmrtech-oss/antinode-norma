# Local System Startup and Manual UI Testing

This guide starts the complete local Antinode Norma system and provides a
repeatable manual test path for the CSV/XLSX generation workflow.

The recommended setup uses the local mock provider. It requires no external
LLM credentials and keeps manual testing deterministic.

## 1. Prerequisites

Use:

- Windows 10/11
- Python 3.10 or newer
- Node.js 18 or newer
- npm
- Git

From PowerShell, verify:

```powershell
python --version
node --version
npm --version
git --version
```

Run all commands below from the repository root:

```text
D:\work-root\codebase\bmrtech-oss\antinode-norma
```

## 2. Install dependencies

Create or activate the backend virtual environment:

```powershell
Set-Location D:\work-root\codebase\bmrtech-oss\antinode-norma
if (-not (Test-Path .venv\Scripts\python.exe)) {
  python -m venv .venv
}
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install -r requirements-dev.txt
```

If PowerShell blocks activation, run the project commands with the explicit
executable instead:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
```

Install the UI dependencies:

```powershell
Set-Location D:\work-root\codebase\bmrtech-oss\antinode-norma\ui
npm install
npx playwright install chromium
```

## 3. Exact local environment configuration

Create `.env` in the repository root with the following values:

```dotenv
# Deterministic local provider; no external API key is required.
LLM_PROVIDER=mock
LLM_MODEL=mock

# Generation worker uses local rendering and does not call an external provider.
NORMA_GENERATION_PROVIDER=

# Local durable state and generated files.
NORMA_IMPORT_DB=.runtime/import_jobs.sqlite3
NORMA_IMPORT_DIR=.runtime/imports
NORMA_ARTIFACT_DIR=.runtime/artifacts

# Local worker capacity.
NORMA_GENERATION_WORKERS=2
NORMA_GENERATION_QUEUE_SIZE=20

# Local request limits.
NORMA_UPLOAD_RATE_LIMIT=20
NORMA_GENERATION_RATE_LIMIT=20
NORMA_RATE_LIMIT_WINDOW_SECONDS=60

# Recovery and retention are safe to enable locally.
NORMA_GENERATION_ABANDON_TIMEOUT_SECONDS=300
NORMA_RETENTION_CLEANUP_ENABLED=false
NORMA_ARTIFACT_RETENTION_DAYS=30
NORMA_IMPORT_RETENTION_DAYS=30

# Provider resilience defaults; retained for compatibility testing.
NORMA_GENERATION_PROVIDER_TIMEOUT_SECONDS=30
NORMA_GENERATION_PROVIDER_MAX_RETRIES=2
NORMA_GENERATION_PROVIDER_RETRY_BASE_SECONDS=0.5
NORMA_GENERATION_PROVIDER_RETRY_MAX_SECONDS=8
NORMA_GENERATION_CIRCUIT_FAILURE_THRESHOLD=3
NORMA_GENERATION_CIRCUIT_RESET_SECONDS=30
```

Do not put real API keys in this file for the mock workflow. `.env` is local
configuration and must not be committed.

The frontend uses the Vite proxy by default:

- UI: `http://localhost:3000`
- Backend: `http://localhost:8000`
- UI `/api` and `/health` requests proxy to the backend.

If the UI is pointed at a different backend, set the Vite variable before
starting it:

```powershell
$env:VITE_API_BASE_URL = "http://localhost:8000"
```

The UI also supports changing the API URL from **Settings**. The selected URL
is stored in browser local storage under `norma-ui-api-base-url`.

## 4. Start the backend

Use a dedicated PowerShell terminal:

```powershell
Set-Location D:\work-root\codebase\bmrtech-oss\antinode-norma
.\.venv\Scripts\python.exe -m uvicorn antinode_norma.server.api:app --host 0.0.0.0 --port 8000
```

Verify the backend before opening the UI:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

The response should contain a healthy status and API version.

For a background process with logs and a PID file, use:

```powershell
.\scripts\start-backend.ps1
```

Logs are written to `.runtime\backend.log` and
`.runtime\backend.error.log`. Stop the managed process with:

```powershell
.\scripts\stop-backend.ps1
```

## 5. Start the frontend

Use a second PowerShell terminal:

```powershell
Set-Location D:\work-root\codebase\bmrtech-oss\antinode-norma\ui
npm run dev -- --host 0.0.0.0
```

Open:

```text
http://localhost:3000
```

Alternatively, from the repository root:

```powershell
.\scripts\start-frontend.ps1
```

Managed frontend logs are written to `.runtime\frontend.log` and
`.runtime\frontend.error.log`. Stop it with:

```powershell
.\scripts\stop-frontend.ps1
```

## 6. Manual UI functional test

Use the supplied fixture:

```text
test data\sample_stories.csv
```

In the browser:

1. Open **Generation**.
2. Upload `test data\sample_stories.csv`.
3. Confirm the import succeeds and a bounded source preview is displayed.
4. Confirm the detected columns and mapping are visible.
5. Run validation.
6. Confirm validation reports the expected row count and no blocking errors.
7. Start generation.
8. Confirm the job moves through queued/running and exposes progress.
9. Reload the browser while the job is active or completed.
10. Confirm the active job/history entry is restored.
11. Open the result preview and verify generated Gherkin content.
12. Download the individual `.feature` artifact.
13. Download the bulk ZIP artifact.
14. Submit the successful result for approval.
15. Open **Feature Review** and confirm the generated result has source
    traceability and approval metadata.
16. Approve or reject the result from the review surface.

The expected happy path is:

```text
uploaded -> validated -> queued/running -> completed -> submitted -> approved
```

## 7. Manual failure-path checks

Run these checks after the happy path:

| Check | Manual action | Expected result |
|---|---|---|
| Unsupported file | Upload a `.txt` file | Clear unsupported-format error; no job is created |
| Malformed CSV | Upload an invalid-encoding or malformed CSV | Import is rejected with a clear validation error |
| Oversized file | Upload a file over the configured limit | Request is rejected with an upload-size error |
| Invalid mapping | Map a required field to a missing column | Mapping is rejected and Generate remains blocked |
| Row validation failure | Use a fixture containing an invalid row | Row-level error is visible; valid rows are not hidden |
| Cancellation | Cancel a running job | Job reaches cancelled state and progress stops |
| Retry | Retry an eligible failed/cancelled job | Retry is admitted and progress/history updates |
| Refresh recovery | Reload during an active job | The same job is restored from history or active-job storage |
| API outage | Stop the backend while viewing the UI | API status shows disconnected/retry state; UI does not silently report success |
| Authorization | Use a different `X-User-ID` against an existing resource | Resource is not exposed across owners/tenants |

For backend-only authorization checks, send headers explicitly:

```powershell
$headers = @{
  "X-User-ID" = "manual-user"
  "X-Tenant-ID" = "default"
}
Invoke-RestMethod -Headers $headers http://localhost:8000/v1/generation-jobs
```

## 8. Run automated tests locally

Backend:

```powershell
Set-Location D:\work-root\codebase\bmrtech-oss\antinode-norma
.\.venv\Scripts\python.exe -m pytest tests\unit tests\integration --tb=no -q
```

Frontend unit and static checks:

```powershell
Set-Location D:\work-root\codebase\bmrtech-oss\antinode-norma\ui
npm run lint
npm run typecheck
npm run test -- --run
npm run build
```

Frontend browser tests:

```powershell
npx playwright test --config playwright.config.ts
npx playwright test e2e/accessibility.spec.ts --config playwright.config.ts
```

The Playwright tests use deterministic API fixtures. They validate the UI
contract and behavior without requiring a live LLM provider.

## 9. Troubleshooting

### Port 8000 is already in use

Find the process:

```powershell
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue |
  Select-Object LocalAddress, LocalPort, OwningProcess
```

Stop only the identified process if it belongs to this project:

```powershell
Stop-Process -Id <PID>
```

### Port 3000 is already in use

Start Vite on another port and update the browser URL:

```powershell
npm run dev -- --host 0.0.0.0 --port 3001
```

The backend remains on port 8000.

### UI shows API disconnected

1. Confirm `Invoke-RestMethod http://localhost:8000/health` succeeds.
2. Open **Settings** in the UI.
3. Set API URL to `http://localhost:8000`.
4. Save and retry the API status check.
5. If using a prior configuration, clear the `norma-ui-api-base-url` local
   storage entry and reload.

### Backend fails during startup

Check:

```powershell
Get-Content .runtime\backend.error.log -Tail 80
```

Confirm the virtual environment is installed and the configured runtime paths
are writable:

```powershell
Test-Path .venv\Scripts\python.exe
New-Item -ItemType Directory -Force .runtime\imports,.runtime\artifacts
```

### Reset local test state

Stop both managed processes first, then remove only the local runtime data:

```powershell
.\scripts\stop-frontend.ps1
.\scripts\stop-backend.ps1
Remove-Item -Recurse -Force .runtime
```

The next backend start recreates the database and artifact directories.
