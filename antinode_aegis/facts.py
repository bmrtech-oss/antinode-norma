"""Backend-agnostic Aegis knowledge-graph fact schema."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import BaseModel, Field


class FactProvenance(BaseModel):
    source: str
    source_version: Optional[str] = None
    curator: Optional[str] = None
    reviewed_at: Optional[str] = None


class KnowledgeFact(BaseModel):
    id: str
    subject: str
    predicate: str
    object: str
    contradiction_phrase: str
    provenance: FactProvenance = Field(
        default_factory=lambda: FactProvenance(source="curated-static")
    )
    tags: List[str] = Field(default_factory=list)


class FactCatalog(BaseModel):
    schema_version: int = 1
    facts: List[KnowledgeFact]

    @classmethod
    def from_yaml(cls, path: Path) -> "FactCatalog":
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return cls.model_validate(data)