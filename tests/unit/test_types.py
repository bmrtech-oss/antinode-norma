from antinode_norma.core.types import (
    TestCase,
    DomainEntity,
    DomainModel,
    GateResult,
    Verdict,
)


def test_test_case_initialization():
    case = TestCase(
        id="TC-001",
        title="User Login",
        role="registered user",
        action="log in",
        benefit="access my account",
        acceptance_criteria=["Valid credentials succeed"],
        tags=["auth", "smoke"],
    )
    assert case.id == "TC-001"
    assert case.role == "registered user"
    assert "auth" in case.tags


def test_domain_model_initialization():
    entity = DomainEntity(
        name="Account",
        attributes=["id", "balance"],
        relationships={"owner": "User"},
    )
    model = DomainModel(name="Banking", entities=[entity])
    assert model.name == "Banking"
    assert len(model.entities) == 1
    assert model.entities[0].name == "Account"


def test_gate_result_initialization():
    gate = GateResult(
        gate_id="Q1",
        passed=True,
        score=1.0,
        issues=[],
    )
    assert gate.gate_id == "Q1"
    assert gate.passed is True


def test_verdict_pass_thresholds():
    passing_verdict = Verdict(
        hard_pass=True,
        soft_score=0.90,
        sem_score=0.88,
    )
    assert passing_verdict.is_overall_pass is True

    failing_soft_verdict = Verdict(
        hard_pass=True,
        soft_score=0.80,
        sem_score=0.90,
    )
    assert failing_soft_verdict.is_overall_pass is False

    failing_hard_verdict = Verdict(
        hard_pass=False,
        soft_score=0.95,
        sem_score=0.95,
    )
    assert failing_hard_verdict.is_overall_pass is False
