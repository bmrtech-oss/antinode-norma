import json
from pathlib import Path

import openpyxl
from click.testing import CliRunner

from antinode_aegis.evidence import validate_matrix
from antinode_aegis.shared_ir import normalize_requirements
from antinode_norma.cli import cli


def test_phase2_ingest_contract_is_consistent_across_sources_and_cli(tmp_path) -> None:
    csv_source = tmp_path / "requirements.csv"
    csv_source.write_text("ID,Summary,Action\nCSV-001,Export report,export\n", encoding="utf-8")

    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = "Requirements"
    worksheet.append(["ID", "Summary", "Action"])
    worksheet.append(["XLSX-001", "Reset password", "reset"])
    xlsx_source = tmp_path / "requirements.xlsx"
    workbook.save(xlsx_source)

    story = {"story_id": "STORY-001", "title": "Audit users", "action": "audit"}
    csv_ir = normalize_requirements(csv_source, "csv")
    xlsx_ir = normalize_requirements(xlsx_source, "xlsx", sheet_name="Requirements")
    story_ir = normalize_requirements(story, "story", source_reference="integration")

    assert [item.provenance.source_kind for item in csv_ir + xlsx_ir + story_ir] == [
        "csv",
        "xlsx",
        "story",
    ]
    assert [item.requirement_id for item in csv_ir + xlsx_ir + story_ir] == [
        "CSV-001",
        "XLSX-001",
        "STORY-001",
    ]
    assert xlsx_ir[0].provenance.source_reference == f"{xlsx_source}#Requirements"
    assert story_ir[0].provenance.source_reference == "integration"

    cli_result = CliRunner().invoke(cli, ["aegis", "normalize", str(csv_source), "--kind", "csv"])
    assert cli_result.exit_code == 0, cli_result.output
    assert json.loads(cli_result.output)[0]["requirement_id"] == "CSV-001"

    matrix_path = Path(__file__).resolve().parents[2] / "docs" / "adr" / "evidence-matrix.yml"
    assert validate_matrix(matrix_path) == []
