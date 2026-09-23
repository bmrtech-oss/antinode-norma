from pathlib import Path

from antinode_aegis.domain import load_aegis_domain_contract


def test_aegis_domain_loader_preserves_norma_model_and_provenance() -> None:
    contract = load_aegis_domain_contract("model.yaml")

    assert contract.domain.name == "norma_baseline_domain"
    assert {entity.name for entity in contract.domain.entities} == {"User", "Account"}
    assert contract.metadata.source_kind == "domain-model"
    assert contract.metadata.source_reference == str(Path("model.yaml"))


def test_aegis_domain_loader_keeps_missing_model_compatible() -> None:
    contract = load_aegis_domain_contract("missing-model.yaml")

    assert contract.domain.name == "default"
    assert contract.domain.entities == []
