import json

from click.testing import CliRunner

from antinode_norma.cli import cli


def test_aegis_normalize_cli_emits_versioned_csv_ir(tmp_path) -> None:
    source = tmp_path / "requirements.csv"
    source.write_text("ID,Summary,Action\nCSV-001,Export report,export\n", encoding="utf-8")

    result = CliRunner().invoke(cli, ["aegis", "normalize", str(source), "--kind", "csv"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload[0]["requirement_id"] == "CSV-001"
    assert payload[0]["provenance"]["source_kind"] == "csv"


def test_aegis_normalize_cli_accepts_story_json() -> None:
    story = json.dumps({"story_id": "STORY-001", "action": "export report"})

    result = CliRunner().invoke(
        cli,
        ["aegis", "normalize", story, "--kind", "story", "--source-reference", "cli-input"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload[0]["requirement_id"] == "STORY-001"
    assert payload[0]["provenance"]["source_reference"] == "cli-input"


def test_aegis_normalize_cli_reports_invalid_story_json() -> None:
    result = CliRunner().invoke(cli, ["aegis", "normalize", "{invalid", "--kind", "story"])

    assert result.exit_code != 0
    assert "Unable to normalize story input" in result.output
