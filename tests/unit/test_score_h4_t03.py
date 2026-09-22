from pathlib import Path


def test_score_md_exists_and_valid():
    score_path = Path("docs/SCORE.md")
    assert score_path.exists(), "docs/SCORE.md must exist"

    content = score_path.read_text(encoding="utf-8")

    assert "# NORMA-BDD Post-Implementation Score Evaluation & Re-Scoring" in content
    assert "9.03" in content
    assert "8.61" in content
    assert "9.09" in content

    required_dimensions = [
        "Security",
        "Enterprise readiness",
        "Determinism",
        "Quality & gates",
        "Performance",
        "Product / UX",
        "Observability",
        "Migration / config",
        "Operational maturity",
        "API strategy",
        "Plugin ecosystem",
        "Governance / approval",
        "Release discipline",
    ]

    for dim in required_dimensions:
        assert dim in content, f"Missing required dimension in docs/SCORE.md: {dim}"
