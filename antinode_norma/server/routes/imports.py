"""Versioned CSV/XLSX import, validation, and generation job endpoints."""

import os
import uuid
import io
import zipfile
import csv
import openpyxl
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import PlainTextResponse, StreamingResponse

from antinode_norma.ingest_structured.csv import CSVIngester
from antinode_norma.ingest_structured.xlsx import XLSXIngester
from antinode_norma.core.normalize import normalize_header
from antinode_norma.server.import_storage import (
    get_generation, get_import, save_generation, save_import, update_import, get_generation_results,
    get_generation_result,
    list_generations,
    save_generation_result,
)
from antinode_norma.server.schemas import (
    GenerationJobResponse, GenerationJobListResponse, ImportResponse, ImportValidationResponse,
    GenerationJobRequest, GenerationApprovalRequest, ImportMappingRequest,
)
from antinode_norma.server.generation_worker import enqueue, cancel, retry, retry_result, wait_for
from antinode_norma.server.routes.approvals import gate

router = APIRouter(prefix="/imports", tags=["Imports"])
generation_router = APIRouter(prefix="/generation-jobs", tags=["Generation jobs"])
legacy_generation_router = APIRouter(prefix="/generation/jobs", tags=["Generation jobs"])
MAX_UPLOAD_BYTES = 25 * 1024 * 1024


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_file(path: Path, extension: str) -> list[dict[str, Any]]:
    ingester = CSVIngester() if extension == "csv" else XLSXIngester()
    return [case.model_dump() for case in ingester.ingest(path)]


def _source_preview(path: Path, extension: str, worksheet: str | None = None) -> tuple[list[str], list[dict[str, Any]], list[str], str | None]:
    """Read source headers/values without losing the names users need to map."""
    if extension == "csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            columns = list(reader.fieldnames or [])
            return columns, [dict(row) for row in reader], [], None
    workbook = openpyxl.load_workbook(path, data_only=True, read_only=True)
    names = list(workbook.sheetnames)
    selected = worksheet if worksheet in names else names[0] if names else None
    if selected is None:
        return [], [], names, None
    sheet = workbook[selected]
    values = list(sheet.iter_rows(values_only=True))
    columns = [str(value) if value is not None else "" for value in (values[0] if values else [])]
    rows = [
        {columns[index]: value for index, value in enumerate(row)
         if index < len(columns) and columns[index]}
        for row in values[1:]
        if any(value is not None for value in row)
    ]
    return columns, rows, names, selected


def _apply_mapping(source_rows: list[dict[str, Any]], mapping: dict[str, str]) -> list[dict[str, Any]]:
    """Convert source rows to the canonical shape consumed by validation/generation."""
    result = []
    canonical = {"id", "title", "role", "action", "benefit", "acceptance_criteria", "tags"}
    for index, source in enumerate(source_rows, 1):
        row: dict[str, Any] = {}
        for field, source_column in mapping.items():
            if field in canonical and source_column in source:
                row[field] = source[source_column]
        # Keep unmapped source columns as metadata, while preserving arbitrary values.
        for name, value in source.items():
            if name not in mapping.values() and value is not None:
                row[name] = value
        row.setdefault("id", f"TC-{index:03d}")
        row.setdefault("title", f"Test Case {index}")
        row.setdefault("role", "user")
        return_rows = row
        result.append(return_rows)
    return result


async def _create_import(file: UploadFile) -> ImportResponse:
    filename = Path(file.filename or "").name
    extension = Path(filename).suffix.lower().lstrip(".")
    if extension not in {"csv", "xlsx"}:
        raise HTTPException(status_code=415, detail="Only CSV and XLSX files are supported")
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Uploaded file exceeds the 25 MB limit")
    import_id = str(uuid.uuid4())
    directory = Path(os.getenv("NORMA_IMPORT_DIR", ".runtime/imports"))
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{import_id}.{extension}"
    path.write_bytes(content)
    try:
        columns, source_rows, worksheet_names, worksheet = _source_preview(path, extension)
        rows = _parse_file(path, extension)
    except Exception as exc:
        path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"Unable to parse {extension.upper()} file: {exc}") from exc
    record = {
        "id": import_id, "filename": filename, "format": extension,
        "storage_path": str(path), "status": "uploaded", "row_count": len(rows),
        "rows": rows, "created_at": _now(),
        "columns": columns, "worksheet_names": worksheet_names, "worksheet": worksheet,
        "mapping": {},
    }
    save_import(record)
    return ImportResponse(**{k: record.get(k) for k in (
        "id", "filename", "format", "status", "row_count", "created_at",
        "worksheet_names", "columns", "worksheet", "mapping")})


@router.post("/upload", response_model=ImportResponse, status_code=201)
async def upload_import(file: UploadFile = File(...)) -> ImportResponse:
    return await _create_import(file)


@router.post("", response_model=ImportResponse, status_code=201)
async def create_import(file: UploadFile = File(...)) -> ImportResponse:
    return await _create_import(file)


@router.get("/{import_id}/preview")
async def preview_import(import_id: str, limit: int = 100) -> dict[str, Any]:
    record = get_import(import_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Import not found")
    columns = record.get("columns", [])
    worksheet_names = record.get("worksheet_names", [])
    _, source_rows, _, _ = _source_preview(
        Path(record["storage_path"]), record["format"], record.get("worksheet")
    )
    preview_rows = []
    for index, row in enumerate(record["rows"][:max(0, min(limit, 1000))], 2):
        values = source_rows[index - 2] if index - 2 < len(source_rows) else row
        preview_rows.append({**row, "source_row": index, "values": values})
    return {"id": import_id, "filename": record["filename"], "format": record["format"],
            "row_count": record["row_count"], "columns": columns,
            "worksheet_names": worksheet_names, "worksheet": record.get("worksheet"),
            "mapping": record.get("mapping", {}), "truncated": record["row_count"] > len(preview_rows),
            "rows": preview_rows}


@router.post("/{import_id}/mapping")
async def map_import(import_id: str, request: ImportMappingRequest) -> dict[str, Any]:
    record = get_import(import_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Import not found")
    worksheet = request.worksheet or record.get("worksheet")
    if worksheet and worksheet not in record.get("worksheet_names", []):
        raise HTTPException(status_code=422, detail="Worksheet not found")
    unknown = set(request.columns.values()) - set(record.get("columns", []))
    if unknown:
        raise HTTPException(status_code=422, detail=f"Unknown source columns: {', '.join(sorted(unknown))}")
    invalid_fields = set(request.columns) - {"id", "title", "role", "action", "benefit", "acceptance_criteria", "tags"}
    if invalid_fields:
        raise HTTPException(status_code=422, detail=f"Unknown canonical fields: {', '.join(sorted(invalid_fields))}")
    path = Path(record["storage_path"])
    columns, source_rows, names, selected = _source_preview(path, record["format"], worksheet)
    mapping = request.columns or {
        normalize_header(column): column
        for column in columns
        if normalize_header(column) in {"id", "title", "role", "action", "benefit", "acceptance_criteria", "tags"}
    }
    rows = _apply_mapping(source_rows, mapping)
    update_import(import_id, rows=rows, row_count=len(rows), worksheet=selected, mapping=mapping)
    updated = get_import(import_id)
    return {"id": import_id, "worksheet": selected, "columns": columns,
            "worksheet_names": names, "mapping": mapping, "row_count": len(rows)}


@router.post("/{import_id}/validate", response_model=ImportValidationResponse)
async def validate_import(import_id: str) -> ImportValidationResponse:
    record = get_import(import_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Import not found")
    errors: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, row in enumerate(record["rows"], 1):
        if row["id"] in seen:
            errors.append({"row": index, "field": "id", "message": "Duplicate id"})
        seen.add(row["id"])
        for field in ("title", "action"):
            if not str(row.get(field, "")).strip():
                errors.append({"row": index, "field": field, "message": "Required value is missing"})
    return ImportValidationResponse(import_id=import_id, valid=not errors, errors=errors, row_count=record["row_count"])


@router.get("/{import_id}/validation", response_model=ImportValidationResponse)
async def get_import_validation(import_id: str) -> ImportValidationResponse:
    return await validate_import(import_id)


@router.get("/{import_id}", response_model=ImportResponse)
async def get_import_details(import_id: str) -> ImportResponse:
    record = get_import(import_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Import not found")
    return ImportResponse(**{
        key: record[key]
        for key in ("id", "filename", "format", "status", "row_count", "created_at",
                    "worksheet_names", "columns", "worksheet", "mapping")
    })


@generation_router.post("", response_model=GenerationJobResponse, status_code=201)
async def create_generation_job(request: GenerationJobRequest) -> GenerationJobResponse:
    import_id = request.import_id
    record = get_import(str(import_id)) if import_id else None
    if record is None:
        raise HTTPException(status_code=404, detail="Import not found")
    validation = await validate_import(str(import_id))
    job_id = str(uuid.uuid4())
    result = {"import_id": import_id, "row_count": record["row_count"], "valid": validation.valid,
              "errors": validation.errors}
    job = {"id": job_id, "import_id": import_id,
           "status": "queued" if validation.valid else "failed", "result": result,
           "total_rows": record["row_count"], "created_at": _now(),
           "error": None if validation.valid else "Validation failed"}
    save_generation(job)
    # Create durable row work items before handing the job to the worker.
    for row_number, row in enumerate(record["rows"], 1):
        save_generation_result({
            "id": str(uuid.uuid4()), "job_id": job_id, "row_number": row_number,
            "case_id": str(row.get("id") or row.get("story_id") or f"row-{row_number}"),
            "status": "pending", "created_at": _now(),
        })
    if validation.valid:
        enqueue(job_id)
    return GenerationJobResponse(**job)


@generation_router.get("", response_model=GenerationJobListResponse)
async def list_generation_jobs(
    status: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> GenerationJobListResponse:
    jobs, total = list_generations(status=status, offset=offset, limit=limit)
    items = []
    for job in jobs:
        total_rows = job.get("total_rows", 0)
        job["progress_percent"] = (
            round(job.get("processed_rows", 0) * 100 / total_rows, 1)
            if total_rows else 0
        )
        items.append(GenerationJobResponse(**job))
    return GenerationJobListResponse(items=items, total=total, offset=offset, limit=limit)


@generation_router.post("/{job_id}/cancel", response_model=GenerationJobResponse)
async def cancel_generation_job(job_id: str) -> GenerationJobResponse:
    job = get_generation(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Generation job not found")
    if job["status"] in {"completed", "completed_with_errors", "failed", "cancelled"}:
        raise HTTPException(status_code=409, detail="Generation job is not cancellable")
    cancel(job_id)
    return await get_generation_job(job_id)


@generation_router.post("/{job_id}/retry", response_model=GenerationJobResponse)
async def retry_generation_job(job_id: str) -> GenerationJobResponse:
    job = get_generation(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Generation job not found")
    if job["status"] not in {"failed", "completed_with_errors", "cancelled"}:
        raise HTTPException(status_code=409, detail="Only failed or cancelled jobs can be retried")
    retry(job_id)
    return await get_generation_job(job_id)


@generation_router.get("/{job_id}/results")
async def generation_results(job_id: str) -> dict[str, Any]:
    if get_generation(job_id) is None:
        raise HTTPException(status_code=404, detail="Generation job not found")
    results = get_generation_results(job_id)
    approvals = {
        request.source_result_id: request
        for request in gate.requests.values()
        if request.source_job_id == job_id and request.source_result_id
    }
    for result in results:
        approval = approvals.get(result["id"])
        result["approval_id"] = approval.id if approval else None
        result["approval_status"] = approval.status.value if approval else None
    return {"job_id": job_id, "results": results, "count": len(results)}


@generation_router.post("/{job_id}/results/{result_id}/retry", response_model=GenerationJobResponse)
async def retry_generation_result(job_id: str, result_id: str) -> GenerationJobResponse:
    job = get_generation(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Generation job not found")
    result = get_generation_result(job_id, result_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Generation result not found")
    if result["status"] != "failed":
        raise HTTPException(status_code=409, detail="Only failed results can be retried")
    if not retry_result(job_id, result_id):
        raise HTTPException(status_code=409, detail="Generation result could not be retried")
    return await get_generation_job(job_id)


@generation_router.post("/{job_id}/results/{result_id}/submit-approval")
async def submit_generation_result_for_approval(job_id: str, result_id: str) -> dict[str, Any]:
    if get_generation(job_id) is None:
        raise HTTPException(status_code=404, detail="Generation job not found")
    result = get_generation_result(job_id, result_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Generation result not found")
    if result["status"] != "completed" or not result.get("content"):
        raise HTTPException(status_code=409, detail="Only successful results can be submitted for approval")
    approval = gate.submit_request(
        feature_id=result["case_id"],
        gherkin_text=result["content"],
        requested_by="generation-workflow",
        source_job_id=job_id,
        source_result_id=result_id,
    )
    return approval.model_dump()


@generation_router.post("/{job_id}/results/submit-approval")
async def submit_generation_results_for_approval(
    job_id: str,
    request: GenerationApprovalRequest,
) -> dict[str, Any]:
    if get_generation(job_id) is None:
        raise HTTPException(status_code=404, detail="Generation job not found")
    submitted: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []
    for result_id in request.result_ids:
        result = get_generation_result(job_id, result_id)
        if result is None:
            rejected.append({"result_id": result_id, "reason": "Generation result not found"})
            continue
        if result["status"] != "completed" or not result.get("content"):
            rejected.append({"result_id": result_id, "reason": "Only successful results can be submitted for approval"})
            continue
        approval = gate.submit_request(
            feature_id=result["case_id"],
            gherkin_text=result["content"],
            requested_by="generation-workflow",
            source_job_id=job_id,
            source_result_id=result_id,
        )
        submitted.append(approval.model_dump())
    return {"job_id": job_id, "submitted": submitted, "rejected": rejected}


@generation_router.get("/{job_id}/results/{result_id}/download")
async def download_generation_result(job_id: str, result_id: str):
    if get_generation(job_id) is None:
        raise HTTPException(status_code=404, detail="Generation job not found")
    result = get_generation_result(job_id, result_id)
    if result is None or not result.get("content"):
        raise HTTPException(status_code=404, detail="Generated artifact not found")
    filename = result.get("artifact_name") or f"row-{result['row_number']}.feature"
    return PlainTextResponse(
        result["content"],
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@generation_router.get("/{job_id}/download")
async def download_generation(job_id: str):
    if get_generation(job_id) is None:
        raise HTTPException(status_code=404, detail="Generation job not found")
    results = [item for item in get_generation_results(job_id) if item.get("content")]
    if not results:
        raise HTTPException(status_code=404, detail="No generated artifacts available")
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for item in results:
            bundle.writestr(item["artifact_name"] or f"row-{item['row_number']}.feature", item["content"])
    archive.seek(0)
    return StreamingResponse(archive, media_type="application/zip",
                             headers={"Content-Disposition": f'attachment; filename="{job_id}.zip"'})


@generation_router.get("/{job_id}", response_model=GenerationJobResponse)
async def get_generation_job(job_id: str) -> GenerationJobResponse:
    job = get_generation(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Generation job not found")
    total = job.get("total_rows", 0)
    job["progress_percent"] = round(job.get("processed_rows", 0) * 100 / total, 1) if total else 0
    return GenerationJobResponse(**job)


@legacy_generation_router.post("", response_model=GenerationJobResponse, status_code=201)
async def create_legacy_generation_job(request: GenerationJobRequest) -> GenerationJobResponse:
    response = await create_generation_job(request)
    # Preserve the Phase 1 legacy contract while the public endpoint is asynchronous.
    if response.status == "queued":
        job = wait_for(response.id)
        return await get_generation_job(response.id) if job else response
    return response


@legacy_generation_router.get("/{job_id}", response_model=GenerationJobResponse)
async def get_legacy_generation_job(job_id: str) -> GenerationJobResponse:
    return await get_generation_job(job_id)
