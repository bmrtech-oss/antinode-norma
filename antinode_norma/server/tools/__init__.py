"""
MCP tool handlers for code generation.

This package contains handler functions for the MCP tools that expose
the code generation module via the Model Context Protocol.
"""

from .codegen_tools import (
    handle_generate_tests,
    handle_generate_page_objects,
    handle_generate_step_defs,
    handle_validate_feature,
)

__all__ = [
    "handle_generate_tests",
    "handle_generate_page_objects",
    "handle_generate_step_defs",
    "handle_validate_feature",
]
