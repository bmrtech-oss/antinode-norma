"""Aegis XLSX ingestion adapter with worksheet provenance."""

from __future__ import annotations

from pathlib import Path

from antinode_aegis.contracts import RequirementIR
from antinode_norma.ingest_structured.xlsx import XLSXIngester


def ingest_xlsx(
    source: str | Path,
    *,
    sheet_name: str | None = None,
    release_profile: str = "aegis-foundation",
) -> list[RequirementIR]:
    """Read an XLSX worksheet through Norma into versioned Aegis IR."""

    source_path = Path(source)
    cases = XLSXIngester(sheet_name=sheet_name).ingest(source_path)
    reference = str(source_path)
    if sheet_name:
        reference = f"{reference}#{sheet_name}"

    return [
        RequirementIR.from_test_case(
            case,
            source_kind="xlsx",
            source_reference=reference,
            release_profile=release_profile,
        )
        for case in cases
    ]
