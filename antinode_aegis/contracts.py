"""Versioned Aegis domain contracts built on the Norma normalization model."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from antinode_norma.core.types import DomainModel, TestCase


class AegisContractMetadata(BaseModel):
    """Metadata required to preserve source and contract provenance."""

    contract_version: str = "1"
    source_kind: str
    source_reference: str | None = None
    release_profile: str = "aegis-foundation"


class RequirementIR(BaseModel):
    """Stable intermediate representation shared by Aegis surfaces."""

    model_config = ConfigDict(extra="forbid")

    requirement_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    role: str = Field(min_length=1)
    action: str = Field(min_length=1)
    benefit: str = ""
    acceptance_criteria: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    provenance: AegisContractMetadata

    @classmethod
    def from_test_case(
        cls,
        case: TestCase,
        *,
        source_kind: str,
        source_reference: str | None = None,
        release_profile: str = "aegis-foundation",
    ) -> RequirementIR:
        return cls(
            requirement_id=case.id,
            title=case.title,
            role=case.role,
            action=case.action,
            benefit=case.benefit,
            acceptance_criteria=case.acceptance_criteria,
            tags=case.tags,
            metadata=case.metadata,
            provenance=AegisContractMetadata(
                source_kind=source_kind,
                source_reference=source_reference,
                release_profile=release_profile,
            ),
        )

    def to_test_case(self) -> TestCase:
        """Return the compatible Norma representation without losing provenance."""

        metadata = dict(self.metadata)
        metadata["aegis_provenance"] = self.provenance.model_dump()
        return TestCase(
            id=self.requirement_id,
            title=self.title,
            role=self.role,
            action=self.action,
            benefit=self.benefit,
            acceptance_criteria=self.acceptance_criteria,
            tags=self.tags,
            metadata=metadata,
        )


class AegisDomainContract(BaseModel):
    """Stable domain contract used by API, CLI, and MCP adapters."""

    contract_version: str = "1"
    domain: DomainModel = Field(default_factory=DomainModel)
    requirements: list[RequirementIR] = Field(default_factory=list)
    metadata: AegisContractMetadata = Field(
        default_factory=lambda: AegisContractMetadata(source_kind="domain-model")
    )
