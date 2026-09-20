from antinode_norma.gates.types import GateContext
from antinode_norma.gates.norma_validator import Q0NormaValidatorGate
from antinode_norma.gates.aggregate import aggregate_results
from antinode_norma.core.types import GateResult


def test_q0_validator_gate_pass():
    gherkin = (
        "Feature: Login\n"
        "  Scenario: Successful login\n"
        "    Given the user is on the login page\n"
        "    When they enter valid credentials\n"
        "    Then they are redirected to dashboard\n"
    )
    ctx = GateContext(gherkin_text=gherkin)
    gate = Q0NormaValidatorGate()
    result = gate.evaluate(ctx)

    assert result.gate_id == "Q0"
    assert result.passed is True
    assert result.score == 1.0
    assert len(result.issues) == 0


def test_q0_validator_gate_fail_empty():
    ctx = GateContext(gherkin_text="")
    gate = Q0NormaValidatorGate()
    result = gate.evaluate(ctx)

    assert result.gate_id == "Q0"
    assert result.passed is False
    assert "empty" in result.issues[0].lower()


def test_aggregate_results_hard_pass():
    results = [
        GateResult(gate_id="Q0", passed=True, score=1.0),
        GateResult(gate_id="Q1", passed=True, score=1.0),
        GateResult(gate_id="Q6", passed=True, score=0.90),
    ]
    verdict = aggregate_results(results)
    assert verdict.hard_pass is True
    assert verdict.soft_score == 0.90
    assert verdict.is_overall_pass is True


def test_aggregate_results_hard_fail():
    results = [
        GateResult(gate_id="Q0", passed=False, score=0.0, issues=["Syntax error"]),
        GateResult(gate_id="Q1", passed=True, score=1.0),
    ]
    verdict = aggregate_results(results)
    assert verdict.hard_pass is False
    assert verdict.is_overall_pass is False
