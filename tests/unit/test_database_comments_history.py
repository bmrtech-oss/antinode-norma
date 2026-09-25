from antinode_norma.collaboration.comments import CommentStore
from antinode_norma.database import migrate
from antinode_norma.execution.history import ExecutionHistoryRecord, ExecutionHistoryStore


def test_database_backed_comments_and_history_survive_reload(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'app.db'}"
    migrate(database_url)
    comments = CommentStore(database_url=database_url)
    comments.add_comment("FEATURE-1", "reviewer", "Please review @admin")
    history = ExecutionHistoryStore(database_url=database_url)
    history.save_run(ExecutionHistoryRecord(id="RUN-1", status="PASSED", total_scenarios=1, passed_scenarios=1))

    reloaded_comments = CommentStore(database_url=database_url)
    reloaded_history = ExecutionHistoryStore(database_url=database_url)

    assert reloaded_comments.get_comments("FEATURE-1")[0].mentions == ["admin"]
    assert reloaded_history.get_history()[0].id == "RUN-1"
