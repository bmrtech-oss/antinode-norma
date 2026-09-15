import pytest
from antinode_norma.core.model_loader import load_domain_model


def test_load_default_model_yaml():
    model = load_domain_model("model.yaml")
    assert model.name == "norma_baseline_domain"
    assert len(model.entities) == 2
    entity_names = [e.name for e in model.entities]
    assert "User" in entity_names
    assert "Account" in entity_names


def test_load_non_existent_file():
    model = load_domain_model("non_existent_model.yaml")
    assert model.name == "default"
    assert len(model.entities) == 0


def test_load_custom_yaml(tmp_path):
    custom_yaml = tmp_path / "custom.yaml"
    custom_yaml.write_text(
        "name: custom_domain\nentities:\n  - name: Order\n    attributes: [id, price]\n"
    )

    model = load_domain_model(custom_yaml)
    assert model.name == "custom_domain"
    assert len(model.entities) == 1
    assert model.entities[0].name == "Order"


def test_load_invalid_yaml(tmp_path):
    invalid_yaml = tmp_path / "invalid.yaml"
    invalid_yaml.write_text("entities: [invalid: yaml: :")

    with pytest.raises(ValueError, match="Failed to load domain model"):
        load_domain_model(invalid_yaml)
