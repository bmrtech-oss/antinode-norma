"""
Cypress (JavaScript) code generator.
"""

from pathlib import Path
import re

from .base import Emitter
from ..models.test_model import TestSuite, TestCase, TestStep, ActionType
from ..utils.file_utils import ensure_directory, write_file


class CypressEmitter(Emitter):
    """Generate Cypress test files in JavaScript."""

    def emit(self, suite: TestSuite, output_dir: Path) -> None:
        ensure_directory(output_dir)
        filename = self._safe_filename(suite.name) + ".cy.js"
        content = self._render(suite)
        write_file(output_dir / filename, content)

    def _safe_filename(self, name: str) -> str:
        return re.sub(r"[^a-zA-Z0-9_]", "_", name).lower()

    def _render(self, suite: TestSuite) -> str:
        lines = [
            "describe('" + suite.name + "', () => {",
        ]
        for case in suite.cases:
            lines.append(f"  it('{case.name}', () => {{")
            for step in case.steps:
                lines.append(f"    {self._translate_step(step)}")
            lines.append("  });")
        lines.append("});")
        return "\n".join(lines)

    def _translate_step(self, step: TestStep) -> str:
        action = step.action
        target = step.target
        value = step.value
        if action == ActionType.NAVIGATE:
            return f"cy.visit('{value}');"
        elif action == ActionType.CLICK:
            return f"cy.get('{target}').click();"
        elif action == ActionType.FILL:
            return f"cy.get('{target}').type('{value}');"
        elif action == ActionType.ASSERT_TEXT:
            return f"cy.contains('{value}').should('be.visible');"
        elif action == ActionType.ASSERT_VISIBLE:
            return f"cy.get('{target}').should('be.visible');"
        elif action == ActionType.ASSERT_HIDDEN:
            return f"cy.get('{target}').should('not.be.visible');"
        elif action == ActionType.WAIT:
            return f"cy.wait({int(value)*1000});"
        elif action == ActionType.CHECK:
            return f"cy.get('{target}').check();"
        elif action == ActionType.UNCHECK:
            return f"cy.get('{target}').uncheck();"
        elif action == ActionType.SELECT:
            return f"cy.get('{target}').select('{value}');"
        elif action == ActionType.ASSERT_URL:
            return f"cy.url().should('eq', '{value}');"
        elif action == ActionType.ASSERT_TITLE:
            return f"cy.title().should('eq', '{value}');"
        else:
            return f"// UNKNOWN: {step.description}"
