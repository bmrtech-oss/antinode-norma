"""Generate Page Object classes from the test suite."""

import re
from pathlib import Path

from .base import Emitter
from ..models.test_model import ActionType, TestSuite


class PageObjectEmitter(Emitter):
    def emit(self, suite: TestSuite, output_dir: Path) -> None:
        self._ensure_output_dir(output_dir)
        page_names = []
        page_steps = {}

        for case in suite.cases:
            for step in case.steps:
                if not step.target:
                    continue
                page_name = self._page_name_for_step(step)
                page_names.append(page_name)
                page_steps.setdefault(page_name, {})[step.target] = step.action

        if not page_names:
            page_name = self._safe_page_name(suite.name or "default") + "Page"
            page_steps[page_name] = {}
            page_names = [page_name]

        for page_name in dict.fromkeys(page_names):
            selectors = page_steps.get(page_name, {})
            content = self._render_page_object(page_name, selectors)
            file_name = f"{self._safe_file_name(page_name)}.page.ts"
            self._write_file(output_dir / file_name, content)

    def _page_name_for_step(self, step) -> str:
        if step.action == ActionType.NAVIGATE and step.value:
            page_name = step.value.strip()
            if page_name.startswith("http"):
                host_and_path = page_name.split("//", 1)[-1]
                path = host_and_path.split("/", 1)[-1] if "/" in host_and_path else "home"
                if path and path != "home":
                    return self._safe_page_name(path) + "Page"
        return "DefaultPage"

    def _render_page_object(self, page_name: str, selectors: dict) -> str:
        lines = [
            "import { Page, Locator } from '@playwright/test';",
            "",
            f"export class {self._class_name(page_name)} {{",
            "  constructor(private page: Page) {}",
            "",
        ]
        for selector, action in selectors.items():
            method_name = self._selector_to_method(selector)
            lines.append(f"  async {method_name}(): Promise<Locator> {{")
            lines.append(f"    return this.page.locator('{self._escape_selector(selector)}');")
            lines.append("  }")
            lines.append("")
        lines.append("}")
        return "\n".join(lines)

    def _selector_to_method(self, selector: str) -> str:
        clean = re.sub(r"[^a-zA-Z0-9_]", "_", selector)
        parts = [part for part in clean.split("_") if part]
        if not parts:
            return "locator"
        return parts[0].lower() + "".join(p.capitalize() for p in parts[1:])

    def _safe_page_name(self, name: str) -> str:
        clean = re.sub(r"[^a-zA-Z0-9]+", " ", str(name)).strip()
        parts = [part.capitalize() for part in clean.split() if part]
        return "".join(parts) if parts else "DefaultPage"

    def _class_name(self, page_name: str) -> str:
        return self._safe_page_name(page_name)

    def _safe_file_name(self, page_name: str) -> str:
        return re.sub(r"[^a-zA-Z0-9_]", "", self._safe_page_name(page_name).lower())

    def _escape_selector(self, selector: str) -> str:
        return selector.replace("'", "\\'")
