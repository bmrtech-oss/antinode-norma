#!/usr/bin/env python3
"""
Command‑line interface for the code generation module.
"""

import click
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..engine.orchestrator import Orchestrator
from ..config import load_config, set_config
from ..parsers.gherkin_parser import GherkinParser


@click.group()
def cli():
    """Antinode Norma – test code generator from Gherkin feature files."""
    pass


@cli.command()
@click.option(
    "--feature",
    "-f",
    "feature_paths",
    required=True,
    multiple=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Path to one or more .feature files. Repeat this flag for multiple files.",
)
@click.option(
    "--output", "-o", type=click.Path(), help="Output directory (overrides config)."
)
@click.option(
    "--framework",
    "-fw",
    default=None,
    help="Target framework: playwright, cypress, or selenium.",
)
@click.option(
    "--config-file",
    "-c",
    type=click.Path(exists=True, dir_okay=False),
    help="Optional YAML configuration file.",
)
@click.option("--use-page-objects", is_flag=True, help="Generate Page Object classes.")
@click.option(
    "--generate-step-defs", is_flag=True, help="Generate reusable step definitions."
)
@click.option(
    "--enable-visual-testing", is_flag=True, help="Include visual snapshot assertions."
)
@click.option(
    "--visual-snapshot-dir", type=click.Path(), help="Directory for baseline snapshots."
)
@click.option(
    "--workers",
    default=1,
    type=int,
    show_default=True,
    help="Number of parallel worker threads for batch generation.",
)
@click.option("--verbose", is_flag=True, help="Enable verbose output.")
def generate(
    feature_paths,
    output,
    framework,
    config_file,
    use_page_objects,
    generate_step_defs,
    enable_visual_testing,
    visual_snapshot_dir,
    workers,
    verbose,
):
    """Generate executable test scripts from one or more Gherkin feature files."""
    # Load configuration
    cfg = load_config(config_file=Path(config_file) if config_file else None)

    # Override with CLI args
    if output:
        cfg.output_dir = Path(output)
    if framework:
        cfg.default_framework = framework
    if use_page_objects:
        cfg.quality.use_page_objects = True
    if generate_step_defs:
        cfg.quality.generate_step_defs = True
    if enable_visual_testing:
        cfg.quality.enable_visual_testing = True
    if visual_snapshot_dir:
        cfg.quality.visual_snapshot_dir = visual_snapshot_dir
    if verbose:
        cfg.verbose = True

    # Apply CLI-loaded config globally so Orchestrator/get_config sees it
    set_config(cfg)

    feature_paths = [Path(p) for p in feature_paths]
    framework_name = framework or cfg.default_framework
    output_dir_path = Path(output) if output else cfg.get_output_dir(framework_name)

    def process_feature(feature_path: Path) -> str:
        orch = Orchestrator()
        orch.generate(
            feature_path=feature_path,
            output_dir=output_dir_path,
            framework=framework_name,
        )
        return str(feature_path)

    results = []
    errors = []

    if len(feature_paths) > 1 or workers > 1:
        workers = min(workers, len(feature_paths))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(process_feature, path): path for path in feature_paths
            }
            for future in as_completed(futures):
                path = futures[future]
                try:
                    results.append(future.result())
                    click.echo(f"✅ Generated tests for '{path}'")
                except Exception as e:
                    errors.append((path, str(e)))
                    click.echo(f"❌ Failed to generate '{path}': {e}", err=True)
    else:
        try:
            generated = process_feature(feature_paths[0])
            results.append(generated)
            click.echo(
                f"✅ Tests generated successfully for '{generated}' → {output_dir_path}"
            )
        except Exception as e:
            click.echo(f"❌ Error generating tests: {e}", err=True)
            raise click.Abort()

    if errors:
        raise click.Abort()

    if cfg.quality.use_page_objects:
        click.echo(f"   📄 Page Objects generated in {cfg.quality.page_object_dir}/")
    if cfg.quality.generate_step_defs:
        click.echo(f"   📄 Step Definitions generated in {cfg.quality.step_def_dir}/")
    if cfg.quality.enable_visual_testing:
        click.echo(f"   🖼️ Visual snapshots in {cfg.quality.visual_snapshot_dir}/")


@cli.command()
@click.option(
    "--feature",
    "-f",
    required=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Path to the .feature file.",
)
@click.option(
    "--check-invest",
    is_flag=True,
    default=True,
    help="Run INVEST quality check on scenarios (default: true).",
)
@click.option("--verbose", is_flag=True, help="Show detailed output.")
def validate(feature, check_invest, verbose):
    """Validate a Gherkin feature file for quality and completeness."""
    try:
        parser = GherkinParser()
        suite = parser.parse(Path(feature))
    except Exception as e:
        click.echo(f"❌ Failed to parse feature file: {e}", err=True)
        raise click.Abort()

    # Basic validation
    issues = []
    warnings = []

    # Check if there are any scenarios
    if not suite.cases:
        issues.append("No scenarios found in the feature file.")

    # INVEST‑style checks
    if check_invest:
        for case in suite.cases:
            # Independent – no steps? (simplified)
            if len(case.steps) == 0:
                issues.append(f"Scenario '{case.name}' has no steps – not testable.")
            # Estimable – too many steps?
            if len(case.steps) > 20:
                issues.append(
                    f"Scenario '{case.name}' has {len(case.steps)} steps – consider splitting."
                )
            elif len(case.steps) > 10:
                warnings.append(
                    f"Scenario '{case.name}' has {len(case.steps)} steps – consider simplifying."
                )
            # Testable – check if each step has a clear action (we already have actions)
            # Small – if there are too many criteria in one scenario?
            if len(case.steps) > 10:
                warnings.append(
                    f"Scenario '{case.name}' is quite long ({len(case.steps)} steps)."
                )

    # Print results
    click.echo(f"\n📋 Validating: {feature}")
    click.echo(f"   Scenarios: {len(suite.cases)}")
    click.echo(f"   Total steps: {sum(len(case.steps) for case in suite.cases)}")
    click.echo(f"   Tags: {suite.tags or 'none'}")

    if verbose:
        click.echo("\n📝 Scenarios:")
        for case in suite.cases:
            click.echo(f"   - {case.name} ({len(case.steps)} steps)")
            if case.tags:
                click.echo(f"     Tags: {', '.join(case.tags)}")

    if issues:
        click.echo("\n❌ Issues:")
        for issue in issues:
            click.echo(f"   • {issue}")
    if warnings:
        click.echo("\n⚠️  Warnings:")
        for warning in warnings:
            click.echo(f"   • {warning}")

    if not issues and not warnings:
        click.echo("\n✅ Feature file is valid and passes all quality checks.")
    elif not issues:
        click.echo("\n✅ Feature file is valid, but has warnings to consider.")
    else:
        click.echo("\n❌ Feature file has issues that need fixing.")
        raise click.Abort()


if __name__ == "__main__":
    cli()
