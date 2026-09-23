from antinode_aegis.csv import ingest_csv


def test_ingest_csv_returns_versioned_ir_with_provenance(tmp_path) -> None:
    csv_file = tmp_path / "requirements.csv"
    csv_file.write_text(
        "Case ID,Summary,As a,I want to,So that,Acceptance Criteria,Labels\n"
        "TC-101,Login Test,user,log in,access app,Valid credentials succeed; Error shown,smoke;auth\n",
        encoding="utf-8",
    )

    requirements = ingest_csv(csv_file)

    assert len(requirements) == 1
    requirement = requirements[0]
    assert requirement.requirement_id == "TC-101"
    assert requirement.title == "Login Test"
    assert requirement.acceptance_criteria == ["Valid credentials succeed", "Error shown"]
    assert requirement.tags == ["smoke", "auth"]
    assert requirement.provenance.source_kind == "csv"
    assert requirement.provenance.source_reference == str(csv_file)


def test_ingest_csv_preserves_missing_file_error(tmp_path) -> None:
    missing = tmp_path / "missing.csv"

    try:
        ingest_csv(missing)
    except FileNotFoundError as exc:
        assert str(missing) in str(exc)
    else:
        raise AssertionError("missing CSV files must raise FileNotFoundError")
