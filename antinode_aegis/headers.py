"""Versioned Aegis adapter for canonical structured-ingest headers."""

from __future__ import annotations

from collections.abc import Mapping

from antinode_norma.core.normalize import normalize_header


def normalize_headers(headers: list[str | None]) -> dict[str, str]:
    """Map raw headers to the canonical Norma/Aegis field names."""

    return {
        header: normalize_header(header or "")
        for header in headers
        if header is not None
    }


def normalize_row(
    row: Mapping[str, object],
) -> dict[str, object]:
    """Normalize a tabular row while preserving values and unknown fields."""

    return {
        normalize_header(str(header)): value
        for header, value in row.items()
        if header is not None
    }
