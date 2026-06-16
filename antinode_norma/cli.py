#!/usr/bin/env python
"""Command-line interface for antinode-norma."""

import asyncio
import sys
import os
import click
from dotenv import load_dotenv

from antinode_norma.runner import run_agent_from_raw

load_dotenv()


@click.group()
def cli():
    """Antinode Norma – Transform user stories into Gherkin feature files."""
    pass


@cli.command()
@click.argument("story_text", required=False)
@click.option("--file", "-f", type=click.Path(exists=True), help="Read story from file")
@click.option(
    "--output-dir", "-o", default="features", help="Output directory for feature files"
)
@click.option(
    "--quality-only", is_flag=True, help="Only check quality, do not generate"
)
def generate(story_text, file, output_dir, quality_only):
    """Generate a feature file from a user story."""
    if file:
        with open(file, "r") as f:
            story_text = f.read()
    if not story_text:
        click.echo(
            "Error: No story provided. Use --file or pass story text as argument."
        )
        sys.exit(1)

    os.environ["NORMA_OUTPUT_DIR"] = output_dir

    async def run():
        result = await run_agent_from_raw(story_text, quality_only=quality_only)
        if quality_only:
            click.echo(f"Quality score: {result['quality_score']}")
            click.echo(f"Passes INVEST: {result['passes_invest']}")
            if result.get("issues"):
                click.echo("Issues:\n  - " + "\n  - ".join(result["issues"]))
        else:
            if "error" in result:
                click.echo(f"Error: {result['error']}")
                if "issues" in result:
                    click.echo("Issues:\n  - " + "\n  - ".join(result["issues"]))
            else:
                click.echo(f"Feature file written: {result['feature_path']}")
        return result

    asyncio.run(run())


@cli.command()
@click.option("--transport", default="stdio", help="MCP transport (stdio or sse)")
def serve(transport):
    """Start the Norma MCP server."""
    from antinode_norma.server.mcp_server import main as mcp_main

    click.echo(f"Starting Norma MCP server on {transport}...")
    mcp_main()


if __name__ == "__main__":
    cli()
