"""Code generation MCP tool handlers.

This module provides MCP tools for generating executable test scripts
from Gherkin feature files.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from antinode_norma.codegen import Orchestrator
from antinode_norma.codegen.config import get_config
from antinode_norma.core import failure_analyzer
from antinode_norma.utils.llm_factory import create_llm_callable
import subprocess
import shutil
import tempfile
import os

# Try to import MCP types; fall back to dict if not available
try:
    from mcp import types
except ImportError:
    # Fallback for type annotations
    types = None


def _format_result(success: bool, message: str, data: Optional[Dict] = None) -> str:
    """Format a result as JSON for MCP response."""
    result = {
        "success": success,
        "message": message,
    }
    if data:
        result.update(data)
    return json.dumps(result, indent=2)


async def handle_generate_tests(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Handle generate_tests MCP tool.

    Generates executable test scripts from a feature file.

    Args:
        arguments: {
            "feature_path": str,      # Path to the .feature file
            "framework": str,         # playwright, cypress, selenium
            "output_dir": str,        # Optional output directory
            "use_page_objects": bool, # Optional quality flag
            "generate_step_defs": bool, # Optional quality flag
            "verbose": bool           # Optional
        }

    Returns:
        List of TextContent objects or dict for MCP response.
    """
    feature_path = arguments.get("feature_path")
    framework = arguments.get("framework", "playwright")
    output_dir = arguments.get("output_dir")
    use_page_objects = arguments.get("use_page_objects", False)
    generate_step_defs = arguments.get("generate_step_defs", False)
    enable_visual_testing = arguments.get("enable_visual_testing", None)
    visual_snapshot_dir = arguments.get("visual_snapshot_dir", None)

    # Validate required arguments
    if not feature_path:
        error_msg = "Error: 'feature_path' is required"
        return [{"type": "text", "text": _format_result(False, error_msg)}]

    feature_path = Path(feature_path)
    if not feature_path.exists():
        error_msg = f"Error: Feature file not found: {feature_path}"
        return [{"type": "text", "text": _format_result(False, error_msg)}]

    try:
        # Load config and optionally override settings
        config = get_config()

        # Override output directory if provided
        if output_dir:
            config.output_dir = Path(output_dir)

        # Override quality settings if provided
        if use_page_objects is not None:
            config.quality.use_page_objects = use_page_objects
        if generate_step_defs is not None:
            config.quality.generate_step_defs = generate_step_defs
        if enable_visual_testing is not None:
            config.quality.enable_visual_testing = enable_visual_testing
        if visual_snapshot_dir is not None:
            config.quality.visual_snapshot_dir = visual_snapshot_dir

        # Create orchestrator and generate
        orchestrator = Orchestrator()
        orchestrator.generate(
            feature_path=feature_path,
            output_dir=config.get_output_dir(framework),
            framework=framework,
        )

        output_path = config.get_output_dir(framework)

        result_data = {
            "feature_path": str(feature_path),
            "framework": framework,
            "output_dir": str(output_path),
            "quality_settings": {
                "use_page_objects": config.quality.use_page_objects,
                "generate_step_defs": config.quality.generate_step_defs,
                "enable_visual_testing": config.quality.enable_visual_testing,
                "visual_snapshot_dir": config.quality.visual_snapshot_dir,
                "selector_strategy": config.quality.selector_strategy,
            },
        }

        return [
            {
                "type": "text",
                "text": _format_result(
                    True, f"Tests generated successfully for {framework}", result_data
                ),
            }
        ]

    except Exception as e:
        return [
            {
                "type": "text",
                "text": _format_result(False, f"Error generating tests: {str(e)}"),
            }
        ]


async def handle_generate_page_objects(
    arguments: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Handle generate_page_objects MCP tool.

    Generates Page Object classes from a feature file.

    Args:
        arguments: {
            "feature_path": str,      # Path to the .feature file
            "framework": str,         # playwright, cypress, selenium
            "output_dir": str,        # Optional output directory
        }

    Returns:
        List of TextContent objects or dict for MCP response.
    """
    feature_path = arguments.get("feature_path")
    framework = arguments.get("framework", "playwright")
    output_dir = arguments.get("output_dir")

    if not feature_path:
        return [
            {
                "type": "text",
                "text": _format_result(False, "Error: 'feature_path' is required"),
            }
        ]

    feature_path = Path(feature_path)
    if not feature_path.exists():
        return [
            {
                "type": "text",
                "text": _format_result(
                    False, f"Error: Feature file not found: {feature_path}"
                ),
            }
        ]

    try:
        # Load config and enable page objects
        config = get_config()
        config.quality.use_page_objects = True

        if output_dir:
            config.output_dir = Path(output_dir)

        # Create orchestrator and generate
        orchestrator = Orchestrator()
        suite = orchestrator.parse(feature_path)

        # Only emit page objects (using a custom emitter)
        from antinode_norma.codegen.emitters.page_object_emitter import (
            PageObjectEmitter,
        )

        emitter = PageObjectEmitter()
        emitter.emit(suite, config.get_output_dir(framework))

        output_path = config.get_output_dir(framework) / config.quality.page_object_dir

        result_data = {
            "feature_path": str(feature_path),
            "framework": framework,
            "page_object_dir": str(output_path),
        }

        return [
            {
                "type": "text",
                "text": _format_result(
                    True, "Page Objects generated successfully", result_data
                ),
            }
        ]

    except Exception as e:
        return [
            {
                "type": "text",
                "text": _format_result(
                    False, f"Error generating page objects: {str(e)}"
                ),
            }
        ]


async def handle_generate_step_defs(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Handle generate_step_defs MCP tool.

    Generates reusable step definitions from a feature file.

    Args:
        arguments: {
            "feature_path": str,      # Path to the .feature file
            "framework": str,         # playwright, cypress, selenium
            "output_dir": str,        # Optional output directory
        }

    Returns:
        List of TextContent objects or dict for MCP response.
    """
    feature_path = arguments.get("feature_path")
    framework = arguments.get("framework", "playwright")
    output_dir = arguments.get("output_dir")

    if not feature_path:
        return [
            {
                "type": "text",
                "text": _format_result(False, "Error: 'feature_path' is required"),
            }
        ]

    feature_path = Path(feature_path)
    if not feature_path.exists():
        return [
            {
                "type": "text",
                "text": _format_result(
                    False, f"Error: Feature file not found: {feature_path}"
                ),
            }
        ]

    try:
        # Load config and enable step definitions
        config = get_config()
        config.quality.generate_step_defs = True

        if output_dir:
            config.output_dir = Path(output_dir)

        # Create orchestrator and generate
        orchestrator = Orchestrator()
        suite = orchestrator.parse(feature_path)

        # Only emit step definitions
        from antinode_norma.codegen.emitters.step_def_emitter import StepDefEmitter

        emitter = StepDefEmitter()
        emitter.emit(suite, config.get_output_dir(framework))

        output_path = config.get_output_dir(framework) / config.quality.step_def_dir

        result_data = {
            "feature_path": str(feature_path),
            "framework": framework,
            "step_def_dir": str(output_path),
        }

        return [
            {
                "type": "text",
                "text": _format_result(
                    True, "Step definitions generated successfully", result_data
                ),
            }
        ]

    except Exception as e:
        return [
            {
                "type": "text",
                "text": _format_result(
                    False, f"Error generating step definitions: {str(e)}"
                ),
            }
        ]


async def handle_validate_feature(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Handle validate_feature MCP tool.

    Validates a Gherkin feature file for quality and completeness.

    Args:
        arguments: {
            "feature_path": str,      # Path to the .feature file
            "check_invest": bool,     # Optional, run INVEST quality check
        }

    Returns:
        List of TextContent objects or dict for MCP response.
    """
    feature_path = arguments.get("feature_path")
    check_invest = arguments.get("check_invest", True)

    if not feature_path:
        return [
            {
                "type": "text",
                "text": _format_result(False, "Error: 'feature_path' is required"),
            }
        ]

    feature_path = Path(feature_path)
    if not feature_path.exists():
        return [
            {
                "type": "text",
                "text": _format_result(
                    False, f"Error: Feature file not found: {feature_path}"
                ),
            }
        ]

    try:
        # Parse the feature file
        from antinode_norma.codegen.parsers.gherkin_parser import GherkinParser

        parser = GherkinParser()
        suite = parser.parse(feature_path)

        # Basic validation
        issues = []
        warnings = []

        # Check if there are any scenarios
        if not suite.cases:
            issues.append("No scenarios found in the feature file.")

        # Check INVEST quality if requested
        if check_invest:
            # For each scenario, check INVEST criteria
            for case in suite.cases:
                # Check Independent (simplified)
                if len(case.steps) == 0:
                    issues.append(f"Scenario '{case.name}' has no steps.")

                # Check Estimable (simplified)
                if len(case.steps) > 20:
                    warnings.append(
                        f"Scenario '{case.name}' has many steps ({len(case.steps)}), consider splitting."
                    )

                # Check Small (simplified)
                if len(case.steps) > 10:
                    warnings.append(
                        f"Scenario '{case.name}' has {len(case.steps)} steps, consider simplifying."
                    )

        result_data = {
            "feature_path": str(feature_path),
            "scenarios": len(suite.cases),
            "total_steps": sum(len(case.steps) for case in suite.cases),
            "tags": suite.tags,
            "issues": issues,
            "warnings": warnings,
            "is_valid": len(issues) == 0,
        }

        return [
            {
                "type": "text",
                "text": _format_result(
                    len(issues) == 0, "Feature validation completed", result_data
                ),
            }
        ]

    except Exception as e:
        return [
            {
                "type": "text",
                "text": _format_result(False, f"Error validating feature: {str(e)}"),
            }
        ]


async def handle_generate_and_autocorrect(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate tests, run them, and attempt automatic Gherkin fixes when failures occur.

    Arguments:
        feature_path: str (required)
        framework: str (default 'playwright')
        output_dir: str (optional)
        run_tests: bool (default True for playwright)
        max_iterations: int (default 2)

    Returns: MCP-style JSON result with success, messages and diagnostics.
    """
    feature_path = arguments.get("feature_path")
    framework = arguments.get("framework", "playwright")
    output_dir = arguments.get("output_dir")
    run_tests = arguments.get("run_tests", True)
    max_iterations = int(arguments.get("max_iterations", 2))
    non_destructive = bool(arguments.get("non_destructive", False))
    create_branch = bool(arguments.get("create_branch", False))
    confirm_before_apply = bool(arguments.get("confirm_before_apply", False))
    approve = bool(arguments.get("approve", False))

    if not feature_path:
        return [{"type": "text", "text": _format_result(False, "Error: 'feature_path' is required")}]

    feature_path = Path(feature_path)
    if not feature_path.exists():
        return [{"type": "text", "text": _format_result(False, f"Error: Feature file not found: {feature_path}")}]

    # Load config and prepare output dir
    try:
        config = get_config()
        if output_dir:
            config.output_dir = Path(output_dir)

        orchestrator = Orchestrator()

        # Iteratively generate -> run -> analyze -> fix
        iteration = 0
        messages: List[str] = []
        last_report = None

        while iteration < max_iterations:
            iteration += 1
            orchestrator.generate(
                feature_path=feature_path,
                output_dir=config.get_output_dir(framework),
                framework=framework,
            )

            messages.append(f"Iteration {iteration}: Generated tests for {framework}.")

            if not run_tests or framework.lower() != "playwright":
                break

            # Find available playwright executable: prefer local node_modules/.bin/playwright, then npx, then playwright CLI
            pw_cmd = None
            if shutil.which("playwright"):
                pw_cmd = ["playwright", "test", str(config.get_output_dir(framework)), "--reporter=json"]
            elif shutil.which("npx"):
                pw_cmd = ["npx", "playwright", "test", str(config.get_output_dir(framework)), "--reporter=json"]

            if not pw_cmd:
                messages.append("Playwright not found on PATH; skipping test run.")
                break

            # Run Playwright and capture JSON output
            try:
                proc = subprocess.run(pw_cmd, capture_output=True, text=True, cwd=os.getcwd())
            except Exception as e:
                messages.append(f"Error running Playwright: {e}")
                break

            # Write stdout to temp report file
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
            tmp.write(proc.stdout.encode("utf-8"))
            tmp.flush()
            tmp.close()
            report_path = Path(tmp.name)
            last_report = str(report_path)

            # Parse and store failures
            failures = failure_analyzer.store_playwright_failures(report_path)
            if not failures:
                messages.append("No failures detected; tests passed.")
                return [
                    {"type": "text", "text": _format_result(True, "Tests passed", {"messages": messages})}
                ]

            messages.append(f"Detected {len(failures)} failure(s).")

            # Build prompt for LLM to suggest Gherkin fixes
            try:
                llm_config = {
                    "provider": os.getenv("LLM_PROVIDER", "openrouter"),
                    "api_key": os.getenv("OPENROUTER_API_KEY") or os.getenv("ANTHROPIC_API_KEY"),
                }
                llm = create_llm_callable(llm_config)

                failure_summary_lines = []
                for f in failures:
                    failure_summary_lines.append(
                        f"Step: {f.step_text or ''}\nSelector: {f.selector or ''}\nError: {f.error_message.splitlines()[0]}"
                    )

                with open(feature_path, "r", encoding="utf-8") as fh:
                    current_feature = fh.read()

                prompt = (
                    "You are an expert BDD engineer. The following Playwright test failures were observed when running the tests generated from the Gherkin feature below.\n\n"
                    "Failures:\n" + "\n---\n".join(failure_summary_lines)
                    + "\n\nCurrent feature:\n" + current_feature
                    + "\n\nProduce a corrected Gherkin feature file that addresses the root causes of these failures. Return ONLY the corrected feature file, with minimal changes."
                )

                fixed = llm(prompt)

                target_path = feature_path
                if non_destructive:
                    target_path = feature_path.with_name(feature_path.stem + ".autocorrected.feature")

                # If confirmation requested, require approval or interactive prompt
                if confirm_before_apply and not approve:
                    try:
                        import sys

                        if sys.stdin is not None and sys.stdin.isatty():
                            resp = input(f"Apply LLM-suggested fixes to {target_path}? [y/N]: ")
                            if resp.strip().lower() not in {"y", "yes"}:
                                messages.append("User declined to apply LLM fixes.")
                                # Do not apply; return current diagnostics
                                data = {"messages": messages}
                                if last_report:
                                    data["last_report"] = last_report
                                return [{"type": "text", "text": _format_result(False, "User declined LLM fixes", data)}]
                        else:
                            # Non-interactive: require explicit 'approve' flag
                            data = {"messages": messages, "note": "Approval required in non-interactive mode (set 'approve': true)"}
                            return [{"type": "text", "text": _format_result(False, "Approval required to apply fixes", data)}]
                    except Exception:
                        data = {"messages": messages, "note": "Unable to prompt for confirmation"}
                        return [{"type": "text", "text": _format_result(False, "Approval required to apply fixes", data)}]

                # Apply or write fixed content
                target_path.write_text(fixed, encoding="utf-8")

                # Optionally create a git branch and commit the change (local only)
                if create_branch:
                    try:
                        import subprocess as _sub

                        safe_branch = f"autocorrect/{feature_path.stem}-iter{iteration}"
                        _sub.run(["git", "checkout", "-b", safe_branch], check=False)
                        _sub.run(["git", "add", str(target_path)], check=False)
                        _sub.run(["git", "commit", "-m", f"autocorrect: apply LLM fixes to {target_path.name}"], check=False)
                        messages.append(f"Committed fixes to branch {safe_branch}.")
                    except Exception:
                        messages.append("Git branch/commit failed (continuing without committing).")

                messages.append(f"Applied LLM-suggested Gherkin fixes to {target_path}.")

                # Loop will regenerate and re-run
                continue
            except Exception as e:
                messages.append(f"LLM-based fix failed: {e}")
                break

        # If we exit loop with failures, return diagnostics
        data = {"messages": messages}
        if last_report:
            data["last_report"] = last_report

        return [{"type": "text", "text": _format_result(False, "Auto-correction completed with unresolved failures", data)}]

    except Exception as e:
        return [{"type": "text", "text": _format_result(False, f"Error during generate_and_autocorrect: {str(e)}")}]


# Tool definitions for MCP server
def get_tool_definitions():
    """Return the tool definitions for MCP registration."""
    return [
        {
            "name": "generate_tests",
            "description": "Generate executable test scripts (Playwright, Cypress, Selenium) from a .feature file.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "feature_path": {
                        "type": "string",
                        "description": "Path to the .feature file",
                    },
                    "framework": {
                        "type": "string",
                        "description": "Target framework",
                        "enum": ["playwright", "cypress", "selenium"],
                        "default": "playwright",
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Output directory for generated tests (optional)",
                    },
                    "use_page_objects": {
                        "type": "boolean",
                        "description": "Generate Page Objects",
                        "default": False,
                    },
                    "generate_step_defs": {
                        "type": "boolean",
                        "description": "Generate reusable step definitions",
                        "default": False,
                    },
                    "verbose": {
                        "type": "boolean",
                        "description": "Enable verbose output",
                        "default": False,
                    },
                },
                "required": ["feature_path"],
            },
        },
        {
            "name": "generate_page_objects",
            "description": "Generate Page Object classes from a .feature file.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "feature_path": {
                        "type": "string",
                        "description": "Path to the .feature file",
                    },
                    "framework": {
                        "type": "string",
                        "description": "Target framework",
                        "enum": ["playwright", "cypress", "selenium"],
                        "default": "playwright",
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Output directory for page objects (optional)",
                    },
                },
                "required": ["feature_path"],
            },
        },
        {
            "name": "generate_step_defs",
            "description": "Generate reusable step definitions from a .feature file.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "feature_path": {
                        "type": "string",
                        "description": "Path to the .feature file",
                    },
                    "framework": {
                        "type": "string",
                        "description": "Target framework",
                        "enum": ["playwright", "cypress", "selenium"],
                        "default": "playwright",
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Output directory for step definitions (optional)",
                    },
                },
                "required": ["feature_path"],
            },
        },
        {
            "name": "validate_feature",
            "description": "Validate a Gherkin feature file for quality and completeness.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "feature_path": {
                        "type": "string",
                        "description": "Path to the .feature file",
                    },
                    "check_invest": {
                        "type": "boolean",
                        "description": "Run INVEST quality check",
                        "default": True,
                    },
                },
                "required": ["feature_path"],
            },
        },
        {
            "name": "generate_and_autocorrect",
            "description": "Generate tests, run Playwright, analyze failures and automatically propose Gherkin fixes using the LLM.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "feature_path": {"type": "string"},
                    "framework": {"type": "string", "enum": ["playwright", "cypress", "selenium"], "default": "playwright"},
                    "output_dir": {"type": "string"},
                    "run_tests": {"type": "boolean", "default": True},
                    "max_iterations": {"type": "integer", "default": 2},
                },
                "required": ["feature_path"],
            },
        },
    ]
