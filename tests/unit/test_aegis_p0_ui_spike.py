from pathlib import Path


def test_ui_spike_is_non_production_and_covers_foundation_surfaces() -> None:
    root = Path(__file__).resolve().parents[2]
    html = (root / "spike" / "ui" / "index.html").read_text(encoding="utf-8")
    readme = (root / "spike" / "ui" / "README.md").read_text(encoding="utf-8")

    for term in ("Aegis foundation UI spike", "Non-production proof of concept", "role=\"status\""):
        assert term in html
    for term in ("Evidence", "Escalations", "Feature flags", "Release gate"):
        assert term in html
    for term in ("does not add production routes", "Aegis API contracts", "versioned contract", "CLI-only release"):
        assert term in readme


def test_ui_documentation_points_to_existing_frontend_primitives() -> None:
    root = Path(__file__).resolve().parents[2]
    readme = (root / "spike" / "ui" / "README.md").read_text(encoding="utf-8")

    assert "ui/src/components/AppShell.tsx" in readme
    assert "ui/src/components/ui/" in readme
