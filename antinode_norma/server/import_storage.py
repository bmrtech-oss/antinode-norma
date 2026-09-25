"""Small SQLite persistence layer for structured import and generation jobs."""

import json
import os
import time
from antinode_norma.utils.observability import metrics_registry
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


class _PostgresCompat:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        self.connection.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return self.connection.__exit__(exc_type, exc_value, traceback)

    def execute(self, statement: str, parameters=()):
        return self.connection.execute(statement.replace("?", "%s"), parameters)

    def commit(self):
        self.connection.commit()

    def close(self):
        self.connection.close()


def _retention_setting(name: str, default: int) -> int:
    try:
        return max(0, int(os.getenv(name, str(default))))
    except (TypeError, ValueError):
        return default


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def _is_within_root(path: Path, root: Path) -> bool:
    """Only permit cleanup of a file below the configured storage root."""
    try:
        path.resolve().relative_to(root.resolve())
        return path.resolve() != root.resolve()
    except ValueError:
        return False


def database_path() -> Path:
    path = Path(os.getenv("NORMA_IMPORT_DB", ".runtime/import_jobs.sqlite3"))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def connect() -> sqlite3.Connection:
    database_url = os.getenv("DATABASE_URL", "")
    if database_url.startswith(("postgresql://", "postgres://")):
        import psycopg
        from psycopg.rows import dict_row

        from antinode_norma.database import migrate

        migrate(database_url)
        connection = psycopg.connect(database_url, row_factory=dict_row)
        connection.execute("CREATE SEQUENCE IF NOT EXISTS generation_events_id_seq")
        connection.execute(
            "ALTER TABLE generation_events ALTER COLUMN id SET DEFAULT nextval('generation_events_id_seq')"
        )
        connection.commit()
        return _PostgresCompat(connection)
    path = database_path()
    database_exists = path.exists()
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    if not database_exists:
        for attempt in range(10):
            try:
                connection.execute("PRAGMA journal_mode=WAL")
                break
            except sqlite3.OperationalError as error:
                if "locked" not in str(error).lower() or attempt == 9:
                    raise
                time.sleep(0.05)
    connection.execute("PRAGMA busy_timeout=10000")
    connection.execute(
        """CREATE TABLE IF NOT EXISTS import_jobs (
            id TEXT PRIMARY KEY, filename TEXT NOT NULL, format TEXT NOT NULL,
            storage_path TEXT NOT NULL, status TEXT NOT NULL, row_count INTEGER NOT NULL,
            rows_json TEXT NOT NULL, created_at TEXT NOT NULL,
            columns_json TEXT NOT NULL DEFAULT '[]',
            worksheet_names_json TEXT NOT NULL DEFAULT '[]',
            worksheet TEXT, mapping_json TEXT NOT NULL DEFAULT '{}',
            owner_id TEXT, tenant_id TEXT
        )"""
    )
    connection.execute("""CREATE TABLE IF NOT EXISTS generation_jobs (
        id TEXT PRIMARY KEY, import_id TEXT NOT NULL, status TEXT NOT NULL,
        result_json TEXT NOT NULL, created_at TEXT NOT NULL,
        total_rows INTEGER NOT NULL DEFAULT 0, processed_rows INTEGER NOT NULL DEFAULT 0,
        successful_rows INTEGER NOT NULL DEFAULT 0, warning_rows INTEGER NOT NULL DEFAULT 0,
        failed_rows INTEGER NOT NULL DEFAULT 0, current_item TEXT,
        started_at TEXT, completed_at TEXT, error TEXT,
        owner_id TEXT, tenant_id TEXT,
        FOREIGN KEY(import_id) REFERENCES import_jobs(id)
    )""")
    columns = {row["name"] for row in connection.execute("PRAGMA table_info(import_jobs)")}
    for name, definition in {
        "columns_json": "TEXT NOT NULL DEFAULT '[]'",
        "worksheet_names_json": "TEXT NOT NULL DEFAULT '[]'",
        "worksheet": "TEXT",
        "mapping_json": "TEXT NOT NULL DEFAULT '{}'",
    }.items():
        if name not in columns:
            connection.execute(f"ALTER TABLE import_jobs ADD COLUMN {name} {definition}")
    for name in ("owner_id", "tenant_id"):
        if name not in columns:
            connection.execute(f"ALTER TABLE import_jobs ADD COLUMN {name} TEXT")
    # Upgrade databases created by the Phase 1 implementation.
    columns = {row["name"] for row in connection.execute("PRAGMA table_info(generation_jobs)")}
    for name, definition in {
        "total_rows": "INTEGER NOT NULL DEFAULT 0", "processed_rows": "INTEGER NOT NULL DEFAULT 0",
        "successful_rows": "INTEGER NOT NULL DEFAULT 0", "warning_rows": "INTEGER NOT NULL DEFAULT 0",
        "failed_rows": "INTEGER NOT NULL DEFAULT 0", "current_item": "TEXT",
        "started_at": "TEXT", "completed_at": "TEXT", "error": "TEXT",
    }.items():
        if name not in columns:
            connection.execute(f"ALTER TABLE generation_jobs ADD COLUMN {name} {definition}")
    for name in ("owner_id", "tenant_id"):
        if name not in columns:
            connection.execute(f"ALTER TABLE generation_jobs ADD COLUMN {name} TEXT")
    connection.execute("""CREATE TABLE IF NOT EXISTS generation_results (
        id TEXT PRIMARY KEY, job_id TEXT NOT NULL, row_number INTEGER NOT NULL,
        case_id TEXT, status TEXT NOT NULL, artifact_path TEXT, artifact_name TEXT,
        content TEXT, warnings_json TEXT NOT NULL DEFAULT '[]', error TEXT,
        created_at TEXT NOT NULL, owner_id TEXT, tenant_id TEXT,
        UNIQUE(job_id, row_number),
        FOREIGN KEY(job_id) REFERENCES generation_jobs(id)
    )""")
    connection.execute("""CREATE TABLE IF NOT EXISTS generation_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(job_id) REFERENCES generation_jobs(id)
    )""")
    connection.commit()
    return connection


def save_import(record: dict[str, Any]) -> None:
    with connect() as db:
        db.execute(
            """INSERT INTO import_jobs
            (id, filename, format, storage_path, status, row_count, rows_json, created_at,
             columns_json, worksheet_names_json, worksheet, mapping_json, owner_id, tenant_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (record["id"], record["filename"], record["format"], record["storage_path"],
             record["status"], record["row_count"], json.dumps(record["rows"]), record["created_at"],
             json.dumps(record.get("columns", [])), json.dumps(record.get("worksheet_names", [])),
             record.get("worksheet"), json.dumps(record.get("mapping", {})),
             record.get("owner_id"), record.get("tenant_id")),
        )


def get_import(import_id: str) -> Optional[dict[str, Any]]:
    with connect() as db:
        row = db.execute("SELECT * FROM import_jobs WHERE id = ?", (import_id,)).fetchone()
    if row is None:
        return None
    result = dict(row)
    result["rows"] = json.loads(result.pop("rows_json"))
    result["columns"] = json.loads(result.pop("columns_json") or "[]")
    result["worksheet_names"] = json.loads(result.pop("worksheet_names_json") or "[]")
    result["mapping"] = json.loads(result.pop("mapping_json") or "{}")
    return result


def update_import(import_id: str, **fields: Any) -> None:
    allowed = {"rows", "row_count", "worksheet", "mapping", "status"}
    values = {key: value for key, value in fields.items() if key in allowed}
    if "rows" in values:
        values["rows_json"] = json.dumps(values.pop("rows"))
    if "mapping" in values:
        values["mapping_json"] = json.dumps(values.pop("mapping"))
    if not values:
        return
    with connect() as db:
        db.execute(
            f"UPDATE import_jobs SET {', '.join(f'{key} = ?' for key in values)} WHERE id = ?",
            (*values.values(), import_id),
        )


def save_generation(record: dict[str, Any]) -> None:
    with connect() as db:
        db.execute(
            """INSERT INTO generation_jobs
            (id, import_id, status, result_json, created_at, total_rows, processed_rows,
             successful_rows, warning_rows, failed_rows, current_item, started_at, completed_at, error,
             owner_id, tenant_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (record["id"], record["import_id"], record["status"], json.dumps(record.get("result", {})),
             record["created_at"], record.get("total_rows", 0), record.get("processed_rows", 0),
             record.get("successful_rows", 0), record.get("warning_rows", 0), record.get("failed_rows", 0),
             record.get("current_item"), record.get("started_at"), record.get("completed_at"), record.get("error"),
             record.get("owner_id"), record.get("tenant_id")),
        )
        _save_generation_event(db, record)


def get_generation(job_id: str) -> Optional[dict[str, Any]]:
    with connect() as db:
        row = db.execute("SELECT * FROM generation_jobs WHERE id = ?", (job_id,)).fetchone()
    if row is None:
        return None
    result = dict(row)
    result["result"] = json.loads(result.pop("result_json") or "{}")
    return result


def list_generations(*, status: Optional[str] = None, owner_id: Optional[str] = None,
                     tenant_id: Optional[str] = None, include_all: bool = False,
                     offset: int = 0,
                     limit: int = 20) -> tuple[list[dict[str, Any]], int]:
    clauses: list[str] = []
    parameters: list[Any] = []
    if status:
        clauses.append("generation_jobs.status = ?")
        parameters.append(status)
    if not include_all and owner_id:
        clauses.append("generation_jobs.owner_id = ?")
        parameters.append(owner_id)
    if tenant_id:
        clauses.append("(generation_jobs.tenant_id = ? OR generation_jobs.tenant_id IS NULL)")
        parameters.append(tenant_id)
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    with connect() as db:
        total = db.execute(
            f"SELECT COUNT(*) AS count FROM generation_jobs{where}", parameters
        ).fetchone()["count"]
        rows = db.execute(
            f"""SELECT generation_jobs.*, import_jobs.filename AS source_filename
                FROM generation_jobs
                JOIN import_jobs ON import_jobs.id = generation_jobs.import_id
                {where}
                ORDER BY generation_jobs.created_at DESC
                LIMIT ? OFFSET ?""",
            (*parameters, limit, offset),
        ).fetchall()
    results = []
    for row in rows:
        item = dict(row)
        item["result"] = json.loads(item.pop("result_json") or "{}")
        results.append(item)
    return results, total


def update_generation(job_id: str, **fields: Any) -> None:
    if not fields:
        return
    allowed = {"status", "processed_rows", "successful_rows", "warning_rows", "failed_rows",
               "current_item", "started_at", "completed_at", "error", "result"}
    values = {key: value for key, value in fields.items() if key in allowed}
    if "result" in values:
        values["result_json"] = json.dumps(values.pop("result"))
    if not values:
        return
    with connect() as db:
        db.execute(
            f"UPDATE generation_jobs SET {', '.join(f'{key} = ?' for key in values)} WHERE id = ?",
            (*values.values(), job_id),
        )
        row = db.execute("SELECT * FROM generation_jobs WHERE id = ?", (job_id,)).fetchone()
        if row is not None:
            _save_generation_event(db, dict(row))


def _event_type(status: str) -> str:
    return {
        "completed": "generation.completed",
        "completed_with_errors": "generation.completed",
        "failed": "generation.failed",
        "abandoned": "generation.abandoned",
        "cancelled": "generation.cancelled",
    }.get(status, "generation.progress")


def _save_generation_event(db: sqlite3.Connection, record: dict[str, Any]) -> None:
    payload = dict(record)
    if "result_json" in payload:
        payload["result"] = json.loads(payload.pop("result_json") or "{}")
    db.execute(
        """INSERT INTO generation_events (job_id, event_type, payload_json, created_at)
           VALUES (?, ?, ?, ?)""",
        (record["id"], _event_type(record["status"]), json.dumps(payload),
         record.get("created_at") or datetime.now(timezone.utc).isoformat()),
    )


def list_generation_events(job_id: str, after_id: int = 0) -> list[dict[str, Any]]:
    with connect() as db:
        rows = db.execute(
            """SELECT id, job_id, event_type, payload_json, created_at
               FROM generation_events WHERE job_id = ? AND id > ? ORDER BY id""",
            (job_id, after_id),
        ).fetchall()
    return [
        {**dict(row), "payload": json.loads(row["payload_json"])}
        for row in rows
    ]


def save_generation_result(record: dict[str, Any]) -> None:
    with connect() as db:
                db.execute("""INSERT INTO generation_results
            (id, job_id, row_number, case_id, status, artifact_path, artifact_name,
             content, warnings_json, error, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(job_id, row_number) DO UPDATE SET
                            id=excluded.id,
                            status=excluded.status, artifact_path=excluded.artifact_path,
                            artifact_name=excluded.artifact_name, content=excluded.content,
                            warnings_json=excluded.warnings_json, error=excluded.error""",
            (record["id"], record["job_id"], record["row_number"], record.get("case_id"),
             record["status"], record.get("artifact_path"), record.get("artifact_name"),
             record.get("content"), json.dumps(record.get("warnings", [])), record.get("error"),
             record["created_at"]))


def get_generation_results(job_id: str) -> list[dict[str, Any]]:
    with connect() as db:
        rows = db.execute("SELECT * FROM generation_results WHERE job_id = ? ORDER BY row_number", (job_id,)).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["warnings"] = json.loads(item.pop("warnings_json") or "[]")
        result.append(item)
    return result


def get_generation_result(job_id: str, result_id: str) -> Optional[dict[str, Any]]:
    with connect() as db:
        row = db.execute(
            "SELECT * FROM generation_results WHERE job_id = ? AND id = ?",
            (job_id, result_id),
        ).fetchone()
    if row is None:
        return None
    item = dict(row)
    item["warnings"] = json.loads(item.pop("warnings_json") or "[]")
    return item


def reset_generation_result(job_id: str, result_id: str) -> bool:
    with connect() as db:
        cursor = db.execute(
            """UPDATE generation_results SET status = 'pending',
               artifact_path = NULL, artifact_name = NULL, content = NULL,
               warnings_json = '[]', error = NULL
               WHERE job_id = ? AND id = ?""",
            (job_id, result_id),
        )
        return cursor.rowcount == 1


def reset_generation_results(job_id: str) -> None:
    with connect() as db:
        db.execute("""UPDATE generation_results SET status = 'pending',
            artifact_path = NULL, artifact_name = NULL, content = NULL,
            warnings_json = '[]', error = NULL WHERE job_id = ?""", (job_id,))


def cleanup_retention(*, now: datetime | None = None) -> dict[str, int]:
    """Remove only stale, safe-to-remove files from local durable storage.

    This intentionally does not delete database rows.  Imports referenced by
    any generation job and artifacts referenced by protected jobs are retained;
    this makes cleanup idempotent and keeps job history/API responses usable.
    Active jobs and recently abandoned jobs remain protected for recovery.
    """
    now = now or datetime.now(timezone.utc)
    artifact_root = Path(os.getenv("NORMA_ARTIFACT_DIR", ".runtime/artifacts"))
    import_root = Path(os.getenv("NORMA_IMPORT_DIR", ".runtime/imports"))
    artifact_cutoff = now.timestamp() - _retention_setting("NORMA_ARTIFACT_RETENTION_DAYS", 30) * 86400
    import_cutoff = now.timestamp() - _retention_setting("NORMA_IMPORT_RETENTION_DAYS", 30) * 86400
    recover_timeout = _retention_setting("NORMA_GENERATION_ABANDON_TIMEOUT_SECONDS", 3600)
    active_statuses = {"queued", "running", "cancelling"}
    terminal_statuses = {"completed", "completed_with_errors", "failed", "cancelled", "abandoned"}
    deleted_artifacts = 0
    deleted_imports = 0
    skipped_protected = 0

    with connect() as db:
        jobs = [dict(row) for row in db.execute(
            "SELECT id, import_id, status, created_at, started_at FROM generation_jobs"
        ).fetchall()]
        protected_ids = set()
        for job in jobs:
            age_reference = _parse_timestamp(job.get("started_at") or job.get("created_at"))
            age = (now - age_reference).total_seconds() if age_reference else 0
            if job["status"] in active_statuses or (
                job["status"] == "abandoned" and age <= recover_timeout
            ):
                protected_ids.add(job["id"])

        # Remove stale artifact files belonging to old terminal jobs.  Keep
        # content in SQLite so historical downloads remain backwards compatible.
        rows = db.execute(
            """SELECT r.id, r.artifact_path, j.id AS job_id, j.status, j.created_at
               FROM generation_results r JOIN generation_jobs j ON j.id = r.job_id
               WHERE r.artifact_path IS NOT NULL"""
        ).fetchall()
        referenced_artifacts = {
            str(row["artifact_path"]) for row in rows if row["artifact_path"]
        }
        for row in rows:
            path = Path(row["artifact_path"])
            if row["job_id"] in protected_ids:
                skipped_protected += 1
                continue
            # A result is a durable reference, regardless of job age.  Its
            # file can only be removed after a separate lifecycle operation
            # clears the reference.
            if str(path) in referenced_artifacts:
                continue
            created = _parse_timestamp(row["created_at"])
            if row["status"] not in terminal_statuses or not created or created.timestamp() > artifact_cutoff:
                continue
            if _is_within_root(path, artifact_root) and path.is_file():
                try:
                    path.unlink()
                    deleted_artifacts += 1
                    db.execute("UPDATE generation_results SET artifact_path = NULL WHERE id = ?", (row["id"],))
                except OSError:
                    continue

        # Imports are retained while referenced by any job.  Only orphaned
        # uploads are eligible, preventing a stale history entry from breaking.
        referenced_imports = {job["import_id"] for job in jobs}
        imports = db.execute(
            "SELECT id, storage_path, created_at FROM import_jobs"
        ).fetchall()
        for row in imports:
            if row["id"] in referenced_imports:
                continue
            created = _parse_timestamp(row["created_at"])
            path = Path(row["storage_path"])
            if not created or created.timestamp() > import_cutoff:
                continue
            if _is_within_root(path, import_root) and path.is_file():
                try:
                    path.unlink()
                    deleted_imports += 1
                except OSError:
                    continue

        # Clean orphan files left by a crash between writing the file and
        # inserting its database record.  Never recurse or remove directories.
        if artifact_root.is_dir():
            for path in artifact_root.rglob("*"):
                if not path.is_file() or str(path) in referenced_artifacts:
                    continue
                try:
                    if path.stat().st_mtime <= artifact_cutoff:
                        path.unlink()
                        deleted_artifacts += 1
                except OSError:
                    continue
        referenced_import_paths = {str(row["storage_path"]) for row in imports}
        if import_root.is_dir():
            for path in import_root.rglob("*"):
                if not path.is_file() or str(path) in referenced_import_paths:
                    continue
                try:
                    if path.stat().st_mtime <= import_cutoff:
                        path.unlink()
                        deleted_imports += 1
                except OSError:
                    continue

    report = {
        "deleted_artifacts": deleted_artifacts,
        "deleted_imports": deleted_imports,
        "skipped_protected": skipped_protected,
    }
    metrics_registry.record_retention_cleanup(report)
    return report
