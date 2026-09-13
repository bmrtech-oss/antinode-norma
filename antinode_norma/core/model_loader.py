import yaml
from pathlib import Path
from typing import Union, Optional
from antinode_norma.core.types import DomainModel, DomainEntity


def load_domain_model(path: Optional[Union[str, Path]] = None) -> DomainModel:
    """Load and parse domain model definitions from a YAML file."""
    model_path = Path(path) if path else Path("model.yaml")

    if not model_path.exists():
        return DomainModel(name="default")

    try:
        with open(model_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        name = data.get("name", "default")
        raw_entities = data.get("entities", [])
        entities = []

        for item in raw_entities:
            if isinstance(item, dict):
                entities.append(
                    DomainEntity(
                        name=item.get("name", "Unnamed"),
                        attributes=item.get("attributes", []),
                        relationships=item.get("relationships", {}),
                    )
                )

        metadata = data.get("metadata", {})
        return DomainModel(name=name, entities=entities, metadata=metadata)
    except Exception as exc:
        raise ValueError(f"Failed to load domain model from {model_path}: {exc}")
