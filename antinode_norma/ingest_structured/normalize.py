from typing import Any, List, Optional
from antinode_norma.core.types import TestCase, DomainModel
from antinode_norma.ingest_structured.csv import CSVIngester
from antinode_norma.ingest_structured.xlsx import XLSXIngester
from antinode_norma.ingest_structured.story import story_to_case


def normalize(
    source: Any,
    kind: str,
    model: Optional[DomainModel] = None,
    sheet_name: Optional[str] = None,
) -> List[TestCase]:
    """Unified normalize adapter converting CSV, XLSX, or story dicts into a list of TestCases."""
    kind_clean = kind.lower().strip()

    if kind_clean == "csv":
        ingester = CSVIngester()
        cases = ingester.ingest(source)
    elif kind_clean in {"xlsx", "excel"}:
        ingester = XLSXIngester(sheet_name=sheet_name)
        cases = ingester.ingest(source)
    elif kind_clean in {"story", "dict"}:
        if isinstance(source, list):
            cases = [story_to_case(s) for s in source if isinstance(s, dict)]
        elif isinstance(source, dict):
            cases = [story_to_case(source)]
        else:
            raise ValueError(f"Invalid story source type: {type(source)}")
    else:
        raise ValueError(f"Unsupported ingest kind: '{kind}'")

    if model:
        for case in cases:
            case.metadata["domain_model"] = model.name

    return cases
