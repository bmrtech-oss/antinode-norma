"""Shared Aegis IR adapter for existing Norma structured ingestion."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from antinode_aegis.contracts import RequirementIR
from antinode_norma.ingest_structured.normalize import normalize


def normalize_requirements(
    source: Any,
    kind: str,
    *,
    source_reference: str | None = None,
    sheet_name: str | None = None,
    release_profile: str = "aegis-foundation",
) -> list[RequirementIR]:
    """Normalize CSV, XLSX, or story input into the shared Aegis IR."""

    cases = normalize(source, kind, sheet_name=sheet_name)
    reference = source_reference
    if reference is None and isinstance(source, (str, Path)):
        reference = str(source)

    return [
        RequirementIR.from_test_case(
            case,
            source_kind=kind.lower().strip(),
            source_reference=reference,
            release_profile=release_profile,
        )
        for case in cases
    ]
