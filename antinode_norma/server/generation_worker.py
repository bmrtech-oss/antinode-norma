"""Durable, single-process generation worker used by the local FastAPI deployment."""
import os
import re
import threading
import time
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
from antinode_norma.utils.observability import metrics_registry


class ProviderTimeoutError(TimeoutError):
    """Provider did not return within the configured deadline."""


class ProviderCircuitOpenError(RuntimeError):
    """Provider calls are temporarily short-circuited after repeated failures."""


class ProviderExecutionError(RuntimeError):
    """A provider failed after the bounded retry policy was exhausted."""


class _ProviderCircuit:
    def __init__(self):
        self.failures = 0
        self.opened_at = 0.0
        self.lock = threading.Lock()

    def allow(self, reset_seconds: float) -> bool:
        with self.lock:
            if not self.opened_at:
                return True
            if time.monotonic() - self.opened_at >= reset_seconds:
                self.opened_at = 0.0
                self.failures = 0
                return True
            return False

    def success(self) -> None:
        with self.lock:
            self.failures = 0
            self.opened_at = 0.0

    def failure(self, threshold: int) -> None:
        with self.lock:
            self.failures += 1
            if self.failures >= threshold:
                self.opened_at = time.monotonic()


_provider_circuits: dict[str, _ProviderCircuit] = {}
_provider_circuits_lock = threading.Lock()


def _float_setting(name: str, default: float, minimum: float = 0.0) -> float:
    try:
        return max(minimum, float(os.getenv(name, str(default))))
    except (TypeError, ValueError):
        return default


def _provider_circuit(name: str) -> _ProviderCircuit:
    with _provider_circuits_lock:
        return _provider_circuits.setdefault(name, _ProviderCircuit())


def _call_with_timeout(provider, prompt: str, timeout: float, cancel_event: threading.Event):
    """Run an untrusted provider without making cancellation wait for it."""
    result = []
    error = []

    def invoke():
        try:
            result.append(provider(prompt))
        except BaseException as exc:  # preserve provider exception type, not its message
            error.append(exc)

    thread = threading.Thread(target=invoke, daemon=True)
    thread.start()
    deadline = time.monotonic() + timeout
    while thread.is_alive():
        if cancel_event.is_set():
            raise InterruptedError("provider call cancelled")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ProviderTimeoutError("provider timeout")
        thread.join(min(0.05, remaining))
    if error:
        raise error[0]
    return result[0] if result else ""


def execute_provider(provider, prompt: str, cancel_event: threading.Event,
                     provider_name: str = "default") -> str:
    """Execute a provider with timeout, bounded retry/backoff, and a circuit breaker.

    Error messages intentionally contain only stable categories; provider responses,
    prompts, URLs, and exception text are never written to logs or durable state.
    """
    timeout = _float_setting("NORMA_GENERATION_PROVIDER_TIMEOUT_SECONDS", 30.0, 0.01)
    retries = _setting("NORMA_GENERATION_PROVIDER_MAX_RETRIES", 2, minimum=0)
    base = _float_setting("NORMA_GENERATION_PROVIDER_RETRY_BASE_SECONDS", 0.5)
    maximum = _float_setting("NORMA_GENERATION_PROVIDER_RETRY_MAX_SECONDS", 8.0)
    threshold = _setting("NORMA_GENERATION_CIRCUIT_FAILURE_THRESHOLD", 3)
    reset = _float_setting("NORMA_GENERATION_CIRCUIT_RESET_SECONDS", 30.0)
    circuit = _provider_circuit(provider_name)
    if not circuit.allow(reset):
        metrics_registry.record_provider_call(circuit_open=True)
        raise ProviderCircuitOpenError("provider circuit open")
    for attempt in range(retries + 1):
        if cancel_event.is_set():
            raise InterruptedError("provider call cancelled")
        try:
            value = _call_with_timeout(provider, prompt, timeout, cancel_event)
            circuit.success()
            metrics_registry.record_provider_call(success=True, retry=attempt > 0)
            return value
        except InterruptedError:
            raise
        except Exception as exc:
            circuit.failure(threshold)
            metrics_registry.record_provider_call(
                timeout=isinstance(exc, ProviderTimeoutError), retry=attempt < retries)
            if attempt >= retries:
                category = "timeout" if isinstance(exc, ProviderTimeoutError) else "failure"
                raise ProviderExecutionError(f"provider {category} after retries") from None
            delay = min(maximum, base * (2 ** attempt))
            if cancel_event.wait(delay):
                raise InterruptedError("provider call cancelled")
    raise ProviderExecutionError("provider failure after retries")

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
metrics_registry.set_generation_capacity(_worker_count + _queue_size)


class GenerationQueueFull(Exception):
    """Raised when the configured worker and queue capacity is exhausted."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _timeout_seconds() -> int:
    return _setting("NORMA_GENERATION_ABANDON_TIMEOUT_SECONDS", 3600)


def _audit(action: str, job: dict, *, result: str = "success", **metadata) -> None:
    """Write safe worker lifecycle metadata without row contents or prompts."""
    from antinode_norma.server.routes.audit import audit_log
    payload = {
        "job_id": job.get("id"),
        "import_id": job.get("import_id"),
        "owner_id": job.get("owner_id"),
        "tenant_id": job.get("tenant_id") or "default",
        "status": job.get("status"),
        "result": result,
    }
    safe_keys = {
        "processed_rows", "successful_rows", "failed_rows", "warning_rows",
        "row_number", "error_type",
    }
    payload.update({
        key: value for key, value in metadata.items()
        if key in safe_keys and value is not None
    })
    audit_log.record_event(
        action=action,
        resource=str(job.get("id")),
        actor=str(job.get("owner_id") or "system"),
        payload=payload,
    )


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
            job["status"] = "abandoned"
            _audit("generation.abandoned", job, result="failure",
                   processed_rows=job.get("processed_rows", 0),
                   error_type="worker_heartbeat_timeout")
            metrics_registry.record_generation_finished("abandoned", rows_processed=job.get("processed_rows", 0))
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


def _generate_content(case, event: threading.Event) -> str:
    """Render locally unless an explicitly configured LLM provider is enabled."""
    provider_name = os.getenv("NORMA_GENERATION_PROVIDER", "").strip()
    prompt = _render(case)
    if not provider_name:
        return prompt
    from antinode_norma.utils.llm_factory import create_llm_callable
    provider = create_llm_callable({
        "provider": provider_name,
        "model": os.getenv("NORMA_GENERATION_MODEL", "gpt-4o-mini"),
    })
    return execute_provider(provider, prompt, event, provider_name)


def _safe_error(exc: Exception) -> str:
    if isinstance(exc, ProviderCircuitOpenError):
        return "provider circuit open"
    if isinstance(exc, ProviderTimeoutError):
        return "provider timeout"
    if isinstance(exc, ProviderExecutionError):
        return str(exc)
    if isinstance(exc, InterruptedError):
        return "provider call cancelled"
    return type(exc).__name__


def _run(job_id: str) -> None:
    started = time.monotonic()
    metrics_registry.record_generation_started()
    try:
        job = get_generation(job_id)
        if not job:
            metrics_registry.record_generation_not_started()
            return
        if job["status"] == "abandoned":
            return
        _audit("generation.started", job, status="running")
        imported = get_import(job["import_id"])
        if not imported:
            update_generation(job_id, status="failed", error="Import not found", completed_at=_now())
            job["status"] = "failed"
            _audit("generation.failed", job, result="failure", error_type="import_not_found")
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
                job["status"] = "cancelled"
                _audit("generation.cancelled", job, processed_rows=processed)
                return
            case_id = str(row.get("id") or row.get("story_id") or f"row-{row_number}")
            update_generation(job_id, current_item=case_id)
            try:
                case = story_to_case(row)
                if not case.action.strip() or not case.title.strip():
                    raise ValueError("Required title or action is missing")
                content = _generate_content(case, event)
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
                if event.is_set() or isinstance(exc, InterruptedError):
                    update_generation(job_id, status="cancelled", completed_at=_now(),
                                      current_item=None)
                    job["status"] = "cancelled"
                    _audit("generation.cancelled", job, processed_rows=processed)
                    return
                failed += 1
                save_generation_result({"id": str(uuid.uuid4()), "job_id": job_id,
                    "row_number": row_number, "case_id": case_id, "status": "failed",
                    "error": _safe_error(exc), "created_at": _now()})
                _audit("generation.failed", {**job, "status": "running"},
                       result="failure", row_number=row_number,
                       error_type=type(exc).__name__)
            processed += 1
            update_generation(job_id, processed_rows=processed, successful_rows=successful,
                              warning_rows=warnings, failed_rows=failed)
        current = get_generation(job_id)
        if current and current["status"] != "abandoned":
            status = "completed" if not failed else "completed_with_errors"
            update_generation(job_id, status=status, current_item=None, completed_at=_now())
            current["status"] = status
            _audit("generation.completed", current, processed_rows=processed,
                   successful_rows=successful, failed_rows=failed,
                   warning_rows=warnings)
    finally:
        current = get_generation(job_id)
        if current and current["status"] in {"completed", "completed_with_errors", "failed", "cancelled", "abandoned"}:
            metrics_registry.record_generation_finished(
                current["status"], time.monotonic() - started,
                current.get("processed_rows", 0),
            )
        elif current:
            metrics_registry.record_generation_worker_stopped()
        _capacity.release()


def enqueue(job_id: str) -> None:
    if not _capacity.acquire(blocking=False):
        raise GenerationQueueFull("Generation worker capacity is exhausted")
    with _lock:
        event = threading.Event()
        _cancel_events[job_id] = event
    metrics_registry.record_generation_admitted()
    try:
        _executor.submit(_run, job_id)
    except Exception:
        metrics_registry.record_generation_not_started()
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
    metrics_registry.record_generation_admitted()
    try:
        reset_generation_results(job_id)
        update_generation(job_id, status="queued", processed_rows=0, successful_rows=0,
                          warning_rows=0, failed_rows=0, current_item=None, started_at=None,
                          completed_at=None, error=None)
        # Results are replaced by row number on retry.
        _executor.submit(_run, job_id)
    except Exception:
        metrics_registry.record_generation_not_started()
        _capacity.release()
        raise


def retry_result(job_id: str, result_id: str) -> bool:
    if not _capacity.acquire(blocking=False):
        raise GenerationQueueFull("Generation worker capacity is exhausted")
    with _lock:
        _cancel_events[job_id] = threading.Event()
    metrics_registry.record_generation_admitted()
    try:
        if not reset_generation_result(job_id, result_id):
            metrics_registry.record_generation_not_started()
            _capacity.release()
            return False
        job = get_generation(job_id)
        if not job:
            metrics_registry.record_generation_not_started()
            _capacity.release()
            return False
        update_generation(job_id, status="queued", current_item=None, completed_at=None, error=None)
        _executor.submit(_run, job_id)
        return True
    except Exception:
        metrics_registry.record_generation_not_started()
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
