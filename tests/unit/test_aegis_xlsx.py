import openpyxl

from antinode_aegis.xlsx import ingest_xlsx


def test_ingest_xlsx_returns_versioned_ir_for_selected_worksheet(tmp_path) -> None:
    workbook = openpyxl.Workbook()
    first = workbook.active
    first.title = "Other"
    first.append(["ID", "Summary", "Role", "Goal", "Outcome", "Criteria", "Tags"])
    first.append(["WRONG", "Wrong sheet", "user", "ignore", "ignore", "ignore", "ignore"])
    selected = workbook.create_sheet("Requirements")
    selected.append(["Test ID", "Name", "Role", "Action", "Benefit", "Acceptance Criteria", "Labels"])
    selected.append(["TC-201", "Reset Password", "user", "reset password", "regain access", "Email sent", "auth"])
    source = tmp_path / "requirements.xlsx"
    workbook.save(source)

    requirements = ingest_xlsx(source, sheet_name="Requirements")

    assert len(requirements) == 1
    requirement = requirements[0]
    assert requirement.requirement_id == "TC-201"
    assert requirement.title == "Reset Password"
    assert requirement.provenance.source_kind == "xlsx"
    assert requirement.provenance.source_reference == f"{source}#Requirements"


def test_ingest_xlsx_preserves_missing_file_error(tmp_path) -> None:
    missing = tmp_path / "missing.xlsx"

    try:
        ingest_xlsx(missing)
    except FileNotFoundError as exc:
        assert str(missing) in str(exc)
    else:
        raise AssertionError("missing XLSX files must raise FileNotFoundError")
