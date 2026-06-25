"""
Helper functions for working with ActionType.
"""
from .test_model import ActionType

# Mapping from Gherkin keywords to ActionType (used in rules)
KEYWORD_TO_ACTION = {
    "Given": ActionType.NAVIGATE,   # default, overridden by step text
    "When": ActionType.CLICK,
    "Then": ActionType.ASSERT_TEXT,
    "And": ActionType.CLICK,
    "But": ActionType.ASSERT_TEXT,
}