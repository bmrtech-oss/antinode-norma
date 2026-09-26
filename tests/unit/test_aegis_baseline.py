from pathlib import Path

from antinode_aegis.baseline import collect_baseline


def test_baseline_contains_revision_runtime_and_test_count() -> None:
    baseline = collect_baseline(Path(__file__).parents[2])

    assert len(baseline["commit_sha"]) == 40
    assert baseline["python_version"]
    assert baseline["collected_test_count"] > 0
    assert baseline["baseline_version"] == 1
