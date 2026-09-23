from pathlib import Path

from antinode_norma.evaluate.cost import CostTracker


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_cost_model_documents_tracker_formula_cache_and_gate() -> None:
    document = (REPOSITORY_ROOT / "docs" / "COST.md").read_text(encoding="utf-8")

    assert "Token & Cost Baseline" in document
    assert "Cache Hit Run" in document
    assert "build/llm_cost.jsonl" in document
    assert "cost_per_run > $0.02" in document

    tracker = CostTracker()
    assert tracker.calculate_cost(2_000, 1_500) == 0.0012
    assert tracker.check_cost_gate(0.02)[0] is True
    assert tracker.check_cost_gate(0.02001)[0] is False
