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
    get_generation, get_import, get_generation_results, save_generation_result,
    update_generation, reset_generation_results, reset_generation_result,
    list_generations,
)

def _setting(name: str, default: int, minimum: int = 1) -> int:
    try:
        return max(minimum, int(os.getenv(name, str(default))))
    except (TypeError, ValueError):
        return default


_worker_count = _setting("NORMA_GENERATION_WORKERS", 2)
_queue_size = _setting("NORMA_GENERATION_QUEUE_SIZE", 8, minimum=0)
_executor = ThreadPoolExecutor(max_workers=_worker_count)
# ThreadPoolExecutor's internal queue is unbounded.  This semaphore makes the
# number of running plus queued jobs explicit and bounded.
_capacity = threading.BoundedSemaphore(_worker_count + _queue_size)
_cancel_events: dict[str, threading.Event] = {}
_lock = threading.Lock()


class GenerationQueueFull(Exception):
    """Raised when the configured worker and queue capacity is exhausted."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _timeout_seconds() -> int:
    return _setting("NORMA_GENERATION_ABANDON_TIMEOUT_SECONDS", 3600)


def _age_seconds(value: str | None) -> float:
    if not value:
        return 0
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return max(0, (datetime.now(timezone.utc) - timestamp).total_seconds())
    except (TypeError, ValueError):
        return 0


def recover_abandoned_jobs() -> int:
    """Recover durable work left behind by a crashed worker/process.

    Capacity is process-local, so a restart releases old leases.  Jobs are
    explicitly terminalized here and can be retried by their owner.
    """
    recovered = 0
    timeout = _timeout_seconds()
    for status in ("queued", "running", "cancelling"):
        jobs, _ = list_generations(status=status, include_all=True, limit=10000)
        for job in jobs:
            reference = job.get("started_at") if status != "queued" else job.get("created_at")
            if _age_seconds(reference) <= timeout:
                continue
            with _lock:
                event = _cancel_events.get(job["id"])
                if event:
                    event.set()
            update_generation(
                job["id"],
                status="abandoned",
                completed_at=_now(),
                current_item=None,
                error=f"Generation worker heartbeat exceeded {_timeout_seconds()} seconds",
            )
            recovered += 1
    return recovered


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
    try:
        job = get_generation(job_id)
        if not job:
            return
        if job["status"] == "abandoned":
            return
        imported = get_import(job["import_id"])
        if not imported:
            update_generation(job_id, status="failed", error="Import not found", completed_at=_now())
            return
        event = _cancel_events[job_id]
        rows = imported["rows"]
        update_generation(job_id, status="running", started_at=_now())
        existing = get_generation_results(job_id)
        completed_ids = {item["row_number"] for item in existing if item["status"] == "completed"}
        failed = sum(1 for item in existing if item["status"] == "failed")
        successful = len(completed_ids)
        warnings = sum(len(item.get("warnings", [])) > 0 for item in existing if item["status"] == "completed")
        processed = successful + failed
        for row_number, row in enumerate(rows, 1):
            if row_number in completed_ids:
                continue
            current = get_generation(job_id)
            if not current or current["status"] == "abandoned":
                return
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
        current = get_generation(job_id)
        if current and current["status"] != "abandoned":
            status = "completed" if not failed else "completed_with_errors"
            update_generation(job_id, status=status, current_item=None, completed_at=_now())
    finally:
        _capacity.release()


def enqueue(job_id: str) -> None:
    if not _capacity.acquire(blocking=False):
        raise GenerationQueueFull("Generation worker capacity is exhausted")
    with _lock:
        event = threading.Event()
        _cancel_events[job_id] = event
    try:
        _executor.submit(_run, job_id)
    except Exception:
        _capacity.release()
        raise


def cancel(job_id: str) -> bool:
    with _lock:
        event = _cancel_events.get(job_id)
        if event is None:
            return False
        event.set()
    update_generation(job_id, status="cancelling")
    return True


def retry(job_id: str) -> None:
    if not _capacity.acquire(blocking=False):
        raise GenerationQueueFull("Generation worker capacity is exhausted")
    with _lock:
        _cancel_events[job_id] = threading.Event()
    try:
        reset_generation_results(job_id)
        update_generation(job_id, status="queued", processed_rows=0, successful_rows=0,
                          warning_rows=0, failed_rows=0, current_item=None, started_at=None,
                          completed_at=None, error=None)
        # Results are replaced by row number on retry.
        _executor.submit(_run, job_id)
    except Exception:
        _capacity.release()
        raise


def retry_result(job_id: str, result_id: str) -> bool:
    if not _capacity.acquire(blocking=False):
        raise GenerationQueueFull("Generation worker capacity is exhausted")
    with _lock:
        _cancel_events[job_id] = threading.Event()
    try:
        if not reset_generation_result(job_id, result_id):
            _capacity.release()
            return False
        job = get_generation(job_id)
        if not job:
            _capacity.release()
            return False
        update_generation(job_id, status="queued", current_item=None, completed_at=None, error=None)
        _executor.submit(_run, job_id)
        return True
    except Exception:
        _capacity.release()
        raise


def wait_for(job_id: str, timeout: float = 10) -> dict:
    import time
    deadline = time.time() + timeout
    while time.time() < deadline:
        job = get_generation(job_id)
        if job and job["status"] not in {"queued", "running", "cancelling"}:
            return job
        time.sleep(0.01)
    return get_generation(job_id)
