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


def test_shared_ir_dispatches_xlsx_with_worksheet_provenance(tmp_path) -> None:
    import openpyxl

    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = "Requirements"
    worksheet.append(["ID", "Summary", "Role", "Action", "Benefit"])
    worksheet.append(["XLSX-001", "Export report", "analyst", "export", "share findings"])
    source = tmp_path / "requirements.xlsx"
    workbook.save(source)

    requirements = normalize_requirements(source, "excel", sheet_name="Requirements")

    assert requirements[0].requirement_id == "XLSX-001"
    assert requirements[0].provenance.source_reference == f"{source}#Requirements"


def test_shared_ir_rejects_unsupported_kinds() -> None:
    try:
        normalize_requirements([], "xml")
    except ValueError as exc:
        assert "Unsupported ingest kind" in str(exc)
    else:
        raise AssertionError("unsupported ingest kinds must fail explicitly")
