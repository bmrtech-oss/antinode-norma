from pathlib import Path


def test_ai_governance_register_maps_required_control_themes() -> None:
    root = Path(__file__).resolve().parents[2]
    document = (root / "docs" / "AI_GOVERNANCE.md").read_text(encoding="utf-8")

    for term in (
        "ISO/IEC 42001",
        "EU AI Act",
        "Risk management",
        "Data governance",
        "Technical documentation",
        "Record-keeping",
        "Transparency",
        "Human oversight",
        "Accuracy and robustness",
        "Cybersecurity",
        "Post-market monitoring",
        "not a certification or conformity",
        "customer-dependent",
    ):
        assert term in document


def test_governance_register_links_existing_policies_and_preserves_boundary() -> None:
    root = Path(__file__).resolve().parents[2]
    document = (root / "docs" / "AI_GOVERNANCE.md").read_text(encoding="utf-8")

    for relative_path in ("ESCALATION.md", "SECRETS.md", "ROLLBACK.md", "COMPONENT_SOURCING.md"):
        assert (root / "docs" / relative_path).exists()
        assert relative_path in document
    assert "never represented" in document
    assert "because a document exists" in document
