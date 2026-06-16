# antinode_norma/core/validator.py

"""
Gherkin syntax validation.

This module provides a simple validator for Gherkin feature files.
It checks for required sections and basic step integrity.
"""

from .schemas import ValidateGherkinOutput

# Keywords that define steps
STEP_KEYWORDS = {"Given", "When", "Then", "And", "But"}


def validate_gherkin(content: str) -> ValidateGherkinOutput:
    """
    Validate a Gherkin feature file string.

    Checks:
    - Presence of 'Feature:' line.
    - Presence of 'Scenario:' or 'Scenario Outline:'.
    - Each step line (Given/When/Then/And/But) has text after the keyword.

    Args:
        content: The Gherkin content as a string.

    Returns:
        ValidateGherkinOutput: An object with 'valid' boolean and 'errors' list.
    """
    errors = []

    # Check for Feature
    if "Feature:" not in content:
        errors.append("Missing 'Feature:' line")

    # Check for Scenario or Scenario Outline
    if "Scenario:" not in content and "Scenario Outline:" not in content:
        errors.append("Missing 'Scenario:' or 'Scenario Outline:'")

    # Check each line for step integrity
    for line in content.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue

        # Check if the line starts with a step keyword
        for keyword in STEP_KEYWORDS:
            if stripped.startswith(keyword):
                # Extract the part after the keyword
                after_keyword = stripped[len(keyword) :].strip()
                # If there is no text after the keyword, it's an incomplete step
                if not after_keyword:
                    errors.append(f"Step incomplete: '{stripped}'")
                break  # Only check the first matching keyword

    return ValidateGherkinOutput(valid=len(errors) == 0, errors=errors)
