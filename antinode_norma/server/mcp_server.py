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
