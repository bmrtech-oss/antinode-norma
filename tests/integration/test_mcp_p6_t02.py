import json

import pytest

from antinode_norma.server.mcp_server import call_tool, list_tools


@pytest.mark.asyncio
async def test_mcp_tool_contract_end_to_end(tmp_path):
    tools = await list_tools()
    tool_names = {tool.name for tool in tools}
    assert {
        "generate_from_csv",
        "generate_from_xlsx",
        "run_quality_gates",
        "assess_story",
    } <= tool_names

    csv_path = tmp_path / "cases.csv"
    csv_path.write_text("ID,Summary\nTC-601,Reset password\n", encoding="utf-8")
    generated = await call_tool(
        "generate_from_csv",
        {"csv_path": str(csv_path), "output_dir": str(tmp_path / "features")},
    )
    generated_data = json.loads(generated[0].text)
    assert generated_data["test_cases"] == 1
    assert (tmp_path / "features" / "cases.feature").exists()

    quality = await call_tool(
        "run_quality_gates",
        {
            "gherkin_text": "Feature: MCP\n  Scenario: Contract\n    Given the tool is available"
        },
    )
    quality_data = json.loads(quality[0].text)
    assert {"verdict", "hard_pass", "soft_score", "sem_score"} <= quality_data.keys()

    assessment = await call_tool(
        "assess_story",
        {
            "role": "user",
            "action": "reset password",
            "benefit": "regain access",
            "acceptance_criteria": ["The system sends a reset link"],
        },
    )
    assessment_data = json.loads(assessment[0].text)
    assert {"passes_invest", "quality_score", "invest_details"} <= assessment_data.keys()
