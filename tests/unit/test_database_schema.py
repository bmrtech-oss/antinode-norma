import sqlite3

from antinode_norma.database import migrate


def test_shared_schema_includes_application_job_tables(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'schema.db'}"
    migrate(database_url)
    connection = sqlite3.connect(tmp_path / "schema.db")
    try:
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    finally:
        connection.close()

    assert {
        "norma_seed_records",
        "tenants",
        "users",
        "user_roles",
        "audit_events",
        "approval_requests",
        "comments",
        "execution_history",
        "llm_cost_events",
        "import_jobs",
        "generation_jobs",
        "generation_results",
        "generation_events",
        "feedback",
        "selector_stats",
        "failure_events",
    } <= tables
