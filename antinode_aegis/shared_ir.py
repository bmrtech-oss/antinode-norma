"""Shared Aegis IR adapter for existing Norma structured ingestion."""

from __future__ import annotations

from typing import Any

from antinode_aegis.contracts import RequirementIR
from antinode_aegis.csv import ingest_csv
from antinode_aegis.story import ingest_stories
from antinode_aegis.xlsx import ingest_xlsx


def normalize_requirements(
    source: Any,
    kind: str,
    *,
    source_reference: str | None = None,
    sheet_name: str | None = None,
    release_profile: str = "aegis-foundation",
) -> list[RequirementIR]:
    """Normalize CSV, XLSX, or story input into the shared Aegis IR."""

    kind_clean = kind.lower().strip()
    if kind_clean == "csv":
        return ingest_csv(
            source,
            release_profile=release_profile,
        )
    if kind_clean in {"xlsx", "excel"}:
        return ingest_xlsx(
            source,
            sheet_name=sheet_name,
            release_profile=release_profile,
        )
    if kind_clean in {"story", "dict"}:
        return ingest_stories(
            source,
            source_reference=source_reference,
            release_profile=release_profile,
        )
    raise ValueError(f"Unsupported ingest kind: '{kind}'")
