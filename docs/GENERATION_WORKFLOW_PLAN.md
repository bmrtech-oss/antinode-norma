# CSV/XLSX Import and Feature Generation Plan

## 1. Purpose

Define the end-to-end product and technical plan for allowing users to:

1. Upload CSV or XLSX test-case files.
2. Preview and map the imported data.
3. Validate rows before generation.
4. Start feature generation.
5. Monitor progress.
6. Review successful and failed results.
7. Download generated Gherkin feature files.
8. Submit generated features for quality review and approval.

The workflow must support large files, long-running LLM operations, partial success, retry, cancellation, browser refreshes, backend restarts, auditability, and future worker scaling.

## 2. Current State

### Existing capabilities

- CSV ingestion exists in `antinode_norma/ingest_structured/csv.py`.
- XLSX ingestion exists in `antinode_norma/ingest_structured/xlsx.py`.
- CLI commands exist:
  - `anorm generate-from-csv`
  - `anorm generate-from-xlsx`
- The React UI can browse generated feature data and governance views.
- The API supports versioned routes under `/v1/`.
- The first import API slice is implemented:
  - `POST /v1/imports`
  - `GET /v1/imports/{import_id}`
  - `GET /v1/imports/{import_id}/preview`
  - `POST /v1/imports/{import_id}/validate`
  - `POST /v1/generation-jobs`
  - `GET /v1/generation-jobs/{job_id}`
- Initial import and job records are persisted in SQLite under `.runtime/`.
- The UI has a Generation area with file selection, upload, validation, and initial job status.

### Current limitations

- The local worker is implemented, but production worker recovery and provider-backed
  quality gates remain Phase 4 work.
- The UI now supports import preview, worksheet selection, mapping, validation issues,
  progress polling, cancellation, retry, job history, and artifact downloads.
- Feature Review integration now includes submitted generated results, approval
  state, generation job/result traceability, and direct approve/reject actions.
- Authorization, rate limits, retention, metrics, and complete audit coverage remain
  Phase 4 work. SSE updates are implemented with polling fallback.
- The current CLI contains fallback behavior that writes synthetic feature content
  after generation errors; the UI workflow must expose failures explicitly instead.

## 3. Product Workflow

## 3.1 New Import

The user opens **Generation → New import** and:

1. Selects or drops a `.csv` or `.xlsx` file.
2. Sees file name, format, size, and upload limits.
3. Uploads the file.
4. Selects an XLSX worksheet when more than one worksheet is available.
5. Reviews a sample preview.
6. Maps source columns to canonical fields.
7. Confirms the import.

Canonical fields:

- ID
- Title
- Role
- Action
- Benefit
- Acceptance criteria
- Tags

The mapping interface must support source files with different header names and must show unmapped columns as optional metadata.

## 3.2 Validation

Before generation, show a validation summary:

```text
Rows detected: 125
Valid rows: 117
Rows with warnings: 6
Rows rejected: 2
```

Show row-level issues:

- Source row number.
- Field.
- Severity.
- Message.
- Suggested correction.

The user can:

- Continue with valid rows.
- Download a validation report.
- Return to column mapping.
- Replace the source file.
- Cancel the import.

No invalid row should be silently converted into synthetic content.

## 3.3 Generation

After validation, the user selects **Start generation**.

The system creates a durable generation job and immediately returns its ID. The browser navigates to the job-progress view.

The progress view shows:

- Overall percentage.
- Processed rows versus total rows.
- Successful rows.
- Warning rows.
- Failed rows.
- Current row/test-case.
- Elapsed time.
- Estimated completion when available.
- Backend connection state.
- Cancel action.

## 3.4 Results

After completion, show:

```text
Generation completed with warnings

125 rows processed
117 features generated
6 generated with warnings
2 rows failed
Quality gate pass rate: 91.5%
```

Each result includes:

- Test-case ID.
- Source row number.
- Generated feature name.
- Generation status.
- Quality-gate status.
- Warning and error count.
- Preview action.
- Download action.
- Retry action when applicable.

Bulk actions:

- Download all successful artifacts.
- Download a validation/generation report.
- Submit selected features for approval.
- Retry failed rows.
- Open selected results in Feature Review.

## 3.5 Job History

Add **Generation → Job history** with:

- Search.
- Status filter.
- Source file filter.
- Submitted-by filter.
- Date range.
- Row counts.
- Duration.
- Result counts.
- Open job action.

Users must be able to refresh the browser and return to an active or completed job.

## 4. Target API Contract

All new endpoints should be versioned under `/v1/`.

### Imports

```text
POST /v1/imports
GET  /v1/imports
GET  /v1/imports/{import_id}
GET  /v1/imports/{import_id}/preview
POST /v1/imports/{import_id}/mapping
POST /v1/imports/{import_id}/validate
GET  /v1/imports/{import_id}/validation
DELETE /v1/imports/{import_id}
```

`POST /v1/imports` accepts multipart form data with a `file` field.

Import response:

```json
{
  "id": "import_123",
  "filename": "requirements.xlsx",
  "format": "xlsx",
  "size_bytes": 182340,
  "sha256": "...",
  "status": "uploaded",
  "worksheet_names": ["Requirements", "Notes"],
  "row_count": 125,
  "created_at": "2026-09-22T10:00:00Z"
}
```

Preview response:

```json
{
  "id": "import_123",
  "columns": ["Case ID", "Summary", "Action"],
  "rows": [
    {
      "source_row": 2,
      "values": {
        "Case ID": "TC-001",
        "Summary": "Login",
        "Action": "log in"
      }
    }
  ],
  "truncated": true
}
```

Mapping request:

```json
{
  "worksheet": "Requirements",
  "columns": {
    "id": "Case ID",
    "title": "Summary",
    "action": "Action",
    "benefit": "Expected outcome",
    "acceptance_criteria": "Acceptance Criteria",
    "tags": "Tags"
  }
}
```

### Generation jobs

```text
POST /v1/generation-jobs
GET  /v1/generation-jobs
GET  /v1/generation-jobs/{job_id}
POST /v1/generation-jobs/{job_id}/cancel
POST /v1/generation-jobs/{job_id}/retry
GET  /v1/generation-jobs/{job_id}/results
GET  /v1/generation-jobs/{job_id}/results/{result_id}
GET  /v1/generation-jobs/{job_id}/download
GET  /v1/generation-jobs/{job_id}/events
```

Create-job request:

```json
{
  "import_id": "import_123",
  "options": {
    "output_format": "gherkin",
    "run_quality_gates": true,
    "strict_validation": false
  },
  "idempotency_key": "..."
}
```

Job response:

```json
{
  "id": "job_123",
  "import_id": "import_123",
  "status": "running",
  "total_rows": 125,
  "processed_rows": 64,
  "successful_rows": 59,
  "warning_rows": 4,
  "failed_rows": 1,
  "progress_percent": 51.2,
  "current_item": "TC-064",
  "started_at": "2026-09-22T10:01:00Z",
  "completed_at": null,
  "estimated_completion_at": null,
  "error": null
}
```

## 5. State Model

### Import states

```text
uploaded
scanning
preview_ready
mapped
validated
invalid
deleted
```

### Generation job states

```text
queued
running
paused
cancelling
completed
completed_with_errors
failed
cancelled
```

State transitions must be validated server-side. Terminal states cannot transition back to running without an explicit retry operation.

## 6. Persistence Model

### Import

Required fields:

- ID.
- Original filename.
- Detected format.
- Storage key/path.
- File size.
- SHA-256.
- Worksheet metadata.
- Mapping configuration.
- Status.
- Row count.
- Creator.
- Created and updated timestamps.
- Retention/deletion timestamp.

### Import row

Required fields:

- Import ID.
- Source row number.
- Normalized test-case ID.
- Normalized fields.
- Original values.
- Validation status.
- Validation messages.

### Generation job

Required fields:

- Job ID.
- Import ID.
- Creator.
- Status.
- Options.
- Total rows.
- Processed rows.
- Successful rows.
- Warning rows.
- Failed rows.
- Current row.
- Start and completion timestamps.
- Cancellation timestamp.
- Error details.
- Idempotency key.

### Generation result

Required fields:

- Result ID.
- Job ID.
- Import row ID.
- Status.
- Artifact ID/path.
- Generated content hash.
- Quality-gate result.
- Warning messages.
- Error messages.
- Created timestamp.

SQLite is acceptable for local single-process development. Production deployments should use PostgreSQL for job metadata and object storage for uploaded files and generated artifacts.

## 7. Worker Architecture

### Local implementation

The first local implementation may use:

- SQLite.
- A configured local upload directory.
- A configured local artifact directory.
- An in-process background worker using `asyncio`, a thread pool, or a process pool.

The worker must:

1. Claim a queued job.
2. Process rows independently.
3. Persist progress after each row.
4. Persist result status and artifact metadata.
5. Continue after row-level failures when policy allows.
6. Check for cancellation between rows and LLM calls.
7. Mark the final job state explicitly.

### Production implementation

Use:

- PostgreSQL.
- Object storage.
- Redis plus Celery, RQ, Dramatiq, or an equivalent worker system.
- Separate worker processes from FastAPI.
- A job lease or heartbeat to recover abandoned jobs.

Do not rely on module-level dictionaries for durable generation state.

## 8. Progress Transport

### Initial version

Use polling:

```text
GET /v1/generation-jobs/{job_id}
```

Poll every 1–2 seconds while a job is active. Apply backoff after connection failures and stop polling in terminal states.

### Implemented (GEN-4-T01)

`GET /v1/generation-jobs/{job_id}/events` emits durable `generation.progress`,
`generation.completed`, `generation.failed`, and `generation.cancelled` events. Each
event has a monotonically increasing SQLite event ID and contains the same job
progress shape as the polling endpoint. Clients may reconnect with the
`Last-Event-ID` header (or `lastEventId` query parameter) to replay missed events.
The stream sends a terminal event and closes; disconnects are detected through the
request lifecycle. The Generation UI prefers SSE and transparently falls back to
the existing 1.5-second polling loop when the stream is unavailable.

### Future transport enhancements

```text
GET /v1/generation-jobs/{job_id}/events
```

The endpoint is now implemented; future work can add shared event storage for
multi-process deployments and stronger stream authorization for external identity
providers.

The UI must display connection state and retain the last known progress if the event stream disconnects.

## 9. Security and Reliability

Uploads must:

- Allow only `.csv` and `.xlsx`.
- Validate extension, MIME type, and file signature.
- Reject macro-enabled formats unless explicitly supported.
- Enforce maximum file size.
- Enforce maximum row count.
- Enforce worksheet and cell limits.
- Store files outside the static web directory.
- Generate server-side storage names.
- Never trust uploaded paths.
- Require authentication and authorization.
- Apply per-user upload and generation limits.
- Add idempotency protection for duplicate Generate clicks.
- Record upload, validation, generation, cancellation, completion, failure, retry, and download audit events.
- Avoid exposing provider credentials or internal stack traces.

Generated CSV reports must protect against spreadsheet formula injection by escaping cells that begin with `=`, `+`, `-`, or `@`.

## 10. Error Handling

Errors must be explicit and typed:

- Unsupported file type: `415`.
- File too large: `413`.
- Malformed workbook or CSV: `422`.
- Missing import/job: `404`.
- Invalid state transition: `409`.
- Permission failure: `403`.
- Provider or worker failure: typed job/result error with retry guidance.

The UI must distinguish:

- Upload failure.
- Parse failure.
- Validation failure.
- Generation failure.
- Partial row failure.
- Backend connection failure.
- Cancellation.

Do not return successful-looking fallback artifacts when generation fails.

## 11. UI Components

Recommended components:

- `GenerationWorkspace`
- `FileDropzone`
- `ImportPreview`
- `WorksheetSelector`
- `ColumnMapper`
- `ValidationSummary`
- `ValidationIssueTable`
- `GenerationProgress`
- `GenerationJobHistory`
- `GenerationResults`
- `ArtifactDownloadButton`
- `JobStatusBadge`

Shared UI requirements:

- Use existing semantic theme tokens.
- Use the existing tooltip and info-icon pattern for technical labels.
- Provide keyboard-accessible file selection.
- Announce upload, validation, and job-state changes with `aria-live`.
- Preserve active jobs across navigation.
- Warn before leaving an active job only when unsaved configuration exists.
- Support responsive layouts for mobile and desktop.

## 12. Integration With Existing Views

### Feature Review

Update the feature API contract and UI model so generated results consistently expose:

- Stable feature ID.
- Filename.
- Title.
- Source job/result ID.
- Status.
- Created/modified timestamp.
- Quality-gate summary.

### Approval Queue

Allow users to submit selected successful generated results for approval. Preserve the generation job and source row references in the approval record.

The generation-specific submission contract is:

```text
POST /v1/generation-jobs/{job_id}/results/{result_id}/submit-approval
```

Only a completed result with generated content may be submitted. The response is
the existing approval request shape plus `source_job_id` and `source_result_id`
for traceability. Duplicate submissions are not silently merged; the approval
queue remains the source of truth for the resulting request IDs and statuses.

### Traceability

Store the source requirement/test-case ID and generation result ID so each generated scenario can be traced back to its input row.

### Audit Trail

Record:

- Import created.
- Import validated.
- Generation started.
- Generation cancelled.
- Generation completed.
- Generation completed with errors.
- Generation failed.
- Artifact downloaded.
- Result submitted for approval.

## 13. Implementation Phases

The delivery model follows the structure used by the repository ADRs. Each phase has a
bounded goal, implementation tasks, observable deliverables, and an exit gate. A phase
may be developed incrementally, but its exit gate must pass before the next phase is
treated as complete.

### Phase 1 — Contracts and persistence

**Goal:** Establish a durable, versioned import and generation data model before adding
long-running execution or complex UI behavior.

**Scope and tasks**

| Task | Implementation | Deliverable | Evidence | Progress |
|---|---|---|---|---|
| GEN-1-T01 | Define import, source-row, mapping, validation, job, result, and artifact contracts | Typed request/response schemas under `/v1/` | Schema review and API contract tests | Complete |
| GEN-1-T02 | Add CSV/XLSX upload handling with extension, size, and parse validation | `POST /v1/imports` and import detail endpoint | Valid, invalid, oversized, and malformed upload tests | Complete |
| GEN-1-T03 | Persist original upload metadata, normalized rows, source columns, worksheets, and mappings | SQLite persistence with configurable runtime paths | Restart/read-back test | Complete |
| GEN-1-T04 | Add bounded preview and worksheet metadata | Import preview response with source row numbers | Preview contract test | Complete |
| GEN-1-T05 | Add canonical-to-source column mapping | Mapping endpoint with unknown-field rejection | Mapping acceptance and failure tests | Complete |
| GEN-1-T06 | Add row-level validation and validation retrieval | Validation summary and issue records | Required-field, duplicate-ID, and malformed-row tests | Complete |

**Dependencies:** Existing CSV/XLSX ingesters, FastAPI routing, and the configured
runtime storage directory.

**Exit criteria**

- An uploaded file can be reopened after a process restart.
- Preview exposes source values without losing source row numbers.
- Worksheet and column mapping choices are persisted.
- Validation returns explicit row-level errors and warnings.
- No invalid row is converted into synthetic content.
- Focused backend tests pass under the supported project environment.

**Status:** Implemented in the initial import vertical slice; additional validation
rules remain part of Phase 5.

### Phase 2 — Worker, progress, and artifacts

**Goal:** Execute validated imports asynchronously with durable progress, cancellation,
retry, and artifact results.

**Scope and tasks**

| Task | Implementation | Deliverable | Evidence | Progress |
|---|---|---|---|---|
| GEN-2-T01 | Reuse the existing story-to-case conversion path and isolate rendering from request handling | Worker-safe generation function | Unit test with deterministic output | Complete |
| GEN-2-T02 | Add queued, running, completed, completed-with-errors, failed, cancelling, and cancelled states | Durable job state transitions | State-transition tests | Complete |
| GEN-2-T03 | Add a bounded local worker executor | Background generation without blocking the API request | Async creation and polling test | Complete |
| GEN-2-T04 | Persist row-level pending, completed, and failed results | Result records with source row and case identifiers | Progress and partial-success tests | Complete |
| GEN-2-T05 | Persist generated feature content and artifact metadata | Per-job artifact directory and ZIP download | Artifact existence and download test | Complete |
| GEN-2-T06 | Add cancellation and retry operations | `/cancel` and `/retry` endpoints with legal-state checks | Cancellation and retry tests | Complete |
| GEN-2-T07 | Sanitize artifact names and isolate artifact paths | Safe, deterministic artifact names | Path traversal regression test | Complete |
| GEN-2-T08 | Add quality-gate execution hooks without hiding generation failures | Result-level quality status contract | Provider/quality-gate failure test | Planned |

**Dependencies:** Phase 1 persistence and validation contracts.

**Exit criteria**

- Job creation returns immediately with a durable job ID.
- Progress survives API process restarts or browser refreshes.
- Cancellation and retry are idempotent within their supported states.
- Partial success is represented without hiding failed rows.
- Artifact paths cannot escape the configured artifact directory.
- Worker exceptions transition jobs to `failed` rather than leaving them running.

**Status:** Core local worker, progress, cancellation, retry, results, downloads, and
artifact-name hardening are implemented. Quality-gate integration and stronger worker
lifecycle recovery are implemented through startup abandoned-job recovery.

Worker recovery is enabled with `NORMA_GENERATION_ABANDON_TIMEOUT_SECONDS` (default
`3600`). On process startup, queued jobs older than the timeout and running or
cancelling jobs whose `started_at` is older than the timeout become terminal
`abandoned` jobs. They retain owner/tenant and row progress metadata and can be
retried through the existing owner-checked retry endpoint. A stale worker observes
the abandoned state before writing further progress, while process-local capacity
leases are naturally released on restart.

### Phase 3 — UI workflow

**Goal:** Provide a complete user workflow from source-file selection through reviewable
generation results without requiring CLI access.

**Scope and tasks**

| Task | Implementation | Deliverable | Evidence | Progress |
|---|---|---|---|---|
| GEN-3-T01 | Add Generation navigation and page shell | Discoverable Generation surface | Navigation and render test | Complete |
| GEN-3-T02 | Add file selection and upload feedback | CSV/XLSX upload control | Invalid-extension and upload-state tests | Complete |
| GEN-3-T03 | Add bounded preview and XLSX worksheet selection | Source-aware preview table | Preview and worksheet interaction test | Complete |
| GEN-3-T04 | Add canonical field mapping controls | Mapping selectors and save action | Mapping request/response test | Complete |
| GEN-3-T05 | Add validation summary and issue table | Row, field, severity/message presentation | Validation issue rendering test | Complete |
| GEN-3-T06 | Add active-job progress polling | Percentage, counts, current item, and connection errors | Polling and error-state test | Complete |
| GEN-3-T07 | Add cancellation, retry, results, and ZIP download actions | Job controls and result summary | End-to-end workflow test | Complete |
| GEN-3-T08 | Add generation job history and reopen behavior | Searchable/filterable history with active-job recovery | Browser-refresh and history tests | Complete |
| GEN-3-T09 | Add artifact preview and per-row actions | Feature content preview and individual download/retry | Result interaction test | Complete |
| GEN-3-T10 | Add approval submission for successful results | Selected-result submission to Feature Review/approval | Approval integration test | Complete |

**Dependencies:** Phase 1 contracts and Phase 2 job/result endpoints.

**Exit criteria**

- A user can complete upload, mapping, validation, generation, and result download
  from the UI.
- Active jobs remain discoverable after browser refresh.
- Validation failures identify the affected rows and fields.
- Partial generation success is visible and actionable.
- All loading, empty, error, retry, and success states are explicit and accessible.
- UI typecheck, lint, unit tests, and production build pass.

**Status:** Upload, preview, worksheet selection, mapping, validation issue display,
progress polling, cancellation, retry, results, and bulk download are implemented.
Artifact preview, per-row download/retry actions, the upload-to-download browser
workflow, approval submission, and Feature Review workflow integration are
implemented. Phase 3 is complete for the current local workflow; production
hardening remains.

### Phase 4 — Live updates and operational hardening

**Goal:** Move from a reliable local workflow to a production-safe service with secure
access, observable execution, and recoverable failures.

**Scope and tasks**

| Task | Implementation | Deliverable | Evidence | Progress |
|---|---|---|---|---|
| GEN-4-T01 | Add SSE progress events with polling fallback | Near-real-time job updates | Durable SSE contract and reconnect tests | Complete |
| GEN-4-T02 | Add authentication and authorization to imports, jobs, results, and artifacts | User/tenant ownership checks | Unauthorized and cross-user access tests | Complete |
| GEN-4-T03 | Add upload rate limits and worker concurrency limits | Abuse and resource controls | Load and limit tests | Complete |
| GEN-4-T04 | Add abandoned-job detection and recovery | Jobs cannot remain running indefinitely | Recovery test after worker interruption | Complete |
| GEN-4-T05 | Add artifact and import retention policies | Configurable cleanup process | Retention and protected-active-job tests | Complete |
| GEN-4-T06 | Add structured metrics and operational alerts | Queue depth, duration, failure, and provider metrics | Metrics assertions and alert runbook | Next |
| GEN-4-T07 | Add lifecycle audit events | Auditable upload, validation, generation, cancellation, retry, download, and approval events | Audit completeness test | Planned |
| GEN-4-T08 | Add provider timeout, retry, and circuit-breaker behavior | Explicit provider failure handling | Provider failure and retry tests | Planned |

**Dependencies:** Phase 2 durable state and Phase 3 user-visible lifecycle actions;
repository authentication, audit, and operational conventions.

**Exit criteria**

- Every job has an owner and an auditable lifecycle.
- A worker or browser interruption does not create an unrecoverable job.
- Resource limits prevent unbounded upload, queue, and artifact growth.
- Live updates degrade safely to polling.
- Operational dashboards can identify queue backlog and failure causes.

### Phase 5 — Full validation and release readiness

**Goal:** Demonstrate that the complete workflow is correct across happy paths,
failure paths, security boundaries, and supported browser/runtime environments.

**Scope and test matrix**

| Area | Required coverage | Release evidence |
|---|---|---|
| Import | CSV, XLSX, worksheet selection, malformed, unsupported, oversized files | Backend contract and integration tests |
| Mapping and validation | Arbitrary headers, missing fields, duplicate IDs, warnings, rejected rows | Row-level fixture suite |
| Generation | Queueing, polling/SSE, partial success, provider failure, quality gates | Worker and API integration tests |
| Lifecycle | Cancellation, retry, abandoned-job recovery, browser refresh | State-transition and browser tests |
| Results | Preview, individual artifacts, bulk ZIP, traceability, approval submission | End-to-end result workflow |
| Security | Path traversal, authorization, rate limits, retention, secret/log hygiene | Security regression suite and review |
| UI quality | Keyboard access, screen-reader labels, responsive layouts, loading/error states | Accessibility, visual, and responsive evidence |
| Operations | Metrics, audit events, cleanup, failure alerts, runbooks | Operational checklist and recovery drill |

**Dependencies:** Completion of the Phase 1–4 exit criteria.

**Exit criteria**

- The acceptance criteria in Section 14 are demonstrably satisfied.
- Backend and UI quality gates pass in CI.
- A clean-environment end-to-end run completes from upload through approval/download.
- Failure and recovery procedures are documented and exercised.
- No unresolved critical or high-severity security findings remain.

### Phase sequencing and change control

Phase 1 and Phase 2 establish the backend walking skeleton. Phase 3 can proceed in
parallel once the contracts are stable, but UI work must not introduce undocumented
API shapes. Phase 4 hardening should begin before production exposure, even if Phase 3
features are still being completed. Phase 5 is a release gate rather than a feature
phase and must be rerun after changes to contracts, worker state transitions, storage,
authentication, or artifact handling.

## 14. Acceptance Criteria

The workflow is complete when:

1. A user can upload a valid CSV or XLSX file from the UI.
2. The UI shows a bounded preview before generation.
3. XLSX users can select a worksheet.
4. Users can map arbitrary source headers to canonical fields.
5. Validation reports row-level errors and warnings.
6. Users can start generation only after validation policy is satisfied.
7. Generation runs asynchronously and survives browser refresh.
8. Progress is accurate and persisted.
9. Users can cancel and retry according to job state.
10. Partial success is visible without hiding failed rows.
11. Generated feature artifacts can be previewed and downloaded.
12. Quality-gate results are attached to each result.
13. Successful results can be submitted for approval.
14. Traceability links results back to source rows.
15. Audit events are created for all significant lifecycle actions.
16. Upload security limits and authorization are enforced.
17. Backend and UI tests cover the complete happy path and failure paths.

## 15. Recommended Next Task

Continue Phase 4 with structured metrics and operational alerts:

1. Instrument queue depth, job duration, throughput, failure, abandonment, and
   provider-facing metrics.
2. Expose a stable metrics surface for dashboards and monitoring.
3. Add metrics assertions and an operational alert/runbook checklist.
