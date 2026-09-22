from datetime import datetime, timedelta, timezone
import os

from antinode_norma.server.import_storage import (
    cleanup_retention,
    get_generation_result,
    save_generation,
    save_generation_result,
    save_import,
)


def test_retention_removes_stale_terminal_artifacts_and_orphan_imports(tmp_path, monkeypatch):
    db = tmp_path / "jobs.sqlite3"
    imports = tmp_path / "imports"
    artifacts = tmp_path / "artifacts"
    monkeypatch.setenv("NORMA_IMPORT_DB", str(db))
    monkeypatch.setenv("NORMA_IMPORT_DIR", str(imports))
    monkeypatch.setenv("NORMA_ARTIFACT_DIR", str(artifacts))
    monkeypatch.setenv("NORMA_ARTIFACT_RETENTION_DAYS", "1")
    monkeypatch.setenv("NORMA_IMPORT_RETENTION_DAYS", "1")
    old = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()

    source = imports / "orphan.csv"
    source.parent.mkdir()
    source.write_text("id,title,action\n", encoding="utf-8")
    save_import({
        "id": "orphan-import", "filename": "orphan.csv", "format": "csv",
        "storage_path": str(source), "status": "uploaded", "row_count": 0,
        "rows": [], "created_at": old,
    })

    artifact = artifacts / "job-terminal" / "TC-1.feature"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("Feature: old\n", encoding="utf-8")
    orphan_artifact = artifacts / "orphan.feature"
    orphan_artifact.write_text("Feature: orphan\n", encoding="utf-8")
    orphan_timestamp = (datetime.now(timezone.utc) - timedelta(days=3)).timestamp()
    os.utime(orphan_artifact, (orphan_timestamp, orphan_timestamp))
    save_import({
        "id": "terminal-import", "filename": "terminal.csv", "format": "csv",
        "storage_path": str(tmp_path / "terminal.csv"), "status": "uploaded",
        "row_count": 1, "rows": [], "created_at": old,
    })
    save_generation({
        "id": "job-terminal", "import_id": "terminal-import", "status": "completed",
        "result": {}, "created_at": old,
    })
    save_generation_result({
        "id": "result-terminal", "job_id": "job-terminal", "row_number": 1,
        "case_id": "TC-1", "status": "completed", "artifact_path": str(artifact),
        "artifact_name": "TC-1.feature", "content": "Feature: old\n", "created_at": old,
    })

    report = cleanup_retention()
    assert report["deleted_artifacts"] == 1
    assert report["deleted_imports"] == 1
    assert artifact.exists()
    assert not orphan_artifact.exists()
    assert not source.exists()
    assert get_generation_result("job-terminal", "result-terminal")["artifact_path"] == str(artifact)
    assert cleanup_retention()["deleted_artifacts"] == 0


def test_retention_protects_active_and_recently_recoverable_jobs(tmp_path, monkeypatch):
    monkeypatch.setenv("NORMA_IMPORT_DB", str(tmp_path / "jobs.sqlite3"))
    monkeypatch.setenv("NORMA_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    monkeypatch.setenv("NORMA_ARTIFACT_RETENTION_DAYS", "0")
    monkeypatch.setenv("NORMA_GENERATION_ABANDON_TIMEOUT_SECONDS", "3600")
    old = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    root = tmp_path / "artifacts"
    active_path = root / "active" / "row.feature"
    abandoned_path = root / "abandoned" / "row.feature"
    for path in (active_path, abandoned_path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Feature: protected\n", encoding="utf-8")

    for job_id, import_id, status, path in (
        ("job-active", "import-active", "running", active_path),
        ("job-abandoned", "import-abandoned", "abandoned", abandoned_path),
    ):
        save_import({
            "id": import_id, "filename": f"{job_id}.csv", "format": "csv",
            "storage_path": str(tmp_path / f"{job_id}.csv"), "status": "uploaded",
            "row_count": 1, "rows": [], "created_at": old,
        })
        save_generation({
            "id": job_id, "import_id": import_id, "status": status,
            "result": {}, "created_at": old, "started_at": old,
        })
        save_generation_result({
            "id": f"{job_id}-result", "job_id": job_id, "row_number": 1,
            "status": "completed", "artifact_path": str(path),
            "artifact_name": "row.feature", "content": "Feature: protected\n",
            "created_at": old,
        })

    report = cleanup_retention()
    assert report["skipped_protected"] == 2
    assert active_path.exists()
    assert abandoned_path.exists()
