import io
import threading
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from antinode_norma.server.api import app
from antinode_norma.server import generation_worker
from antinode_norma.server.import_storage import save_generation, save_import, get_generation


def _upload(client, headers):
    return client.post(
        "/v1/imports",
        headers=headers,
        files={"file": ("cases.csv", io.BytesIO(b"ID,Summary,Action\nTC-1,Login,log in\n"), "text/csv")},
    )


def test_upload_rate_limit_is_per_user(tmp_path, monkeypatch):
    monkeypatch.setenv("NORMA_IMPORT_DB", str(tmp_path / "jobs.sqlite3"))
    monkeypatch.setenv("NORMA_IMPORT_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("NORMA_UPLOAD_RATE_LIMIT", "1")
    client = TestClient(app)
    assert _upload(client, {"X-User-ID": "admin-limit-a"}).status_code == 201
    assert _upload(client, {"X-User-ID": "admin-limit-a"}).status_code == 429
    assert _upload(client, {"X-User-ID": "admin-limit-b"}).status_code == 201


def test_generation_rate_limit_and_full_queue_are_explicit(tmp_path, monkeypatch):
    monkeypatch.setenv("NORMA_IMPORT_DB", str(tmp_path / "jobs.sqlite3"))
    monkeypatch.setenv("NORMA_IMPORT_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("NORMA_GENERATION_RATE_LIMIT", "1")
    client = TestClient(app)
    headers = {"X-User-ID": "admin-generation-limit"}
    imported = _upload(client, headers).json()
    assert client.post("/v1/generation-jobs", headers=headers,
                       json={"import_id": imported["id"]}).status_code == 201
    assert client.post("/v1/generation-jobs", headers=headers,
                       json={"import_id": imported["id"]}).status_code == 429

    # Admission is non-blocking: a saturated bounded executor rejects work
    # instead of allowing an unbounded in-memory backlog.
    monkeypatch.setenv("NORMA_GENERATION_RATE_LIMIT", "0")
    original = generation_worker._capacity
    generation_worker._capacity = threading.BoundedSemaphore(0)
    try:
        imported = _upload(client, {"X-User-ID": "admin-queue-limit"}).json()
        response = client.post("/v1/generation-jobs", headers={"X-User-ID": "admin-queue-limit"},
                               json={"import_id": imported["id"]})
        assert response.status_code == 503
    finally:
        generation_worker._capacity = original


def test_startup_sweep_marks_interrupted_jobs_abandoned_and_retryable(tmp_path, monkeypatch):
    monkeypatch.setenv("NORMA_IMPORT_DB", str(tmp_path / "jobs.sqlite3"))
    monkeypatch.setenv("NORMA_GENERATION_ABANDON_TIMEOUT_SECONDS", "1")
    old = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    owner = "interrupted-worker"
    tenant = "tenant-recovery"
    save_import({
        "id": "import-recovery", "filename": "cases.csv", "format": "csv",
        "storage_path": str(tmp_path / "cases.csv"), "status": "uploaded",
        "row_count": 1, "rows": [{"id": "TC-1", "title": "Login", "action": "log in"}],
        "created_at": old, "owner_id": owner, "tenant_id": tenant,
    })
    save_generation({
        "id": "job-recovery", "import_id": "import-recovery", "status": "running",
        "created_at": old, "started_at": old, "total_rows": 1,
        "owner_id": owner, "tenant_id": tenant,
    })

    assert generation_worker.recover_abandoned_jobs() == 1
    job = get_generation("job-recovery")
    assert job["status"] == "abandoned"
    assert job["completed_at"]
    assert "heartbeat exceeded" in job["error"]
