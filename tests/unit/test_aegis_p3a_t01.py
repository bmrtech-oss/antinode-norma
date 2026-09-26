import pytest

from antinode_norma.core.types import GateResult
from antinode_norma.gates.aggregate import aggregate_results
from antinode_norma.gates.norma_validator import Q0NormaValidatorGate
from antinode_norma.gates.runner import GateRunner
from antinode_norma.gates.types import GateContext


VALID_GHERKIN = """Feature: Login
  Scenario: Successful login
    Given the user is on the login page
    When they enter valid credentials
    Then they see the dashboard
"""


def test_q0_is_a_hard_gate_and_reports_empty_input() -> None:
    result = Q0NormaValidatorGate().evaluate(GateContext(gherkin_text=""))

    assert result.gate_id == "Q0"
    assert result.passed is False
    assert result.score == 0.0
    assert result.issues == ["Gherkin feature text is empty"]


def test_aggregator_requires_hard_pass_and_thresholded_soft_score() -> None:
    passing = aggregate_results(
        [
            GateResult(gate_id="Q0", passed=True),
            GateResult(gate_id="Q6", passed=True, score=0.90),
            GateResult(gate_id="Q7", passed=True, score=0.80),
        ]
    )
    failing = aggregate_results(
        [
            GateResult(gate_id="Q0", passed=True),
            GateResult(gate_id="Q6", passed=True, score=0.84),
            GateResult(gate_id="Q7", passed=True, score=0.86),
        ]
    )

    assert passing.hard_pass is True
    assert passing.soft_score == pytest.approx(0.85)
    assert passing.is_overall_pass is True
    assert failing.soft_score == pytest.approx(0.85)
    assert failing.is_overall_pass is True


def test_aggregator_fails_when_any_hard_gate_fails() -> None:
    verdict = aggregate_results(
        [
            GateResult(gate_id="Q0", passed=False, score=0.0),
            GateResult(gate_id="Q1", passed=True),
        ]
    )

    assert verdict.hard_pass is False
    assert verdict.is_overall_pass is False


def test_gate_runner_registers_q0_before_the_remaining_gate_chain() -> None:
    runner = GateRunner()

    assert [gate.gate_id for gate in runner.gates] == [
        "Q0",
        "Q1",
        "Q2",
        "Q3",
        "Q4",
        "Q5",
        "Q6",
        "Q7",
        "Q8",
        "Q9",
        "Q10",
    ]
    assert runner.gates[0].is_hard_gate is True
    assert Q0NormaValidatorGate().evaluate(
        GateContext(gherkin_text=VALID_GHERKIN)
    ).passed is True
