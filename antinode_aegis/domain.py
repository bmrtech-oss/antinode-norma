"""Aegis adapter for loading the existing Norma domain model."""

from __future__ import annotations

from pathlib import Path

from antinode_aegis.contracts import AegisContractMetadata, AegisDomainContract
from antinode_norma.core.model_loader import load_domain_model


def load_aegis_domain_contract(
    path: str | Path | None = None,
    *,
    release_profile: str = "aegis-foundation",
) -> AegisDomainContract:
    """Load a Norma domain model into the versioned Aegis domain contract."""

    model_path = Path(path) if path is not None else Path("model.yaml")
    domain = load_domain_model(model_path)
    return AegisDomainContract(
        domain=domain,
        metadata=AegisContractMetadata(
            source_kind="domain-model",
            source_reference=str(model_path),
            release_profile=release_profile,
        ),
    )
