import json
from pathlib import Path


def test_component_sourcing_register_separates_verified_and_future_candidates() -> None:
    root = Path(__file__).resolve().parents[2]
    document = (root / "docs" / "COMPONENT_SOURCING.md").read_text(encoding="utf-8")

    assert "## Verified current reuse" in document
    assert "## Future candidates requiring a separate verification record" in document
    assert "contributes no savings" in document
    for term in ("FastAPI", "React 18", "Playwright", "openpyxl", "Ruff", "gitleaks"):
        assert term in document
    for term in ("PostgreSQL", "Redis with Dramatiq or Celery", "Not installed or verified"):
        assert term in document


def test_verified_candidates_are_present_in_repository_manifests() -> None:
    root = Path(__file__).resolve().parents[2]
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    ui_package = json.loads((root / "ui" / "package.json").read_text(encoding="utf-8"))
    ui_dependencies = {
        *ui_package["dependencies"].keys(),
        *ui_package["devDependencies"].keys(),
    }

    for package in ("fastapi", "pydantic", "openpyxl", "PyYAML", "gherkin-official"):
        assert package in pyproject
    for package in ("react", "vite", "@playwright/test", "tailwindcss"):
        assert package in ui_dependencies
