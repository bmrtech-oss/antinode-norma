from antinode_norma.evaluate.cost import CostTracker


def test_cost_calculation():
    tracker = CostTracker()
    # 2,000 input tokens = 0.002 * 0.15 = 0.0003 USD
    # 1,500 output tokens = 0.0015 * 0.60 = 0.0009 USD
    # Total = 0.0012 USD
    cost = tracker.calculate_cost(2000, 1500)
    assert abs(cost - 0.0012) < 1e-6


def test_cost_logging_and_total(tmp_path):
    log_file = tmp_path / "llm_cost.jsonl"
    tracker = CostTracker(log_path=log_file)

    cost1 = tracker.log_call("prompt 1", "completion 1", 2000, 1500)
    cost2 = tracker.log_call("prompt 2", "completion 2", 1000, 500)

    assert log_file.exists()
    lines = log_file.read_text().splitlines()
    assert len(lines) == 2

    total = tracker.get_total_cost()
    assert abs(total - (cost1 + cost2)) < 1e-6


def test_cost_gate_check():
    tracker = CostTracker()

    # Under $0.02 threshold passes
    passed, msg = tracker.check_cost_gate(0.003, threshold=0.02)
    assert passed is True
    assert "within limit" in msg

    # Exceeding $0.02 threshold fails
    passed, msg = tracker.check_cost_gate(0.025, threshold=0.02)
    assert passed is False
    assert "exceeds maximum threshold" in msg
