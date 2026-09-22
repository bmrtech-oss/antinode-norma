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

- Generation jobs are not yet durable background workers.
- Generation currently validates imported rows but does not execute the full per-row feature-generation pipeline.
- Progress is not persisted per row.
- There is no cancellation or retry operation.
- There are no generated artifact records or downloads.
- XLSX worksheet selection is not exposed in the UI.
- Column mapping is implicit and does not support arbitrary source headers interactively.
- Validation results are not yet shown at row level.
- Job history and active-job views are not implemented.
- The existing Feature Review contract needs alignment with the feature API response shape.
- The current CLI contains fallback behavior that writes synthetic feature content after generation errors; the UI workflow must expose failures explicitly instead.

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

### Follow-up version

Add Server-Sent Events:

```text
GET /v1/generation-jobs/{job_id}/events
```

SSE is preferred over WebSockets because the UI primarily receives progress updates.

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

### Phase 1 — Contracts and persistence

- Define import, row, job, result, and artifact schemas.
- Complete upload, detail, preview, mapping, and validation endpoints.
- Persist import metadata and normalized rows.
- Add upload limits.
- Add backend unit tests.

### Phase 2 — Worker and artifacts

- Extract shared generation logic from the CLI.
- Add queued and running states.
- Add local background worker.
- Persist per-row progress.
- Persist generated feature artifacts.
- Add quality-gate execution per result.
- Add cancellation and retry.
- Add worker tests.

### Phase 3 — UI workflow

- Complete New Import.
- Add XLSX worksheet selection.
- Add column mapping.
- Add preview and validation issue table.
- Add active job progress.
- Add job history.
- Add results and downloads.
- Add approval submission.

### Phase 4 — Live updates and hardening

- Add SSE progress events.
- Add authentication and authorization checks.
- Add rate limits and concurrency limits.
- Add abandoned-job recovery.
- Add retention cleanup.
- Add operational metrics and alerts.
- Add audit coverage.

### Phase 5 — Full validation

Add automated coverage for:

- CSV upload.
- XLSX upload and worksheet selection.
- Invalid file type.
- Oversized file.
- Malformed file.
- Column mapping.
- Duplicate IDs.
- Missing required fields.
- Partial generation success.
- Provider failure.
- Progress polling/SSE.
- Cancellation.
- Retry.
- Browser refresh during active job.
- Artifact downloads.
- Approval submission.

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

Implement Phase 2 as the next vertical slice:

1. Extract shared per-test-case generation logic from the CLI.
2. Add a local background worker.
3. Add persisted row-level progress and result records.
4. Add `/cancel`, `/retry`, `/results`, and `/download` endpoints.
5. Update the Generation UI to poll the active job.
6. Add an end-to-end test from CSV upload through generated artifact download.
