from pathlib import Path
from typing import List, Dict, Any
from antinode_norma.core.types import TestCase
from antinode_norma.core.agent import NormaAgent


class EvalHarness:
    """
    Evaluation Harness.
    Measures BDD agent quality metrics across evaluation runs against golden datasets.
    Metrics measured:
    - pass_rate: Ratio of evaluation runs passing all hard quality gates
    - first_attempt_syntax_rate: Ratio of runs passing syntax checks on attempt 1
    - avg_attempts: Average number of attempts per run
    - determinism_score: Consistency score across multiple runs
    """

    def __init__(self, golden_dir: Path = Path("tests/eval/golden")):
        self.golden_dir = golden_dir

    def evaluate_agent(
        self,
        agent: NormaAgent,
        test_cases: List[TestCase],
        iterations: int = 1,
    ) -> Dict[str, Any]:
        """
        Run agent evaluation over N iterations and return aggregated metrics.
        """
        passes = 0
        first_attempt_syntax_passes = 0
        total_attempts = 0
        generated_features = []

        for _ in range(iterations):
            gherkin_text, verdict, attempts = agent.generate_feature_with_repair(test_cases)
            generated_features.append(gherkin_text)
            total_attempts += attempts

            if verdict.hard_pass:
                passes += 1

            if attempts == 1 and verdict.gate_results.get("Q1", None) and verdict.gate_results["Q1"].passed:
                first_attempt_syntax_passes += 1

        pass_rate = passes / iterations if iterations > 0 else 0.0
        first_attempt_syntax_rate = (
            first_attempt_syntax_passes / iterations if iterations > 0 else 0.0
        )
        avg_attempts = total_attempts / iterations if iterations > 0 else 0.0

        # Determinism score: ratio of identical generated outputs
        unique_outputs = len(set(generated_features))
        determinism_score = 1.0 if iterations <= 1 else (iterations - unique_outputs + 1) / iterations

        return {
            "iterations": iterations,
            "pass_rate": pass_rate,
            "first_attempt_syntax_rate": first_attempt_syntax_rate,
            "avg_attempts": avg_attempts,
            "determinism_score": max(0.0, determinism_score),
            "meets_thresholds": pass_rate >= 0.95 and avg_attempts <= 1.5,
        }
