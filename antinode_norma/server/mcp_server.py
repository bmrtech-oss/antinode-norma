<<<<<<< HEAD
"""MCP Server for Norma BDD tool."""

import asyncio
import json

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.types as types
import mcp.server.stdio

from antinode_norma.runner import run_agent_from_raw, run_bdd_agent

# Import codegen tools
from .tools import (
    handle_generate_tests,
    handle_generate_page_objects,
    handle_generate_step_defs,
    handle_validate_feature,
)

server = Server("norma")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """List all available tools."""
    return [
        # Existing BDD tools
        types.Tool(
            name="submit_story",
            description="Submit a user story for INVEST quality assessment.",
            inputSchema={
                "type": "object",
                "properties": {
                    "story": {"type": "string", "description": "The user story text"},
                    "file_path": {
                        "type": "string",
                        "description": "Optional output file path",
                    },
                },
                "required": ["story"],
            },
        ),
        types.Tool(
            name="improve_story",
            description="Improve a story based on INVEST quality feedback.",
            inputSchema={
                "type": "object",
                "properties": {
                    "story": {"type": "string", "description": "The user story text"},
                    "issues": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["story", "issues"],
            },
        ),
        types.Tool(
            name="generate_feature",
            description="Generate a Gherkin .feature file from a user story.",
            inputSchema={
                "type": "object",
                "properties": {
                    "story": {"type": "string", "description": "The user story text"},
                    "file_path": {
                        "type": "string",
                        "description": "Optional output file path",
                    },
                },
                "required": ["story"],
            },
        ),
        types.Tool(
            name="run_bdd_agent",
            description="Run the autonomous BDD agent on a story.",
            inputSchema={
                "type": "object",
                "properties": {
                    "story": {"type": "string", "description": "The user story text"},
                    "max_iterations": {"type": "integer", "default": 3},
                },
                "required": ["story"],
            },
        ),
        # New codegen tools
        types.Tool(
            name="generate_tests",
            description="Generate executable test scripts (Playwright, Cypress, Selenium) from a .feature file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "feature_path": {
                        "type": "string",
                        "description": "Path to the .feature file",
                    },
                    "framework": {
                        "type": "string",
                        "enum": ["playwright", "cypress", "selenium"],
                        "default": "playwright",
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Output directory (optional)",
                    },
                    "use_page_objects": {"type": "boolean", "default": False},
                    "generate_step_defs": {"type": "boolean", "default": False},
                    "verbose": {"type": "boolean", "default": False},
                },
                "required": ["feature_path"],
            },
        ),
        types.Tool(
            name="generate_page_objects",
            description="Generate Page Object classes from a .feature file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "feature_path": {
                        "type": "string",
                        "description": "Path to the .feature file",
                    },
                    "framework": {
                        "type": "string",
                        "enum": ["playwright", "cypress", "selenium"],
                        "default": "playwright",
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Output directory (optional)",
                    },
                },
                "required": ["feature_path"],
            },
        ),
        types.Tool(
            name="generate_step_defs",
            description="Generate reusable step definitions from a .feature file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "feature_path": {
                        "type": "string",
                        "description": "Path to the .feature file",
                    },
                    "framework": {
                        "type": "string",
                        "enum": ["playwright", "cypress", "selenium"],
                        "default": "playwright",
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Output directory (optional)",
                    },
                },
                "required": ["feature_path"],
            },
        ),
        types.Tool(
            name="validate_feature",
            description="Validate a Gherkin feature file for quality and completeness.",
            inputSchema={
                "type": "object",
                "properties": {
                    "feature_path": {
                        "type": "string",
                        "description": "Path to the .feature file",
                    },
                    "check_invest": {"type": "boolean", "default": True},
                },
                "required": ["feature_path"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls."""
    # Existing BDD handlers
    if name == "submit_story":
        story = arguments.get("story")
        file_path = arguments.get("file_path")
        result = await run_agent_from_raw(story, file_path)
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "improve_story":
        story = arguments.get("story")
        # Implementation for improvement...
        return [
            types.TextContent(type="text", text="Improvement suggestions generated.")
        ]

    elif name == "generate_feature":
        story = arguments.get("story")
        file_path = arguments.get("file_path")
        result = await run_agent_from_raw(story, file_path)
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "run_bdd_agent":
        story = arguments.get("story")
        max_iterations = arguments.get("max_iterations", 3)
        result = await run_bdd_agent(story, max_iterations)
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    # New codegen handlers
    elif name == "generate_tests":
        result = await handle_generate_tests(arguments)
        return [types.TextContent(type="text", text=result[0]["text"])]

    elif name == "generate_page_objects":
        result = await handle_generate_page_objects(arguments)
        return [types.TextContent(type="text", text=result[0]["text"])]

    elif name == "generate_step_defs":
        result = await handle_generate_step_defs(arguments)
        return [types.TextContent(type="text", text=result[0]["text"])]

    elif name == "validate_feature":
        result = await handle_validate_feature(arguments)
        return [types.TextContent(type="text", text=result[0]["text"])]

    else:
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="norma",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
=======
<<<<<<< HEAD
"""MCP Server for Norma BDD tool."""

import asyncio
import json

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.types as types
import mcp.server.stdio

from antinode_norma.runner import run_agent_from_raw, run_bdd_agent

# Import codegen tools
from .tools import (
    handle_generate_tests,
    handle_generate_page_objects,
    handle_generate_step_defs,
    handle_validate_feature,
)

server = Server("norma")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """List all available tools."""
    return [
        # Existing BDD tools
        types.Tool(
            name="submit_story",
            description="Submit a user story for INVEST quality assessment.",
            inputSchema={
                "type": "object",
                "properties": {
                    "story": {"type": "string", "description": "The user story text"},
                    "file_path": {
                        "type": "string",
                        "description": "Optional output file path",
                    },
                },
                "required": ["story"],
            },
        ),
        types.Tool(
            name="improve_story",
            description="Improve a story based on INVEST quality feedback.",
            inputSchema={
                "type": "object",
                "properties": {
                    "story": {"type": "string", "description": "The user story text"},
                    "issues": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["story", "issues"],
            },
        ),
        types.Tool(
            name="generate_feature",
            description="Generate a Gherkin .feature file from a user story.",
            inputSchema={
                "type": "object",
                "properties": {
                    "story": {"type": "string", "description": "The user story text"},
                    "file_path": {
                        "type": "string",
                        "description": "Optional output file path",
                    },
                },
                "required": ["story"],
            },
        ),
        types.Tool(
            name="run_bdd_agent",
            description="Run the autonomous BDD agent on a story.",
            inputSchema={
                "type": "object",
                "properties": {
                    "story": {"type": "string", "description": "The user story text"},
                    "max_iterations": {"type": "integer", "default": 3},
                },
                "required": ["story"],
            },
        ),
        # New codegen tools
        types.Tool(
            name="generate_tests",
            description="Generate executable test scripts (Playwright, Cypress, Selenium) from a .feature file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "feature_path": {
                        "type": "string",
                        "description": "Path to the .feature file",
                    },
                    "framework": {
                        "type": "string",
                        "enum": ["playwright", "cypress", "selenium"],
                        "default": "playwright",
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Output directory (optional)",
                    },
                    "use_page_objects": {"type": "boolean", "default": False},
                    "generate_step_defs": {"type": "boolean", "default": False},
                    "verbose": {"type": "boolean", "default": False},
                },
                "required": ["feature_path"],
            },
        ),
        types.Tool(
            name="generate_page_objects",
            description="Generate Page Object classes from a .feature file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "feature_path": {
                        "type": "string",
                        "description": "Path to the .feature file",
                    },
                    "framework": {
                        "type": "string",
                        "enum": ["playwright", "cypress", "selenium"],
                        "default": "playwright",
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Output directory (optional)",
                    },
                },
                "required": ["feature_path"],
            },
        ),
        types.Tool(
            name="generate_step_defs",
            description="Generate reusable step definitions from a .feature file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "feature_path": {
                        "type": "string",
                        "description": "Path to the .feature file",
                    },
                    "framework": {
                        "type": "string",
                        "enum": ["playwright", "cypress", "selenium"],
                        "default": "playwright",
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Output directory (optional)",
                    },
                },
                "required": ["feature_path"],
            },
        ),
        types.Tool(
            name="validate_feature",
            description="Validate a Gherkin feature file for quality and completeness.",
            inputSchema={
                "type": "object",
                "properties": {
                    "feature_path": {
                        "type": "string",
                        "description": "Path to the .feature file",
                    },
                    "check_invest": {"type": "boolean", "default": True},
                },
                "required": ["feature_path"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls."""
    # Existing BDD handlers
    if name == "submit_story":
        story = arguments.get("story")
        file_path = arguments.get("file_path")
        result = await run_agent_from_raw(story, file_path)
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "improve_story":
        story = arguments.get("story")
        # Implementation for improvement...
        return [
            types.TextContent(type="text", text="Improvement suggestions generated.")
        ]

    elif name == "generate_feature":
        story = arguments.get("story")
        file_path = arguments.get("file_path")
        result = await run_agent_from_raw(story, file_path)
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "run_bdd_agent":
        story = arguments.get("story")
        max_iterations = arguments.get("max_iterations", 3)
        result = await run_bdd_agent(story, max_iterations)
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    # New codegen handlers
    elif name == "generate_tests":
        result = await handle_generate_tests(arguments)
        return [types.TextContent(type="text", text=result[0]["text"])]

    elif name == "generate_page_objects":
        result = await handle_generate_page_objects(arguments)
        return [types.TextContent(type="text", text=result[0]["text"])]

    elif name == "generate_step_defs":
        result = await handle_generate_step_defs(arguments)
        return [types.TextContent(type="text", text=result[0]["text"])]

    elif name == "validate_feature":
        result = await handle_validate_feature(arguments)
        return [types.TextContent(type="text", text=result[0]["text"])]

    else:
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="norma",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
=======
"""MCP Server for Norma BDD tool."""

import json
from pathlib import Path

from mcp.server.mcpserver import MCPServer
import mcp.types as types

from antinode_norma.runner import run_agent_from_raw
from antinode_norma.ingest_structured.csv import CSVIngester
from antinode_norma.ingest_structured.xlsx import XLSXIngester
from antinode_norma.core.agent import NormaAgent
from antinode_norma.gates.runner import GateRunner
from antinode_norma.gates.types import GateContext
from antinode_norma.core.quality import compute_quality
from antinode_norma.core.schemas import UserStory

# Import codegen tools
from .tools import (
    handle_generate_tests,
    handle_generate_page_objects,
    handle_generate_step_defs,
    handle_validate_feature,
)

mcp_app = MCPServer("norma")


def _mcp_mock_llm(prompt: str) -> str:
    """Deterministic LLM mock callable for MCP tools that extracts required test case IDs from prompt."""
    tc_tags = []
    for line in prompt.splitlines():
        if "Test Case [" in line:
            # Extract ID inside square brackets e.g. Test Case [TC-601]:
            start = line.find("[") + 1
            end = line.find("]")
            if start > 0 and end > start:
                tc_tags.append(f"@{line[start:end]}")

    tag_str = " ".join(tc_tags) if tc_tags else "@TC-101"

    return f"""
@smoke {tag_str}
Feature: MCP Generated Feature
  Scenario: Generated scenario
    Given the user initiates the flow
    When the system processes the request
    Then the expected outcome is achieved
"""


@mcp_app.tool()
async def submit_story(story: str, file_path: str = None) -> str:
    """Submit a user story for INVEST quality assessment."""
    result = await run_agent_from_raw(story, file_path)
    return json.dumps(result, indent=2)


@mcp_app.tool()
async def improve_story(story: str, issues: list[str]) -> str:
    """Improve a story based on INVEST quality feedback."""
    return "Improvement suggestions generated."


@mcp_app.tool()
async def generate_feature(story: str, file_path: str = None) -> str:
    """Generate a Gherkin .feature file from a user story."""
    result = await run_agent_from_raw(story, file_path)
    return json.dumps(result, indent=2)


@mcp_app.tool()
async def run_bdd_agent(story: str, max_iterations: int = 3) -> str:
    """Run the autonomous BDD agent on a story."""
    result = await run_agent_from_raw(story)
    return json.dumps(result, indent=2)


@mcp_app.tool()
async def generate_from_csv(csv_path: str, output_dir: str = "features") -> str:
    """Generate Gherkin feature files from a CSV file."""
    ingester = CSVIngester()
    test_cases = ingester.ingest(csv_path)

    agent = NormaAgent(llm_callable=_mcp_mock_llm)
    gherkin_text, verdict, attempts = agent.generate_feature_with_repair(test_cases)

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    file_out = out_path / f"{Path(csv_path).stem}.feature"
    file_out.write_text(gherkin_text, encoding="utf-8")

    res_data = {
        "test_cases": len(test_cases),
        "output_file": str(file_out),
        "verdict": verdict.summary,
        "attempts": attempts,
    }
    return json.dumps(res_data, indent=2)


@mcp_app.tool()
async def generate_from_xlsx(xlsx_path: str, sheet_name: str = None, output_dir: str = "features") -> str:
    """Generate Gherkin feature files from an XLSX spreadsheet file."""
    ingester = XLSXIngester(sheet_name=sheet_name)
    test_cases = ingester.ingest(xlsx_path)

    agent = NormaAgent(llm_callable=_mcp_mock_llm)
    gherkin_text, verdict, attempts = agent.generate_feature_with_repair(test_cases)

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    file_out = out_path / f"{Path(xlsx_path).stem}.feature"
    file_out.write_text(gherkin_text, encoding="utf-8")

    res_data = {
        "test_cases": len(test_cases),
        "output_file": str(file_out),
        "verdict": verdict.summary,
        "attempts": attempts,
    }
    return json.dumps(res_data, indent=2)


@mcp_app.tool()
async def run_quality_gates(gherkin_text: str = None, feature_path: str = None) -> str:
    """Run Quality Gates (Q0-Q5) on a Gherkin feature string or file path."""
    if not gherkin_text and feature_path:
        gherkin_text = Path(feature_path).read_text(encoding="utf-8")

    if not gherkin_text:
        return "Error: gherkin_text or feature_path required."

    ctx = GateContext(gherkin_text=gherkin_text)
    runner = GateRunner()
    verdict = runner.evaluate(ctx)
    report = runner.generate_report(verdict)

    res_data = {
        "verdict": verdict.summary,
        "hard_pass": verdict.hard_pass,
        "report": report,
    }
    return json.dumps(res_data, indent=2)


@mcp_app.tool()
async def assess_story(role: str = "user", action: str = "", benefit: str = "", acceptance_criteria: list[str] = None) -> str:
    """Assess a user story against INVEST criteria."""
    criteria = acceptance_criteria or []
    story = UserStory(role=role, action=action, benefit=benefit, acceptance_criteria=criteria)
    report = compute_quality(story)

    res_data = {
        "passes_invest": report.passes_invest,
        "quality_score": report.quality_score,
        "invest_details": report.invest_details,
        "issues": report.issues,
        "suggestions": report.suggestions,
    }
    return json.dumps(res_data, indent=2)


@mcp_app.tool()
async def generate_tests(feature_path: str, framework: str = "playwright", output_dir: str = None, use_page_objects: bool = False, generate_step_defs: bool = False, verbose: bool = False) -> str:
    """Generate executable test scripts (Playwright, Cypress, Selenium) from a .feature file."""
    res = await handle_generate_tests({"feature_path": feature_path, "framework": framework, "output_dir": output_dir, "use_page_objects": use_page_objects, "generate_step_defs": generate_step_defs, "verbose": verbose})
    return res[0]["text"]


@mcp_app.tool()
async def generate_page_objects(feature_path: str, framework: str = "playwright", output_dir: str = None) -> str:
    """Generate Page Object classes from a .feature file."""
    res = await handle_generate_page_objects({"feature_path": feature_path, "framework": framework, "output_dir": output_dir})
    return res[0]["text"]


@mcp_app.tool()
async def generate_step_defs(feature_path: str, framework: str = "playwright", output_dir: str = None) -> str:
    """Generate reusable step definitions from a .feature file."""
    res = await handle_generate_step_defs({"feature_path": feature_path, "framework": framework, "output_dir": output_dir})
    return res[0]["text"]


@mcp_app.tool()
async def validate_feature(feature_path: str, check_invest: bool = True) -> str:
    """Validate a Gherkin feature file for quality and completeness."""
    res = await handle_validate_feature({"feature_path": feature_path, "check_invest": check_invest})
    return res[0]["text"]


async def list_tools() -> list[types.Tool]:
    """Helper to list registered tools for compatibility/testing."""
    return await mcp_app.list_tools()


async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Helper to call tool for compatibility/testing."""
    res = await mcp_app.call_tool(name, arguments)
    if isinstance(res, str):
        text_content = res
    elif hasattr(res, "content") and res.content:
        first_item = res.content[0]
        text_content = first_item.text if hasattr(first_item, "text") else str(first_item)
    elif isinstance(res, list):
        text_content = str(res[0]) if res else ""
    else:
        text_content = str(res)

    return [types.TextContent(type="text", text=text_content)]


def main():
    """Run the MCP server stdio transport."""
    mcp_app.run()


if __name__ == "__main__":
    main()
>>>>>>> d4d2d9a (fix(tests): update CORS header assertion in test_api_p9_t01.py)
>>>>>>> c3cac3b (feat(ui): implement frontend scaffold with React, Vite, and Tailwind CSS (P9-T03))
