import re
from typing import List, Union, Optional, Dict

HEADER_ALIASES: Dict[str, str] = {
    # ID
    "id": "id",
    "key": "id",
    "case id": "id",
    "test id": "id",
    "test_id": "id",
    "case_id": "id",
    # Title
    "title": "title",
    "name": "title",
    "summary": "title",
    "scenario": "title",
    "scenario_title": "title",
    # Role
    "role": "role",
    "as a": "role",
    "as_a": "role",
    "user": "role",
    "actor": "role",
    # Action
    "action": "action",
    "i want to": "action",
    "i_want_to": "action",
    "goal": "action",
    "when": "action",
    # Benefit
    "benefit": "benefit",
    "so that": "benefit",
    "so_that": "benefit",
    "outcome": "benefit",
    "then": "benefit",
    # Acceptance Criteria
    "acceptance_criteria": "acceptance_criteria",
    "acceptance criteria": "acceptance_criteria",
    "criteria": "acceptance_criteria",
    "given": "acceptance_criteria",
    "steps": "acceptance_criteria",
    "rules": "acceptance_criteria",
    # Tags
    "tags": "tags",
    "labels": "tags",
    "categories": "tags",
}


def normalize_header(header: str) -> str:
    """Normalize a raw tabular or CSV/XLSX header string to its canonical TestCase field name."""
    if not header:
        return ""
    clean = header.strip().lower().replace("-", " ").replace("_", " ")
    clean = re.sub(r"\s+", " ", clean)
    return HEADER_ALIASES.get(clean, clean.replace(" ", "_"))


def split_multi(
    value: Union[str, List[str], None],
    delimiters: Optional[List[str]] = None,
) -> List[str]:
    """Split multi-value or multi-line text into a cleaned list of non-empty strings."""
    if value is None:
        return []

    if isinstance(value, list):
        result = []
        for item in value:
            result.extend(split_multi(item, delimiters))
        return result

    val_str = str(value).strip()
    if not val_str:
        return []

    if delimiters is None:
        delimiters = [";", "\n", "|"]

    pattern = "|".join(re.escape(d) for d in delimiters)
    parts = re.split(pattern, val_str)

    cleaned = []
    for part in parts:
        stripped = part.strip()
        if stripped:
            if stripped.startswith("- "):
                stripped = stripped[2:].strip()
            elif stripped.startswith("* "):
                stripped = stripped[2:].strip()
            if stripped:
                cleaned.append(stripped)

    return cleaned
