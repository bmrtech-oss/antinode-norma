from antinode_norma.codegen.engine.feedback_store import FeedbackStore
from antinode_norma.database import migrate


def test_feedback_store_database_url_uses_shared_sqlite_database(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'app.db'}"
    migrate(database_url)
    store = FeedbackStore(database_url=database_url)

    store.record_result(
        step_text="Given the user logs in",
        action_type="login",
        selector="#login",
        test_result="pass",
        execution_context={"browser": "chromium"},
    )

    assert store.get_success_rate("#login") == 1.0
