# antinode_norma/core/validator.py

"""Gherkin syntax validation backed by the official Cucumber parser."""

from gherkin.parser import Parser

from .schemas import ValidateGherkinOutput

# Keywords that define steps
STEP_KEYWORDS = {"Given", "When", "Then", "And", "But"}


def validate_gherkin(content: str) -> ValidateGherkinOutput:
    """
    Validate a Gherkin feature file string.

    Checks the repository's minimum structure before delegating complete syntax
    validation to ``gherkin-official``.

    Args:
        content: The Gherkin content as a string.

    Returns:
        ValidateGherkinOutput: An object with 'valid' boolean and 'errors' list.
    """
    errors = []

    if "Feature:" not in content:
        errors.append("Missing 'Feature:' line")

    if "Scenario:" not in content and "Scenario Outline:" not in content:
        errors.append("Missing 'Scenario:' or 'Scenario Outline:'")

    for line in content.split("\n"):
        stripped = line.strip()
        for keyword in STEP_KEYWORDS:
            if stripped.startswith(keyword) and not stripped[len(keyword) :].strip():
                errors.append(f"Step incomplete: '{stripped}'")
                break

    if errors:
        return ValidateGherkinOutput(valid=False, errors=errors)

    try:
        Parser().parse(content)
    except Exception as exc:
        errors.append(str(exc))

    return ValidateGherkinOutput(valid=len(errors) == 0, errors=errors)
