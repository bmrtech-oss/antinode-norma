"""Aegis CSV ingestion adapter with versioned provenance."""

from __future__ import annotations

from pathlib import Path

from antinode_aegis.contracts import RequirementIR
from antinode_norma.ingest_structured.csv import CSVIngester


def ingest_csv(
    source: str | Path,
    *,
    release_profile: str = "aegis-foundation",
) -> list[RequirementIR]:
    """Read a CSV file through Norma and return versioned Aegis requirements."""

    source_path = Path(source)
    cases = CSVIngester().ingest(source_path)
    return [
        RequirementIR.from_test_case(
            case,
            source_kind="csv",
            source_reference=str(source_path),
            release_profile=release_profile,
        )
        for case in cases
    ]
