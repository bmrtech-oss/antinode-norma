from antinode_norma.gates.types import GateContext
from antinode_norma.gates.semantic import Q10SemanticJudgeGate
from antinode_norma.gates.runner import GateRunner
from antinode_norma.core.types import TestCase, DomainModel, DomainEntity


def test_q10_empty_context():
    gate = Q10SemanticJudgeGate()
    context = GateContext(gherkin_text="")
    result = gate.evaluate(context)
    assert result.passed is True
    assert result.score == 1.0


def test_q10_llm_callable():
    def mock_llm(prompt: str) -> str:
        return "Score: 0.95"

    gate = Q10SemanticJudgeGate(llm_callable=mock_llm)
    context = GateContext(gherkin_text="Feature: Test", metadata={"user_story": "As a user..."})
    result = gate.evaluate(context)
    assert result.passed is True
    assert result.score == 0.95


def test_q10_fallback_overlap():
    domain_model = DomainModel(
        name="account",
        entities=[DomainEntity(name="account", attributes=["balance"])]
    )
    gherkin = """
    @TC-101
    Feature: Account details

      Scenario: View balance
        Given the user has an active account
        When the user opens balance settings
        Then the account balance displays
    """
    tc = TestCase(id="TC-101", title="View balance", steps=["Given the user has an active account"])
    gate = Q10SemanticJudgeGate()
    context = GateContext(
        gherkin_text=gherkin,
        test_cases=[tc],
        domain_model=domain_model,
        metadata={"user_story": "As an account holder I want to view balance"}
    )
    result = gate.evaluate(context)
    assert result.passed is True
    assert result.score >= 0.85


def test_gate_runner_q0_to_q10_wired():
    runner = GateRunner()
    gate_ids = [g.gate_id for g in runner.gates]
    assert gate_ids == ["Q0", "Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "Q9", "Q10"]

    gherkin = """
    @TC-1
    Feature: Full Gate Execution

      Scenario: Execute all gates
        Given a valid system state
        When an event occurs
        Then the system responds correctly
    """
    tc = TestCase(id="TC-1", title="Execute all gates", steps=["Given a valid system state", "When an event occurs", "Then the system responds correctly"])
    context = GateContext(gherkin_text=gherkin, test_cases=[tc])
    verdict = runner.evaluate(context)

    assert verdict.hard_pass is True
    assert verdict.summary == "PASS"
    assert "Q10" in verdict.gate_results
    assert "Q6" in verdict.gate_results
