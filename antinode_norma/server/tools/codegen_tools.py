"""Code generation MCP tool handlers.

This module provides MCP tools for generating executable test scripts
from Gherkin feature files.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from antinode_norma.codegen import Orchestrator
from antinode_norma.codegen.config import get_config

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
    verbose = arguments.get("verbose", False)

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
    ]
