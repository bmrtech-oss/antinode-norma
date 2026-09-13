import pytest
from antinode_norma.server.mcp_server import list_tools_handler
import mcp.types as types


@pytest.mark.asyncio
async def test_mcp_contract_registered_tools():
    req = types.ListToolsRequest(method="tools/list")
    res = await list_tools_handler(req)
    tool_names = {t.name for t in res.tools}
    expected_tools = {
        "submit_story",
        "improve_story",
        "generate_feature",
        "run_bdd_agent",
        "generate_tests",
        "generate_page_objects",
        "generate_step_defs",
        "validate_feature",
    }
    assert expected_tools.issubset(tool_names), f"Missing MCP tools: {expected_tools - tool_names}"


@pytest.mark.asyncio
async def test_mcp_contract_submit_story_schema():
    req = types.ListToolsRequest(method="tools/list")
    res = await list_tools_handler(req)
    submit_tool = next(t for t in res.tools if t.name == "submit_story")
    schema = getattr(submit_tool, "input_schema", getattr(submit_tool, "inputSchema", None))
    assert schema is not None
    assert "story" in schema["properties"]
    assert "story" in schema["required"]
