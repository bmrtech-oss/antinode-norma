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
