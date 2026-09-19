from pathlib import Path
from antinode_norma.core.types import TestCase
from antinode_norma.core.agent import NormaAgent
from antinode_norma.evaluate.harness import EvalHarness


def test_eval_harness_metrics_pass():
    def mock_llm(prompt: str) -> str:
        return """
@TC-101
Feature: Account Details
  Scenario: View account details
    Given user is logged in
"""

    tc = TestCase(id="TC-101", title="View account details")
    agent = NormaAgent(llm_callable=mock_llm)

    harness = EvalHarness(golden_dir=Path("tests/eval/golden"))
    metrics = harness.evaluate_agent(agent, [tc], iterations=2)

    assert metrics["iterations"] == 2
    assert metrics["pass_rate"] == 1.0
    assert metrics["first_attempt_syntax_rate"] == 1.0
    assert metrics["avg_attempts"] == 1.0
    assert metrics["determinism_score"] == 1.0
    assert metrics["meets_thresholds"] is True


def test_eval_harness_golden_file_exists():
    golden = Path("tests/eval/golden/account_details.feature")
    assert golden.exists()
    content = golden.read_text()
    assert "Feature: Account Details Management" in content
    assert "@TC-101" in content
