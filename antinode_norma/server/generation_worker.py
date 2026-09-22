"""Durable, single-process generation worker used by the local FastAPI deployment."""
import os
import re
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from antinode_norma.ingest_structured.story import story_to_case
from antinode_norma.server.import_storage import (
    get_generation, get_import, save_generation_result, update_generation, reset_generation_results,
)

_executor = ThreadPoolExecutor(max_workers=int(os.getenv("NORMA_GENERATION_WORKERS", "2")))
_cancel_events: dict[str, threading.Event] = {}
_lock = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _render(case) -> str:
    criteria = case.acceptance_criteria or [f"the user can {case.action}"]
    lines = [f"Feature: {case.title}", "", f"  Scenario: {case.title}",
             f"    Given I am a {case.role}", f"    When I {case.action}",
             f"    Then I should {case.benefit or criteria[0]}"]
    return "\n".join(lines) + "\n"


def _artifact_name(case_id: str) -> str:
    safe_id = re.sub(r"[^A-Za-z0-9._-]+", "_", case_id).strip("._")
    return f"{safe_id or 'row'}.feature"


def _run(job_id: str) -> None:
    job = get_generation(job_id)
    if not job:
        return
    imported = get_import(job["import_id"])
    if not imported:
        update_generation(job_id, status="failed", error="Import not found", completed_at=_now())
        return
    event = _cancel_events[job_id]
    rows = imported["rows"]
    update_generation(job_id, status="running", started_at=_now())
    processed = successful = warnings = failed = 0
    for row_number, row in enumerate(rows, 1):
        if event.is_set():
            update_generation(job_id, status="cancelled", completed_at=_now(), current_item=None)
            return
        case_id = str(row.get("id") or row.get("story_id") or f"row-{row_number}")
        update_generation(job_id, current_item=case_id)
        try:
            case = story_to_case(row)
            if not case.action.strip() or not case.title.strip():
                raise ValueError("Required title or action is missing")
            content = _render(case)
            artifact_dir = Path(os.getenv("NORMA_ARTIFACT_DIR", ".runtime/artifacts")) / job_id
            artifact_dir.mkdir(parents=True, exist_ok=True)
            name = _artifact_name(case_id)
            path = artifact_dir / name
            path.write_text(content, encoding="utf-8")
            save_generation_result({"id": str(uuid.uuid4()), "job_id": job_id,
                "row_number": row_number, "case_id": case_id, "status": "completed",
                "artifact_path": str(path), "artifact_name": name, "content": content,
                "created_at": _now()})
            successful += 1
        except Exception as exc:
            failed += 1
            save_generation_result({"id": str(uuid.uuid4()), "job_id": job_id,
                "row_number": row_number, "case_id": case_id, "status": "failed",
                "error": str(exc), "created_at": _now()})
        processed += 1
        update_generation(job_id, processed_rows=processed, successful_rows=successful,
                          warning_rows=warnings, failed_rows=failed)
    status = "completed" if not failed else "completed_with_errors"
    update_generation(job_id, status=status, current_item=None, completed_at=_now())


def enqueue(job_id: str) -> None:
    with _lock:
        event = threading.Event()
        _cancel_events[job_id] = event
        _executor.submit(_run, job_id)


def cancel(job_id: str) -> bool:
    with _lock:
        event = _cancel_events.get(job_id)
        if event is None:
            return False
        event.set()
    update_generation(job_id, status="cancelling")
    return True


def retry(job_id: str) -> None:
    with _lock:
        _cancel_events[job_id] = threading.Event()
    reset_generation_results(job_id)
    update_generation(job_id, status="queued", processed_rows=0, successful_rows=0,
                      warning_rows=0, failed_rows=0, current_item=None, started_at=None,
                      completed_at=None, error=None)
    # Results are replaced by row number on retry.
    _executor.submit(_run, job_id)


def wait_for(job_id: str, timeout: float = 10) -> dict:
    import time
    deadline = time.time() + timeout
    while time.time() < deadline:
        job = get_generation(job_id)
        if job and job["status"] not in {"queued", "running", "cancelling"}:
            return job
        time.sleep(0.01)
    return get_generation(job_id)
