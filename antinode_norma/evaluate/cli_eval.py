import sys
from pathlib import Path
from antinode_norma.core.types import TestCase
from antinode_norma.core.agent import NormaAgent
from antinode_norma.evaluate.harness import EvalHarness
from antinode_norma.evaluate.cost import CostTracker


def mock_llm(prompt: str) -> str:
    return """
@TC-101 @TC-102
Feature: Account Details Management
  Scenario: View account details
    Given the user is logged in
"""


def run_eval_ci() -> int:
    """
    Run evaluation harness and check cost gate for CI validation.
    Returns 0 on success, 1 on failure.
    """
    print("=== Running Evaluation CI Job ===")
    test_cases = [
        TestCase(id="TC-101", title="View account details"),
        TestCase(id="TC-102", title="Update contact email address"),
    ]

    agent = NormaAgent(llm_callable=mock_llm)
    harness = EvalHarness(golden_dir=Path("tests/eval/golden"))
    metrics = harness.evaluate_agent(agent, test_cases, iterations=1)

    tracker = CostTracker()
    # Log simulated token usage for gpt-4o-mini
    call_cost = tracker.log_call(
        prompt="Simulated prompt text",
        completion="Simulated completion text",
        input_tokens=2000,
        output_tokens=1500,
    )

    cost_passed, cost_msg = tracker.check_cost_gate(call_cost, threshold=0.02)

    print(f"Pass Rate: {metrics['pass_rate']:.2f}")
    print(f"Avg Attempts: {metrics['avg_attempts']:.2f}")
    print(f"Cost Per Run: ${call_cost:.5f}")
    print(f"Cost Gate Status: {cost_msg}")

    if not metrics["meets_thresholds"]:
        print("FAIL: Quality thresholds not met.")
        return 1

    if not cost_passed:
        print("FAIL: Cost gate threshold exceeded.")
        return 1

    print("SUCCESS: Evaluation passed quality and cost gates.")
    return 0


if __name__ == "__main__":
    sys.exit(run_eval_ci())
