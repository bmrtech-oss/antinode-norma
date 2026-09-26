"""Specialised emitter for Scenario Outline data-driven tests."""

from pathlib import Path

from .base import Emitter
from ..models.test_model import TestSuite


class ScenarioOutlineEmitter(Emitter):
    def emit(self, suite: TestSuite, output_dir: Path) -> None:
        self._ensure_output_dir(output_dir)
        content = self._render(suite)
        file_name = f"{self._safe_name(suite.name)}_outline.spec.ts"
        self._write_file(output_dir / file_name, content)

    def _safe_name(self, name: str) -> str:
        import re

        return re.sub(r"[^a-zA-Z0-9_]", "_", name).lower()

    def _render(self, suite: TestSuite) -> str:
        examples = []
        for case in suite.cases:
            examples.append({"name": case.name, "steps": len(case.steps)})

        lines = [
            "import { test, expect } from '@playwright/test';",
            "",
            f"describe('{suite.name}', () => {{",
            "  const cases = [",
        ]
        for example in examples:
            lines.append(f"    {{ name: '{example['name']}', steps: {example['steps']} }},")
        lines.extend([
            "  ];",
            "",
            "  for (const example of cases) {",
            "    test(`outline: ${example.name}`, async ({ page }) => {",
            "      expect(example.steps).toBeGreaterThan(0);",
            "    });",
            "  }",
            "});",
        ])
        return "\n".join(lines)
