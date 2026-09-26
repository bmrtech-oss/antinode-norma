import json
import sqlite3

from antinode_norma.database import migrate
from antinode_norma.core import failure_analyzer


def test_failure_analyzer_database_schema_is_shared(tmp_path, monkeypatch):
    database_url = f"sqlite:///{tmp_path / 'app.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    migrate(database_url)
    failure_analyzer._ensure_database()

    connection = sqlite3.connect(tmp_path / "app.db")
    try:
        table = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='failure_events'"
        ).fetchone()
    finally:
        connection.close()
    assert table == ("failure_events",)


def test_failure_analyzer_uses_shared_sqlite_database(tmp_path, monkeypatch):
    database_url = f"sqlite:///{tmp_path / 'app.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    migrate(database_url)

    report_path = tmp_path / "report.json"
    report_path.write_text(
        json.dumps(
            {
                "tests": [
                    {
                        "title": "logs in",
                        "location": {"file": "tests/example.feature", "line": 7},
                        "results": [
                            {
                                "status": "failed",
                                "error": {"message": "Unable to find element with selector '#login'"},
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    failure_analyzer.store_playwright_failures(report_path)

    with sqlite3.connect(tmp_path / "app.db") as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM failure_events WHERE selector = ?",
            ("#login",),
        ).fetchone()

    assert row == (1,)
