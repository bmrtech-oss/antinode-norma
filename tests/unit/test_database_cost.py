from antinode_norma.database import migrate
from antinode_norma.evaluate.cost import CostTracker


def test_database_backed_cost_tracker(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'app.db'}"
    migrate(database_url)
    tracker = CostTracker(database_url=database_url, model="test-model")

    first = tracker.log_call("prompt", "completion", 1000, 500)
    second = tracker.log_call("prompt2", "completion2", 2000, 1000)

    assert abs(tracker.get_total_cost() - (first + second)) < 1e-9
