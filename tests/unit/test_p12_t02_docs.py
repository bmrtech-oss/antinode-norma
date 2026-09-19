"""
Unit tests for Task P12-T02: Documentation consolidation.
Verifies that all required architecture and platform documentation files exist and contain key required sections.
"""

from pathlib import Path


def test_docs_files_exist():
    docs_dir = Path("docs")
    required_docs = [
        "ARCHITECTURE.md",
        "QUALITY_GATES.md",
        "CONFIGURATION.md",
        "SECRETS.md",
        "COST.md",
        "GIT_WORKFLOW.md",
        "ROLLBACK.md",
        "ESCALATION.md",
        "TRACKS.md",
        "UI.md",
        "AUTH.md",
        "EXECUTION.md",
        "PLUGINS.md",
    ]

    for doc_name in required_docs:
        doc_path = docs_dir / doc_name
        assert doc_path.exists(), f"Required documentation file {doc_path} is missing."
        assert doc_path.stat().st_size > 100, f"Documentation file {doc_path} appears empty or too short."


def test_architecture_doc_content():
    content = Path("docs/ARCHITECTURE.md").read_text()
    assert "NormaAgent" in content
    assert "TestCase" in content
    assert "Quality Gate" in content


def test_quality_gates_doc_content():
    content = Path("docs/QUALITY_GATES.md").read_text()
    assert "Q0" in content
    assert "Q10" in content
    assert "hard_pass" in content
    assert "soft_score" in content


def test_configuration_doc_content():
    content = Path("docs/CONFIGURATION.md").read_text()
    assert "features" in content
    assert "norma.config.yml" in content
    assert "NORMA_LLM_PROVIDER" in content


def test_readme_references_docs():
    readme_content = Path("README.md").read_text()
    assert "docs/ARCHITECTURE.md" in readme_content
    assert "docs/QUALITY_GATES.md" in readme_content
    assert "docs/CONFIGURATION.md" in readme_content
    assert "docs/PLUGINS.md" in readme_content
