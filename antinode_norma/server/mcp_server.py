import asyncio
import json
import uuid
import os
from typing import Dict, List, Optional
from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

from ..core.schemas import UserStory
from ..core.quality import compute_quality
from ..core.parser import parse_story
from ..core.gherkin_generator import generate_gherkin
from ..core.validator import validate_gherkin
from ..utils.llm_factory import create_llm_callable
from ..utils.file_writer import write_feature_file
from ..agent import BDDAgent
from ..agent_tools import (
    fetch_jira_story,
    submit_story as agent_submit_story,
    improve_story as agent_improve_story,
    generate_feature as agent_generate_feature,
    run_tests,
    fix_feature,
    create_pr,
    comment_on_jira,
)

# LLM Configuration
LLM_CONFIG = {
    "provider": os.getenv("LLM_PROVIDER", "openrouter"),
    "api_key": os.getenv("OPENROUTER_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY"),
    "model": os.getenv("LLM_MODEL", "openai/gpt-oss-120b:free"),
    "base_url": os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1"),
    "temperature": float(os.getenv("LLM_TEMPERATURE", "0.2")),
    "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "1024")),
    "url": os.getenv("LLM_URL")
}
llm_call = create_llm_callable(LLM_CONFIG)

# In‑memory story store
stories: Dict[str, UserStory] = {}

# Agent tool registry
AGENT_TOOLS = {
    "fetch_jira_story": fetch_jira_story,
    "submit_story": agent_submit_story,
    "improve_story": agent_improve_story,
    "generate_feature": agent_generate_feature,
    "run_tests": run_tests,
    "fix_feature": fix_feature,
    "create_pr": create_pr,
    "comment_on_jira": comment_on_jira,
}

# ------------------------------
# Tool Handlers (common logic)
# ------------------------------

async def handle_submit_story(arguments: dict) -> list[types.TextContent]:
    try:
        story = UserStory(**arguments)
    except Exception as e:
        return [types.TextContent(type="text", text=f"Invalid story data: {e}")]
    story_id = str(uuid.uuid4())
    story.story_id = story_id
    stories[story_id] = story
    report = compute_quality(story)
    result = {
        "story_id": story_id,
        "quality_score": report.quality_score,
        "passes_invest": report.passes_invest,
        "issues": report.issues,
        "suggestions": report.suggestions
    }
    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

async def handle_improve_story(arguments: dict) -> list[types.TextContent]:
    story_id = arguments.get("story_id")
    suggestions = arguments.get("suggestions", [])
    if story_id not in stories:
        return [types.TextContent(type="text", text=f"Story {story_id} not found")]
    original = stories[story_id]
    prompt = f"""Improve this story based on suggestions:
{original.json(indent=2)}
Suggestions: {suggestions}
Return improved JSON matching the same schema."""
    improved_json = llm_call(prompt)
    if "```json" in improved_json:
        improved_json = improved_json.split("```json")[1].split("```")[0]
    elif "```" in improved_json:
        improved_json = improved_json.split("```")[1].split("```")[0]
    improved_data = json.loads(improved_json)
    improved_story = UserStory(**improved_data)
    improved_story.story_id = story_id
    stories[story_id] = improved_story
    return [types.TextContent(type="text", text=improved_json)]

async def handle_generate_feature(arguments: dict) -> list[types.TextContent]:
    story_id = arguments.get("story_id")
    step_defs = arguments.get("step_definitions", [])
    if story_id not in stories:
        return [types.TextContent(type="text", text=f"Story {story_id} not found")]
    story = stories[story_id]
    gherkin = generate_gherkin(story, step_defs, llm_call)
    validation = validate_gherkin(gherkin)
    if not validation.valid:
        return [types.TextContent(type="text", text=f"Validation failed: {validation.errors}")]
    safe_action = story.action.lower().replace(' ', '_')
    output_dir = os.getenv("NORMA_OUTPUT_DIR", "features")
    file_path = os.path.join(output_dir, f"{safe_action}.feature")
    write_feature_file(file_path, gherkin)
    result = {"feature_file_path": file_path, "validation_passed": True}
    return [types.TextContent(type="text", text=json.dumps(result))]

async def handle_run_bdd_agent(arguments: dict) -> list[types.TextContent]:
    goal = arguments.get("goal", "")
    agent = BDDAgent(LLM_CONFIG, AGENT_TOOLS)
    result = agent.run(goal)
    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

# ------------------------------
# MCP Server Setup (using @server.list_tools() and @server.call_tool())
# ------------------------------

async def main():
    server = Server("antinode-norma")

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="submit_story",
                description="Submit a user story and return a quality report.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "raw_text": {"type": "string"},
                        "role": {"type": "string"},
                        "action": {"type": "string"},
                        "benefit": {"type": "string"},
                        "acceptance_criteria": {"type": "array", "items": {"type": "string"}},
                        "dependencies": {"type": "array", "items": {"type": "string"}},
                        "estimated_points": {"type": "integer"}
                    },
                    "required": ["role", "action", "benefit", "acceptance_criteria"]
                }
            ),
            types.Tool(
                name="improve_story",
                description="Improve a story based on suggestions.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "story_id": {"type": "string"},
                        "suggestions": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["story_id", "suggestions"]
                }
            ),
            types.Tool(
                name="generate_feature",
                description="Generate a .feature file for a story.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "story_id": {"type": "string"},
                        "step_definitions": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["story_id"]
                }
            ),
            types.Tool(
                name="run_bdd_agent",
                description="Run the autonomous BDD agent with a high‑level goal.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "goal": {"type": "string"}
                    },
                    "required": ["goal"]
                }
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        if name == "submit_story":
            return await handle_submit_story(arguments)
        elif name == "improve_story":
            return await handle_improve_story(arguments)
        elif name == "generate_feature":
            return await handle_generate_feature(arguments)
        elif name == "run_bdd_agent":
            return await handle_run_bdd_agent(arguments)
        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

    capabilities = {"tools": {}}

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="antinode-norma",
                server_version="0.1.0",
                capabilities=capabilities
            )
        )

if __name__ == "__main__":
    asyncio.run(main())