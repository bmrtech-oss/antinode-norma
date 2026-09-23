from pathlib import Path

from antinode_aegis.shared_ir import normalize_requirements


def test_shared_ir_normalizes_csv_through_existing_norma_ingest() -> None:
    requirements = normalize_requirements(
        Path("test data/sample_stories.csv"),
        "csv",
    )

    assert requirements
    assert all(item.provenance.source_kind == "csv" for item in requirements)
    assert requirements[0].provenance.source_reference == str(Path("test data/sample_stories.csv"))
    assert requirements[0].requirement_id


def test_shared_ir_normalizes_story_dicts_with_explicit_reference() -> None:
    requirements = normalize_requirements(
        {
            "story_id": "STORY-IR-001",
            "title": "Export report",
            "role": "analyst",
            "action": "export a report",
            "benefit": "share findings",
            "acceptance_criteria": ["The report downloads"],
        },
        "story",
        source_reference="request-42",
    )

    assert len(requirements) == 1
    assert requirements[0].requirement_id == "STORY-IR-001"
    assert requirements[0].provenance.source_reference == "request-42"
    assert requirements[0].to_test_case().action == "export a report"
