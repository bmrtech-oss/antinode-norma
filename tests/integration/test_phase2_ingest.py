import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from antinode_norma.cli import cli


@pytest.fixture(autouse=True)
def mock_llm_calls_for_cli():
    with patch("antinode_norma.agent_tools.create_llm_callable", return_value=MagicMock(return_value="Feature: Test\nScenario: Test\nGiven something")):
        yield


def test_phase2_integration_generate_from_csv(tmp_path):
    csv_file = tmp_path / "cases.csv"
    csv_file.write_text(
        "ID,Summary,As a,I want to,So that,Acceptance Criteria\n"
        "TC-999,CSV Generation,registered user,log in using credentials,access dashboard,Displays welcome dashboard; Shows invalid error message\n"
    )

    out_dir = tmp_path / "features"
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "generate-from-csv",
            str(csv_file),
            "--output-dir",
            str(out_dir),
        ],
    )

    assert result.exit_code == 0
    assert "Ingested 1 test cases" in result.output
    assert out_dir.exists()
    feature_files = list(out_dir.glob("*.feature"))
    assert len(feature_files) == 1
    content = feature_files[0].read_text()
    assert "Feature:" in content or "Scenario:" in content


def test_phase2_integration_generate_from_xlsx(tmp_path):
    import openpyxl

    xlsx_file = tmp_path / "cases.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["ID", "Summary", "As a", "I want to", "So that", "Acceptance Criteria"])
    ws.append(["TC-888", "XLSX Generation", "admin", "export report", "analyze metrics", "Exports CSV file; Shows download prompt"])
    wb.save(xlsx_file)

    out_dir = tmp_path / "features"
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "generate-from-xlsx",
            str(xlsx_file),
            "--output-dir",
            str(out_dir),
        ],
    )

    assert result.exit_code == 0
    assert "Ingested 1 test cases" in result.output
    assert out_dir.exists()
    feature_files = list(out_dir.glob("*.feature"))
    assert len(feature_files) == 1
