"""Minimal SQLite/PostgreSQL migration and local seed persistence."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

SCHEMA = """
CREATE TABLE IF NOT EXISTS norma_seed_records (
    kind TEXT NOT NULL,
    record_id TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (kind, record_id)
);
CREATE TABLE IF NOT EXISTS audit_events (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    action TEXT NOT NULL,
    resource TEXT NOT NULL,
    actor TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    previous_hash TEXT NOT NULL,
    content_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS approval_requests (
    id TEXT PRIMARY KEY,
    feature_id TEXT NOT NULL,
    gherkin_text TEXT NOT NULL,
    status TEXT NOT NULL,
    requested_by TEXT NOT NULL,
    reviewer TEXT,
    reason TEXT,
    owner_id TEXT,
    tenant_id TEXT,
    source_job_id TEXT,
    source_result_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS comments (
    id TEXT PRIMARY KEY,
    feature_id TEXT NOT NULL,
    author_id TEXT NOT NULL,
    text TEXT NOT NULL,
    mentions_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS execution_history (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    duration_seconds REAL NOT NULL,
    status TEXT NOT NULL,
    total_scenarios INTEGER NOT NULL,
    passed_scenarios INTEGER NOT NULL,
    failed_scenarios INTEGER NOT NULL,
    skipped_scenarios INTEGER NOT NULL,
    metadata_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS llm_cost_events (
    id TEXT PRIMARY KEY,
    timestamp REAL NOT NULL,
    model TEXT NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cost_usd REAL NOT NULL,
    prompt_length INTEGER NOT NULL,
    completion_length INTEGER NOT NULL,
    metadata_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tenants (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    environment TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY(tenant_id) REFERENCES tenants(id)
);
CREATE TABLE IF NOT EXISTS user_roles (
    user_id TEXT NOT NULL,
    role TEXT NOT NULL,
    PRIMARY KEY(user_id, role),
    FOREIGN KEY(user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS import_jobs (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    format TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    status TEXT NOT NULL,
    row_count INTEGER NOT NULL,
    rows_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    columns_json TEXT NOT NULL DEFAULT '[]',
    worksheet_names_json TEXT NOT NULL DEFAULT '[]',
    worksheet TEXT,
    mapping_json TEXT NOT NULL DEFAULT '{}',
    owner_id TEXT,
    tenant_id TEXT
);
CREATE TABLE IF NOT EXISTS generation_jobs (
    id TEXT PRIMARY KEY,
    import_id TEXT NOT NULL,
    status TEXT NOT NULL,
    result_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    total_rows INTEGER NOT NULL DEFAULT 0,
    processed_rows INTEGER NOT NULL DEFAULT 0,
    successful_rows INTEGER NOT NULL DEFAULT 0,
    warning_rows INTEGER NOT NULL DEFAULT 0,
    failed_rows INTEGER NOT NULL DEFAULT 0,
    current_item TEXT,
    started_at TEXT,
    completed_at TEXT,
    error TEXT,
    owner_id TEXT,
    tenant_id TEXT
);
CREATE TABLE IF NOT EXISTS generation_results (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    row_number INTEGER NOT NULL,
    case_id TEXT,
    status TEXT NOT NULL,
    artifact_path TEXT,
    artifact_name TEXT,
    content TEXT,
    warnings_json TEXT NOT NULL DEFAULT '[]',
    error TEXT,
    created_at TEXT NOT NULL,
    owner_id TEXT,
    tenant_id TEXT,
    UNIQUE(job_id, row_number)
);
CREATE TABLE IF NOT EXISTS generation_events (
    id INTEGER PRIMARY KEY,
    job_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY,
    mapping_id TEXT UNIQUE,
    step_text TEXT,
    action_type TEXT,
    selector TEXT,
    test_result TEXT,
    execution_context TEXT,
    mapping_source TEXT DEFAULT 'unknown',
    confidence REAL DEFAULT 0.0,
    timestamp TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS selector_stats (
    id INTEGER PRIMARY KEY,
    selector TEXT UNIQUE,
    action_type TEXT,
    pass_count INTEGER DEFAULT 0,
    fail_count INTEGER DEFAULT 0,
    skip_count INTEGER DEFAULT 0,
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_feedback_step_text ON feedback(step_text);
CREATE INDEX IF NOT EXISTS idx_feedback_selector ON feedback(selector);
CREATE INDEX IF NOT EXISTS idx_feedback_test_result ON feedback(test_result)
;
CREATE TABLE IF NOT EXISTS failure_events (
    id INTEGER PRIMARY KEY,
    step_text TEXT,
    test_title TEXT NOT NULL,
    file_path TEXT,
    line INTEGER,
    selector TEXT,
    error_message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""


def _database_url(database_url: str | None = None) -> str:
    return database_url or os.getenv("DATABASE_URL", "sqlite:///.runtime/norma.db")


def _connect(database_url: str | None = None):
    url = _database_url(database_url)
    if url.startswith("sqlite:///"):
        path = Path(url.removeprefix("sqlite:///"))
        path.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(path), "sqlite"
    if url.startswith(("postgresql://", "postgres://")):
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError("PostgreSQL support requires the psycopg package") from exc
        return psycopg.connect(url), "postgres"
    raise ValueError("DATABASE_URL must use sqlite:/// or postgresql://")


def migrate(database_url: str | None = None) -> None:
    connection, backend = _connect(database_url)
    try:
        _apply_schema(connection, backend)
        connection.commit()
    finally:
        connection.close()


def _apply_schema(connection: Any, backend: str) -> None:
    if backend == "sqlite":
        connection.executescript(SCHEMA)
    else:
        for statement in SCHEMA.split(";"):
            if statement.strip():
                connection.execute(statement)


def execute(database_url: str, statement: str, parameters: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
    connection, _ = _connect(database_url)
    try:
        cursor = connection.execute(statement, parameters)
        rows = cursor.fetchall() if cursor.description else []
        connection.commit()
        return rows
    finally:
        connection.close()


def save_audit_event(database_url: str, event: dict[str, Any]) -> None:
    connection, backend = _connect(database_url)
    try:
        placeholders = "%s" if backend == "postgres" else "?"
        connection.execute(
            "INSERT INTO audit_events(id, timestamp, action, resource, actor, payload_json, previous_hash, content_hash) "
            f"VALUES ({placeholders}, {placeholders}, {placeholders}, {placeholders}, {placeholders}, {placeholders}, {placeholders}, {placeholders})",
            (
                event["id"], event["timestamp"], event["action"], event["resource"],
                event["actor"], json.dumps(event["payload"], sort_keys=True),
                event["previous_hash"], event["content_hash"],
            ),
        )
        connection.commit()
    finally:
        connection.close()


def load_audit_events(database_url: str) -> list[dict[str, Any]]:
    rows = execute(database_url, "SELECT id, timestamp, action, resource, actor, payload_json, previous_hash, content_hash FROM audit_events ORDER BY timestamp, id")
    return [
        {
            "id": row[0], "timestamp": row[1], "action": row[2], "resource": row[3],
            "actor": row[4], "payload": json.loads(row[5]), "previous_hash": row[6],
            "content_hash": row[7],
        }
        for row in rows
    ]


def save_approval_request(database_url: str, request: dict[str, Any]) -> None:
    connection, backend = _connect(database_url)
    try:
        placeholder = "%s" if backend == "postgres" else "?"
        values = (
            request["id"], request["feature_id"], request["gherkin_text"], request["status"],
            request["requested_by"], request.get("reviewer"), request.get("reason"),
            request.get("owner_id"), request.get("tenant_id"), request.get("source_job_id"),
            request.get("source_result_id"), request["created_at"], request["updated_at"],
        )
        connection.execute(
            "INSERT INTO approval_requests(id, feature_id, gherkin_text, status, requested_by, reviewer, reason, owner_id, tenant_id, source_job_id, source_result_id, created_at, updated_at) "
            f"VALUES ({', '.join([placeholder] * 13)}) ON CONFLICT(id) DO UPDATE SET status=excluded.status, reviewer=excluded.reviewer, reason=excluded.reason, updated_at=excluded.updated_at",
            values,
        )
        connection.commit()
    finally:
        connection.close()


def load_approval_requests(database_url: str) -> list[dict[str, Any]]:
    rows = execute(database_url, "SELECT id, feature_id, gherkin_text, status, requested_by, reviewer, reason, owner_id, tenant_id, source_job_id, source_result_id, created_at, updated_at FROM approval_requests ORDER BY created_at, id")
    fields = ("id", "feature_id", "gherkin_text", "status", "requested_by", "reviewer", "reason", "owner_id", "tenant_id", "source_job_id", "source_result_id", "created_at", "updated_at")
    return [dict(zip(fields, row)) for row in rows]


def save_comment(database_url: str, comment: dict[str, Any]) -> None:
    connection, backend = _connect(database_url)
    try:
        placeholder = "%s" if backend == "postgres" else "?"
        connection.execute(
            "INSERT INTO comments(id, feature_id, author_id, text, mentions_json, created_at) "
            f"VALUES ({', '.join([placeholder] * 6)})",
            (
                comment["id"], comment["feature_id"], comment["author_id"], comment["text"],
                json.dumps(comment["mentions"], sort_keys=True), comment["created_at"],
            ),
        )
        connection.commit()
    finally:
        connection.close()


def load_comments(database_url: str, feature_id: str | None = None) -> list[dict[str, Any]]:
    if feature_id:
        rows = execute(database_url, "SELECT id, feature_id, author_id, text, mentions_json, created_at FROM comments WHERE feature_id = %s" if database_url.startswith(("postgres://", "postgresql://")) else "SELECT id, feature_id, author_id, text, mentions_json, created_at FROM comments WHERE feature_id = ?", (feature_id,))
    else:
        rows = execute(database_url, "SELECT id, feature_id, author_id, text, mentions_json, created_at FROM comments ORDER BY created_at, id")
    fields = ("id", "feature_id", "author_id", "text", "mentions", "created_at")
    return [dict(zip(fields, (*row[:4], json.loads(row[4]), row[5]))) for row in rows]


def save_execution_history(database_url: str, record: dict[str, Any]) -> None:
    connection, backend = _connect(database_url)
    try:
        placeholder = "%s" if backend == "postgres" else "?"
        connection.execute(
            "INSERT INTO execution_history(id, timestamp, duration_seconds, status, total_scenarios, passed_scenarios, failed_scenarios, skipped_scenarios, metadata_json) "
            f"VALUES ({', '.join([placeholder] * 9)}) ON CONFLICT(id) DO UPDATE SET status=excluded.status, metadata_json=excluded.metadata_json",
            (
                record["id"], record["timestamp"], record["duration_seconds"], record["status"],
                record["total_scenarios"], record["passed_scenarios"], record["failed_scenarios"],
                record["skipped_scenarios"], json.dumps(record["metadata"], sort_keys=True),
            ),
        )
        connection.commit()
    finally:
        connection.close()


def load_execution_history(database_url: str) -> list[dict[str, Any]]:
    rows = execute(database_url, "SELECT id, timestamp, duration_seconds, status, total_scenarios, passed_scenarios, failed_scenarios, skipped_scenarios, metadata_json FROM execution_history ORDER BY timestamp, id")
    return [
        {
            "id": row[0], "timestamp": row[1], "duration_seconds": row[2], "status": row[3],
            "total_scenarios": row[4], "passed_scenarios": row[5], "failed_scenarios": row[6],
            "skipped_scenarios": row[7], "metadata": json.loads(row[8]),
        }
        for row in rows
    ]


def save_cost_event(database_url: str, event: dict[str, Any]) -> None:
    connection, backend = _connect(database_url)
    try:
        placeholder = "%s" if backend == "postgres" else "?"
        connection.execute(
            "INSERT INTO llm_cost_events(id, timestamp, model, input_tokens, output_tokens, cost_usd, prompt_length, completion_length, metadata_json) "
            f"VALUES ({', '.join([placeholder] * 9)})",
            (
                event["id"], event["timestamp"], event["model"], event["input_tokens"],
                event["output_tokens"], event["cost_usd"], event["prompt_length"],
                event["completion_length"], json.dumps(event["metadata"], sort_keys=True),
            ),
        )
        connection.commit()
    finally:
        connection.close()


def total_cost(database_url: str) -> float:
    rows = execute(database_url, "SELECT COALESCE(SUM(cost_usd), 0) FROM llm_cost_events")
    return float(rows[0][0]) if rows else 0.0


def upsert_seed_records(records: Iterator[tuple[str, str, Any]], database_url: str | None = None) -> int:
    connection, backend = _connect(database_url)
    try:
        _apply_schema(connection, backend)
        now = datetime.now(timezone.utc).isoformat()
        count = 0
        for kind, record_id, payload in records:
            if backend == "sqlite":
                connection.execute(
                    "INSERT INTO norma_seed_records(kind, record_id, payload_json, updated_at) "
                    "VALUES (?, ?, ?, ?) ON CONFLICT(kind, record_id) DO UPDATE SET "
                    "payload_json=excluded.payload_json, updated_at=excluded.updated_at",
                    (kind, record_id, json.dumps(payload, sort_keys=True), now),
                )
            else:
                connection.execute(
                    "INSERT INTO norma_seed_records(kind, record_id, payload_json, updated_at) "
                    "VALUES (%s, %s, %s, %s) ON CONFLICT(kind, record_id) DO UPDATE SET "
                    "payload_json=EXCLUDED.payload_json, updated_at=EXCLUDED.updated_at",
                    (kind, record_id, json.dumps(payload, sort_keys=True), now),
                )
            count += 1
        connection.commit()
        return count
    finally:
        connection.close()


def seed_database(seed_root: Path, database_url: str | None = None) -> int:
    records: list[tuple[str, str, Any]] = []
    for filename, kind in (("users.json", "user"), ("approvals.json", "approval")):
        entries = json.loads((seed_root / filename).read_text(encoding="utf-8"))
        records.extend((kind, str(item["id"]), item) for item in entries)
    return upsert_seed_records(iter(records), database_url)


def seed_auth_users(database_url: str, tenant_id: str = "seed-tenant") -> int:
    users = [
        ("seed-admin", "admin", "admin@local.test", "admin"),
        ("seed-reviewer", "reviewer", "reviewer@local.test", "reviewer"),
        ("seed-generator", "generator", "generator@local.test", "generator"),
        ("seed-viewer", "viewer", "viewer@local.test", "viewer"),
    ]
    connection, backend = _connect(database_url)
    try:
        _apply_schema(connection, backend)
        placeholder = "%s" if backend == "postgres" else "?"
        upsert = (
            "INSERT INTO tenants(id, name, environment) VALUES ({0}, {0}, {0}) "
            "ON CONFLICT(id) DO UPDATE SET name=EXCLUDED.name, environment=EXCLUDED.environment"
        ).format(placeholder)
        connection.execute(upsert, (tenant_id, "Local Test Tenant", "local"))
        for user_id, username, email, role in users:
            connection.execute(
                "INSERT INTO users(id, tenant_id, username, email, is_active) VALUES (" + ", ".join([placeholder] * 5) + ") "
                "ON CONFLICT(id) DO UPDATE SET tenant_id=excluded.tenant_id, email=excluded.email, is_active=excluded.is_active",
                (user_id, tenant_id, username, email, 1),
            )
            connection.execute(
                "INSERT INTO user_roles(user_id, role) VALUES (" + ", ".join([placeholder] * 2) + ") ON CONFLICT(user_id, role) DO NOTHING",
                (user_id, role),
            )
        connection.commit()
        return len(users)
    finally:
        connection.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["migrate"])
    parser.add_argument("--database-url", default=None)
    args = parser.parse_args()
    migrate(args.database_url)
    print("database migration complete")