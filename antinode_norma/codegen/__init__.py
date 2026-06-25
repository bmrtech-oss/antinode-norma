"""
antinode_norma.codegen – Framework‑agnostic test code generator.

This package transforms Gherkin feature files into executable test scripts
for multiple frameworks (Playwright, Cypress, Selenium, etc.).

Public API:
    - Orchestrator: main entry point for the generation pipeline.
    - GherkinParser: reads .feature files and produces a TestSuite.
    - PlaywrightEmitter, CypressEmitter, SeleniumEmitter: framework emitters.
    - get_emitter: factory function to obtain an emitter by name.
    - TestSuite, TestCase, TestStep: immutable data models.
"""

from .engine.orchestrator import Orchestrator
from .parsers.gherkin_parser import GherkinParser
from .emitters.playwright_emitter import PlaywrightEmitter
from .emitters.cypress_emitter import CypressEmitter
from .emitters.selenium_emitter import SeleniumEmitter
from .emitters.factory import get_emitter
from .models.test_model import TestSuite, TestCase, TestStep, ActionType
from .config import CodegenConfig, load_config

__all__ = [
    "Orchestrator",
    "GherkinParser",
    "PlaywrightEmitter",
    "CypressEmitter",
    "SeleniumEmitter",
    "get_emitter",
    "TestSuite",
    "TestCase",
    "TestStep",
    "ActionType",
    "CodegenConfig",
    "load_config",
]
