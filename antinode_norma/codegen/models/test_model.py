"""
Generic test model (Intermediate Representation).

This module defines immutable data classes that describe a test suite
in a framework‑agnostic way. All transformations pass data through
these structures.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any
from enum import Enum


class ActionType(Enum):
    """Supported test actions."""
    NAVIGATE = "navigate"
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    HOVER = "hover"
    FILL = "fill"
    CLEAR = "clear"
    SELECT = "select"
    CHECK = "check"
    UNCHECK = "uncheck"
    ASSERT_VISIBLE = "assert_visible"
    ASSERT_HIDDEN = "assert_hidden"
    ASSERT_TEXT = "assert_text"
    ASSERT_VALUE = "assert_value"
    ASSERT_URL = "assert_url"
    ASSERT_TITLE = "assert_title"
    WAIT = "wait"
    SCREENSHOT = "screenshot"
    EXECUTE_SCRIPT = "execute_script"
    # Extend as needed


@dataclass(frozen=True)
class TestStep:
    """A single test step."""
    action: ActionType
    target: Optional[str] = None       # CSS selector, XPath, URL, etc.
    value: Optional[str] = None        # text to fill, expected text, etc.
    description: Optional[str] = None  # human‑readable step text (from Gherkin)
    options: dict = field(default_factory=dict)  # extra parameters (timeout, etc.)


@dataclass(frozen=True)
class TestCase:
    """A single test case (scenario)."""
    name: str
    steps: List[TestStep]
    tags: List[str] = field(default_factory=list)
    description: Optional[str] = None
    background: Optional[List[TestStep]] = None  # shared steps before scenario


@dataclass(frozen=True)
class TestSuite:
    """A collection of test cases from one feature file."""
    name: str
    cases: List[TestCase]
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    background: Optional[List[TestStep]] = None  # global background for all scenarios