from antinode_aegis.config import AegisConfig
from antinode_aegis.contracts import RequirementIR
from antinode_norma.core.types import TestCase as NormaTestCase


def test_requirement_ir_round_trips_existing_norma_test_case() -> None:
    case = NormaTestCase(
        id="STORY-001",
        title="Reset password",
        role="registered user",
        action="reset password",
        benefit="regain access",
        acceptance_criteria=["Reset link is sent"],
        metadata={"source_row": 4},
    )

    contract = RequirementIR.from_test_case(
        case,
        source_kind="csv",
        source_reference="sample_stories.csv#4",
    )

    restored = contract.to_test_case()

    assert restored.id == case.id
    assert restored.acceptance_criteria == case.acceptance_criteria
    assert restored.metadata["aegis_provenance"]["source_kind"] == "csv"
    assert contract.provenance.contract_version == "1"


def test_domain_contract_rejects_unknown_requirement_fields() -> None:
    try:
        RequirementIR(
            requirement_id="STORY-001",
            title="A story",
            role="user",
            action="act",
            provenance={"source_kind": "csv"},
            unexpected="not allowed",
        )
    except ValueError as exc:
        assert "unexpected" in str(exc)
    else:
        raise AssertionError("unknown contract fields must be rejected")


def test_aegis_config_is_disabled_by_default_and_bounds_repairs() -> None:
    config = AegisConfig()

    assert config.enabled is False
    assert config.require_surface_parity is True
    assert config.max_repair_attempts == 3
