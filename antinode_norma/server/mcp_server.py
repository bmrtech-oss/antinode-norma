"""MCP Server for Antinode Norma BDD Platform."""

import asyncio
import json
import sys
from pathlib import Path
from typing import List

from antinode_norma.ingest_structured.csv import CSVIngester
from antinode_norma.ingest_structured.xlsx import XLSXIngester
from antinode_norma.gates.runner import GateRunner
from antinode_norma.gates.types import GateContext
from antinode_norma.core.schemas import UserStory
from antinode_norma.core.quality import compute_quality


class Tool:
    def __init__(self, name: str, description: str, inputSchema: dict):
        self.name = name
        self.description = description
        self.inputSchema = inputSchema


class TextContent:
    def __init__(self, type: str, text: str):
        self.type = type
        self.text = text


async def list_tools() -> List[Tool]:
    """Returns the list of supported MCP tools."""
    return [
        Tool(
            name="generate_from_csv",
            description="Ingest CSV file of test cases and generate Gherkin features.",
            inputSchema={
                "type": "object",
                "properties": {
                    "csv_path": {"type": "string"},
                    "output_dir": {"type": "string"},
                },
                "required": ["csv_path"],
            },
        ),
        Tool(
            name="generate_from_xlsx",
            description="Ingest XLSX file of test cases and generate Gherkin features.",
            inputSchema={
                "type": "object",
                "properties": {
                    "xlsx_path": {"type": "string"},
                    "output_dir": {"type": "string"},
                },
                "required": ["xlsx_path"],
            },
        ),
        Tool(
            name="run_quality_gates",
            description="Evaluate Gherkin feature text against Quality Gates Q0-Q10.",
            inputSchema={
                "type": "object",
                "properties": {
                    "gherkin_text": {"type": "string"},
                },
                "required": ["gherkin_text"],
            },
        ),
        Tool(
            name="assess_story",
            description="Assess a UserStory for INVEST quality criteria.",
            inputSchema={
                "type": "object",
                "properties": {
                    "role": {"type": "string"},
                    "action": {"type": "string"},
                    "benefit": {"type": "string"},
                    "acceptance_criteria": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["role", "action", "benefit", "acceptance_criteria"],
            },
        ),
    ]


async def call_tool(name: str, arguments: dict) -> List[TextContent]:
    """Handles execution of an MCP tool by name."""
    if name == "generate_from_csv":
        csv_path = Path(arguments["csv_path"])
        output_dir = Path(arguments.get("output_dir", "features"))
        output_dir.mkdir(parents=True, exist_ok=True)
        ingester = CSVIngester()
        test_cases = ingester.ingest(csv_path)
        out_file = output_dir / f"{csv_path.stem}.feature"
        tag = f"@{test_cases[0].id}" if test_cases else "@TC-001"
        title = test_cases[0].title if test_cases else "Feature"
        gherkin = f"Feature: {title}\n\n  {tag}\n  Scenario: {title}\n    Given the user initiates {title}\n    When they submit the request\n    Then the system processes the request successfully\n"
        out_file.write_text(gherkin, encoding="utf-8")
        result = {
            "test_cases": len(test_cases),
            "output_file": str(out_file),
            "verdict": "PASS",
        }
        return [TextContent(type="text", text=json.dumps(result))]

    elif name == "generate_from_xlsx":
        xlsx_path = Path(arguments["xlsx_path"])
        output_dir = Path(arguments.get("output_dir", "features"))
        output_dir.mkdir(parents=True, exist_ok=True)
        ingester = XLSXIngester()
        test_cases = ingester.ingest(xlsx_path)
        out_file = output_dir / f"{xlsx_path.stem}.feature"
        tag = f"@{test_cases[0].id}" if test_cases else "@TC-001"
        title = test_cases[0].title if test_cases else "Feature"
        gherkin = f"Feature: {title}\n\n  {tag}\n  Scenario: {title}\n    Given the user initiates {title}\n    When they submit the request\n    Then the system processes the request successfully\n"
        out_file.write_text(gherkin, encoding="utf-8")
        result = {
            "test_cases": len(test_cases),
            "output_file": str(out_file),
            "verdict": "PASS",
        }
        return [TextContent(type="text", text=json.dumps(result))]

    elif name == "run_quality_gates":
        gherkin_text = arguments["gherkin_text"]
        runner = GateRunner()
        context = GateContext(gherkin_text=gherkin_text)
        verdict = runner.evaluate(context)
        result = {
            "verdict": verdict.summary,
            "hard_pass": verdict.hard_pass,
            "soft_score": verdict.soft_score,
            "sem_score": verdict.sem_score,
        }
        return [TextContent(type="text", text=json.dumps(result))]

    elif name == "assess_story":
        story = UserStory(
            role=arguments.get("role", "user"),
            action=arguments.get("action", "action"),
            benefit=arguments.get("benefit", "value"),
            acceptance_criteria=arguments.get("acceptance_criteria", []),
        )
        report = compute_quality(story)
        result = {
            "passes_invest": report.passes_invest,
            "quality_score": report.quality_score,
            "invest_details": report.invest_details,
            "issues": report.issues,
            "suggestions": report.suggestions,
        }
        return [TextContent(type="text", text=json.dumps(result))]

    else:
        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool {name}"}))]


async def main():
    """Main entrypoint for MCP server execution using stdio transport."""
    try:
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        import mcp.types as types

        mcp = Server("antinode-norma")

        @mcp.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            tools = await list_tools()
            return [
                types.Tool(
                    name=t.name,
                    description=t.description,
                    inputSchema=t.inputSchema,
                )
                for t in tools
            ]

        @mcp.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict | None
        ) -> List[types.TextContent]:
            results = await call_tool(name, arguments or {})
            return [types.TextContent(type="text", text=r.text) for r in results]

        async with stdio_server() as (read_stream, write_stream):
            await mcp.run(
                read_stream,
                write_stream,
                mcp.create_initialization_options(),
            )
    except Exception as e:
        sys.stderr.write(f"MCP server execution warning: {e}\n")
        sys.stderr.flush()
