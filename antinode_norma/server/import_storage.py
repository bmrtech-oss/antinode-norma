"""Small SQLite persistence layer for structured import and generation jobs."""

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def database_path() -> Path:
    path = Path(os.getenv("NORMA_IMPORT_DB", ".runtime/import_jobs.sqlite3"))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(database_path(), timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """CREATE TABLE IF NOT EXISTS import_jobs (
            id TEXT PRIMARY KEY, filename TEXT NOT NULL, format TEXT NOT NULL,
            storage_path TEXT NOT NULL, status TEXT NOT NULL, row_count INTEGER NOT NULL,
            rows_json TEXT NOT NULL, created_at TEXT NOT NULL,
            columns_json TEXT NOT NULL DEFAULT '[]',
            worksheet_names_json TEXT NOT NULL DEFAULT '[]',
            worksheet TEXT, mapping_json TEXT NOT NULL DEFAULT '{}'
        )"""
    )
    connection.execute("""CREATE TABLE IF NOT EXISTS generation_jobs (
        id TEXT PRIMARY KEY, import_id TEXT NOT NULL, status TEXT NOT NULL,
        result_json TEXT NOT NULL, created_at TEXT NOT NULL,
        total_rows INTEGER NOT NULL DEFAULT 0, processed_rows INTEGER NOT NULL DEFAULT 0,
        successful_rows INTEGER NOT NULL DEFAULT 0, warning_rows INTEGER NOT NULL DEFAULT 0,
        failed_rows INTEGER NOT NULL DEFAULT 0, current_item TEXT,
        started_at TEXT, completed_at TEXT, error TEXT,
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
    connection.execute("""CREATE TABLE IF NOT EXISTS generation_results (
        id TEXT PRIMARY KEY, job_id TEXT NOT NULL, row_number INTEGER NOT NULL,
        case_id TEXT, status TEXT NOT NULL, artifact_path TEXT, artifact_name TEXT,
        content TEXT, warnings_json TEXT NOT NULL DEFAULT '[]', error TEXT,
        created_at TEXT NOT NULL, UNIQUE(job_id, row_number),
        FOREIGN KEY(job_id) REFERENCES generation_jobs(id)
    )""")
    connection.commit()
    return connection


def save_import(record: dict[str, Any]) -> None:
    with connect() as db:
        db.execute(
            """INSERT INTO import_jobs
            (id, filename, format, storage_path, status, row_count, rows_json, created_at,
             columns_json, worksheet_names_json, worksheet, mapping_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (record["id"], record["filename"], record["format"], record["storage_path"],
             record["status"], record["row_count"], json.dumps(record["rows"]), record["created_at"],
             json.dumps(record.get("columns", [])), json.dumps(record.get("worksheet_names", [])),
             record.get("worksheet"), json.dumps(record.get("mapping", {}))),
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
             successful_rows, warning_rows, failed_rows, current_item, started_at, completed_at, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (record["id"], record["import_id"], record["status"], json.dumps(record.get("result", {})),
             record["created_at"], record.get("total_rows", 0), record.get("processed_rows", 0),
             record.get("successful_rows", 0), record.get("warning_rows", 0), record.get("failed_rows", 0),
             record.get("current_item"), record.get("started_at"), record.get("completed_at"), record.get("error")),
        )


def get_generation(job_id: str) -> Optional[dict[str, Any]]:
    with connect() as db:
        row = db.execute("SELECT * FROM generation_jobs WHERE id = ?", (job_id,)).fetchone()
    if row is None:
        return None
    result = dict(row)
    result["result"] = json.loads(result.pop("result_json") or "{}")
    return result


def list_generations(*, status: Optional[str] = None, offset: int = 0,
                     limit: int = 20) -> tuple[list[dict[str, Any]], int]:
    clauses: list[str] = []
    parameters: list[Any] = []
    if status:
        clauses.append("generation_jobs.status = ?")
        parameters.append(status)
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


def save_generation_result(record: dict[str, Any]) -> None:
    with connect() as db:
        db.execute("""INSERT OR REPLACE INTO generation_results
            (id, job_id, row_number, case_id, status, artifact_path, artifact_name,
             content, warnings_json, error, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
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
