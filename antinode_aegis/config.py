"""Aegis configuration contract with safe disabled-by-default behavior."""

from pydantic import BaseModel, Field


class AegisConfig(BaseModel):
    """Configuration shared by future Aegis adapters."""

    enabled: bool = False
    release_profile: str = "aegis-foundation"
    contract_version: str = "1"
    require_surface_parity: bool = True
    evidence_matrix_path: str = "docs/adr/evidence-matrix.yml"
    max_repair_attempts: int = Field(default=3, ge=0, le=10)
