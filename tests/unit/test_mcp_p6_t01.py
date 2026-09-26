import pytest
import json
import subprocess
import sys
from antinode_norma.server.mcp_server import list_tools, call_tool


@pytest.mark.asyncio
async def test_mcp_list_tools_registered():
    tools = await list_tools()
    tool_names = [t.name for t in tools]

    assert "generate_from_csv" in tool_names
    assert "generate_from_xlsx" in tool_names
    assert "run_quality_gates" in tool_names
    assert "assess_story" in tool_names


def test_mcp_module_serves_stdio_requests():
    requests = "\n".join(
        [
            json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0"},
                },
            }),
            json.dumps({
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {},
            }),
            json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}),
        ]
    ) + "\n"
    completed = subprocess.run(
        [sys.executable, "-m", "antinode_norma.server.mcp_server"],
        input=requests,
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )

    responses = [json.loads(line) for line in completed.stdout.splitlines()]
    assert responses[0]["id"] == 1
    assert responses[1]["id"] == 2
    assert {tool["name"] for tool in responses[1]["result"]["tools"]} >= {
        "generate_from_csv",
        "assess_story",
    }


@pytest.mark.asyncio
async def test_mcp_call_run_quality_gates():
    gherkin = """
Feature: MCP Test
  Scenario: Test quality gate tool
    Given user runs test
"""
    result = await call_tool("run_quality_gates", {"gherkin_text": gherkin})
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert "verdict" in data
    assert "hard_pass" in data


@pytest.mark.asyncio
async def test_mcp_call_generate_from_csv(tmp_path):
    csv_file = tmp_path / "cases.csv"
    csv_file.write_text("ID,Summary\nTC-501,MCP CSV Test\n")

    out_dir = tmp_path / "features"
    result = await call_tool("generate_from_csv", {
        "csv_path": str(csv_file),
        "output_dir": str(out_dir),
    })

    assert len(result) == 1
    data = json.loads(result[0].text)
    assert data["test_cases"] == 1
    assert "output_file" in data


@pytest.mark.asyncio
async def test_mcp_call_assess_story():
    result = await call_tool("assess_story", {
        "role": "shopper",
        "action": "checkout cart",
        "benefit": "receive goods",
        "acceptance_criteria": ["system displays summary screen"],
    })

    assert len(result) == 1
    data = json.loads(result[0].text)
    assert "passes_invest" in data
    assert "quality_score" in data
    assert "invest_details" in data
