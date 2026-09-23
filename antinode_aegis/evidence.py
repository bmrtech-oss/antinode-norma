"""Validation for the machine-readable ADR-003 evidence matrix."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

SURFACES = ("ui", "api", "cli", "mcp")
SURFACE_STATUSES = {"required", "supported", "not_applicable", "planned", "blocked"}
MATRIX_STATUSES = {"implemented", "partial", "planned", "deferred", "waived", "not_applicable"}
REQUIRED_FIELDS = {
    "requirement_id",
    "release_profile",
    "phase",
    "task_id",
    "owner",
    "code_paths",
    "test_paths",
    "command",
    "expected_result",
    "artifact_path",
    "surfaces",
    "status",
    "last_verified",
}
SURFACE_REFERENCE_FIELDS = {
    "ui": "route_or_component",
    "api": "endpoint_or_schema",
    "cli": "command",
    "mcp": "tool_or_resource",
}


@dataclass(frozen=True)
class EvidenceMatrixError:
    """A validation error tied to a matrix location."""

    location: str
    message: str

    def __str__(self) -> str:
        return f"{self.location}: {self.message}"


def validate_matrix(path: Path) -> list[EvidenceMatrixError]:
    """Return validation errors for an ADR-003 evidence matrix."""

    errors: list[EvidenceMatrixError] = []
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return [EvidenceMatrixError(str(path), f"cannot load YAML: {exc}")]

    if not isinstance(document, dict):
        return [EvidenceMatrixError("document", "must be a mapping")]

    _require_equal(errors, document, "version", 1, "document")
    _require_equal(errors, document, "document", "ADR-003-AEGIS", "document")

    schema = document.get("schema")
    if not isinstance(schema, dict):
        errors.append(EvidenceMatrixError("schema", "must be a mapping"))
        schema = {}

    _validate_schema(errors, schema)
    requirements = document.get("requirements")
    if not isinstance(requirements, list) or not requirements:
        errors.append(EvidenceMatrixError("requirements", "must be a non-empty list"))
        return errors

    root = path.parent.parent.parent
    for index, requirement in enumerate(requirements):
        location = f"requirements[{index}]"
        _validate_requirement(errors, requirement, location, root)
    return errors


def _validate_schema(
    errors: list[EvidenceMatrixError],
    schema: dict[str, Any],
) -> None:
    required = schema.get("required")
    if not isinstance(required, list):
        errors.append(EvidenceMatrixError("schema.required", "must be a list"))
    else:
        missing = REQUIRED_FIELDS.difference(required)
        if missing:
            errors.append(
                EvidenceMatrixError(
                    "schema.required",
                    f"missing fields: {', '.join(sorted(missing))}",
                )
            )

    statuses = schema.get("statuses")
    if not isinstance(statuses, list):
        errors.append(EvidenceMatrixError("schema.statuses", "must be a list"))
    elif set(statuses) != MATRIX_STATUSES:
        errors.append(
            EvidenceMatrixError(
                "schema.statuses",
                f"must contain exactly: {', '.join(sorted(MATRIX_STATUSES))}",
            )
        )


def _validate_requirement(
    errors: list[EvidenceMatrixError],
    requirement: Any,
    location: str,
    root: Path,
) -> None:
    if not isinstance(requirement, dict):
        errors.append(EvidenceMatrixError(location, "must be a mapping"))
        return

    missing = REQUIRED_FIELDS.difference(requirement)
    if missing:
        errors.append(EvidenceMatrixError(location, f"missing fields: {', '.join(sorted(missing))}"))
        return

    for field in ("requirement_id", "release_profile", "phase", "task_id", "owner", "expected_result"):
        if not isinstance(requirement[field], str) or not requirement[field].strip():
            errors.append(EvidenceMatrixError(f"{location}.{field}", "must be a non-empty string"))

    status = requirement["status"]
    if status not in MATRIX_STATUSES:
        errors.append(
            EvidenceMatrixError(
                f"{location}.status",
                f"must be one of: {', '.join(sorted(MATRIX_STATUSES))}",
            )
        )

    for field in ("code_paths", "test_paths"):
        _validate_paths(errors, requirement[field], f"{location}.{field}", root)

    artifact_path = requirement["artifact_path"]
    if artifact_path is not None and not isinstance(artifact_path, str):
        errors.append(EvidenceMatrixError(f"{location}.artifact_path", "must be a string or null"))
    elif isinstance(artifact_path, str) and not (root / artifact_path).exists():
        errors.append(
            EvidenceMatrixError(
                f"{location}.artifact_path",
                f"referenced artifact does not exist: {artifact_path}",
            )
        )

    _validate_surfaces(errors, requirement["surfaces"], f"{location}.surfaces", root)

    if status in {"implemented", "partial"}:
        if not isinstance(requirement["command"], str) or not requirement["command"].strip():
            errors.append(EvidenceMatrixError(f"{location}.command", "required for implemented or partial records"))
        if not requirement["code_paths"]:
            errors.append(EvidenceMatrixError(f"{location}.code_paths", "cannot be empty for implemented or partial records"))
        if not requirement["test_paths"]:
            errors.append(EvidenceMatrixError(f"{location}.test_paths", "cannot be empty for implemented or partial records"))
        if not isinstance(artifact_path, str) or not artifact_path.strip():
            errors.append(EvidenceMatrixError(f"{location}.artifact_path", "required for implemented or partial records"))
        if not isinstance(requirement["last_verified"], str) or not requirement["last_verified"].strip():
            errors.append(EvidenceMatrixError(f"{location}.last_verified", "required for implemented or partial records"))


def _validate_paths(
    errors: list[EvidenceMatrixError],
    value: Any,
    location: str,
    root: Path,
) -> None:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        errors.append(EvidenceMatrixError(location, "must be a list of strings"))
        return
    for item in value:
        if not item:
            errors.append(EvidenceMatrixError(location, "paths cannot contain empty strings"))
        elif not (root / item).exists():
            errors.append(EvidenceMatrixError(location, f"referenced path does not exist: {item}"))


def _validate_surfaces(
    errors: list[EvidenceMatrixError],
    value: Any,
    location: str,
    root: Path,
) -> None:
    if not isinstance(value, dict):
        errors.append(EvidenceMatrixError(location, "must be a mapping"))
        return

    missing = set(SURFACES).difference(value)
    if missing:
        errors.append(EvidenceMatrixError(location, f"missing surfaces: {', '.join(sorted(missing))}"))

    for surface in SURFACES:
        entry = value.get(surface)
        surface_location = f"{location}.{surface}"
        if not isinstance(entry, dict):
            errors.append(EvidenceMatrixError(surface_location, "must be a mapping"))
            continue

        status = entry.get("status")
        if status not in SURFACE_STATUSES:
            errors.append(
                EvidenceMatrixError(
                    f"{surface_location}.status",
                    f"must be one of: {', '.join(sorted(SURFACE_STATUSES))}",
                )
            )

        reference_field = SURFACE_REFERENCE_FIELDS[surface]
        reference = entry.get(reference_field)
        if not isinstance(reference, str) or not reference.strip():
            errors.append(EvidenceMatrixError(f"{surface_location}.{reference_field}", "must be a non-empty string"))

        test_paths = entry.get("test_paths")
        _validate_paths(errors, test_paths, f"{surface_location}.test_paths", root)


def _require_equal(
    errors: list[EvidenceMatrixError],
    document: dict[str, Any],
    field: str,
    expected: Any,
    location: str,
) -> None:
    if document.get(field) != expected:
        errors.append(EvidenceMatrixError(f"{location}.{field}", f"must equal {expected!r}"))


def main(argv: list[str] | None = None) -> int:
    """Run evidence-matrix validation as a command-line module."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="path to evidence-matrix.yml")
    args = parser.parse_args(argv)

    errors = validate_matrix(args.path)
    if errors:
        for error in errors:
            print(f"ERROR {error}")
        return 1
    print(f"Evidence matrix valid: {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
