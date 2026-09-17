from antinode_norma.core.types import TestCase, DomainModel, DomainEntity
from antinode_norma.core.prompts import build_feature_generation_prompt


def test_build_feature_generation_prompt_basic():
    tc = TestCase(
        id="TC-101",
        title="Login Test",
        role="user",
        action="log in with credentials",
        benefit="access account",
        acceptance_criteria=["Valid password logs user in"],
    )

    sys_p, user_p = build_feature_generation_prompt([tc])

    assert "expert BDD author" in sys_p
    assert "Test Case [TC-101]: Login Test" in user_p
    assert "@TC-101" in user_p
    assert "Valid password logs user in" in user_p


def test_build_feature_generation_prompt_with_domain_model_and_feedback():
    tc = TestCase(id="TC-102", title="Checkout")
    domain = DomainModel(
        entities=[DomainEntity(name="Cart", attributes=["total_price"])]
    )
    feedback = ["Missing @TC-102 tag"]

    sys_p, user_p = build_feature_generation_prompt([tc], domain_model=domain, feedback=feedback)

    assert "Domain Model Context" in user_p
    assert "Cart" in user_p
    assert "PREVIOUS EVALUATION FEEDBACK" in user_p
    assert "Missing @TC-102 tag" in user_p
