from pathlib import Path

import yaml

from antinode_aegis.evidence import validate_matrix

MATRIX_PATH = Path(__file__).parents[2] / "docs" / "adr" / "evidence-matrix.yml"


def test_repository_evidence_matrix_is_valid() -> None:
    assert validate_matrix(MATRIX_PATH) == []


def test_validator_rejects_missing_surface_and_broken_path(tmp_path: Path) -> None:
    document = yaml.safe_load(MATRIX_PATH.read_text(encoding="utf-8"))
    requirement = document["requirements"][0]
    requirement["code_paths"] = ["does/not/exist.py"]
    del requirement["surfaces"]["mcp"]

    matrix_path = tmp_path / "evidence-matrix.yml"
    matrix_path.write_text(yaml.safe_dump(document), encoding="utf-8")

    errors = validate_matrix(matrix_path)

    messages = [str(error) for error in errors]
    assert any("referenced path does not exist" in message for message in messages)
    assert any("missing surfaces: mcp" in message for message in messages)


def test_validator_requires_evidence_for_implemented_records(tmp_path: Path) -> None:
    document = yaml.safe_load(MATRIX_PATH.read_text(encoding="utf-8"))
    requirement = document["requirements"][0]
    requirement["artifact_path"] = None
    requirement["command"] = None

    matrix_path = tmp_path / "evidence-matrix.yml"
    matrix_path.write_text(yaml.safe_dump(document), encoding="utf-8")

    messages = [str(error) for error in validate_matrix(matrix_path)]

    assert any("command: required for implemented or partial records" in message for message in messages)
    assert any("artifact_path: required for implemented or partial records" in message for message in messages)
