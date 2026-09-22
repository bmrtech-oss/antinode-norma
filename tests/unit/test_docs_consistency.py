from pathlib import Path


def test_readme_has_hardening_docs():
    readme_path = Path("README.md")
    assert readme_path.exists(), "README.md must exist"

    content = readme_path.read_text(encoding="utf-8")

    required_links = [
        "docs/HARDENING_SUMMARY.md",
        "docs/SCORE.md",
        "docs/RELEASE_CHECKLIST.md",
        "docs/DR.md",
        "docs/MIGRATION.md",
        "docs/API_VERSIONING.md",
    ]

    for link in required_links:
        assert link in content, f"README.md missing documentation link: {link}"


def test_norma_summary_has_hardening():
    summary_path = Path("docs/NORMA_SUMMARY.md")
    assert summary_path.exists(), "docs/NORMA_SUMMARY.md must exist"

    content = summary_path.read_text(encoding="utf-8")
    assert "ADR-002" in content
