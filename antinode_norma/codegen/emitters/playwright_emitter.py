"""
Playwright (TypeScript) code generator.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Set
from ..models.test_model import TestSuite, TestCase, TestStep, ActionType
from .base import Emitter
from ..utils.file_utils import ensure_directory, write_file
from ..config import get_config
from ..engine.quality import QualityConfig
from ..post_processors.healer import render_playwright_healer

class PlaywrightEmitter(Emitter):
    """Generate Playwright test files with optional quality enhancements."""

    def __init__(self):
        self.config = get_config()
        self.quality: QualityConfig = self.config.quality

    def emit(self, suite: TestSuite, output_dir: Path) -> None:
        ensure_directory(output_dir)
        self._collect_pages(suite)
        if self.quality.use_page_objects:
            self._emit_page_objects(suite, output_dir / self.quality.page_object_dir)
        if self.quality.generate_step_defs:
            self._emit_step_defs(suite, output_dir / self.quality.step_def_dir)
        if self.quality.enable_self_healing:
            self._emit_self_healing_helper(output_dir)
        if self.quality.enable_visual_testing:
            self._ensure_visual_snapshot_dir(output_dir)
        # Generate the main test file
        filename = self._safe_filename(suite.name) + ".spec.ts"
        content = self._render(suite, output_dir)
        write_file(output_dir / filename, content)

    def _collect_pages(self, suite: TestSuite) -> None:
        """Extract distinct pages (URLs) from the suite for page objects."""
        self.pages: Dict[str, List[TestStep]] = {}
        for case in suite.cases:
            for step in case.steps:
                if step.action == ActionType.NAVIGATE and step.value:
                    url = step.value
                    # Normalize URL to a page name
                    # Example: https://example.com/login -> LoginPage
                    page_name = self._url_to_page_name(url)
                    if page_name not in self.pages:
                        self.pages[page_name] = []
                    self.pages[page_name].append(step)
        # Also collect any selectors used per page (we'll infer from target)

    def _url_to_page_name(self, url: str) -> str:
        """Convert URL to a CamelCase page name."""
        # Remove protocol and domain, keep path
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        path = parsed.path.strip('/')
        if not path:
            path = 'home'
        parts = path.split('/')
        # Capitalise each part
        name = ''.join(p.capitalize() for p in parts if p)
        return name + 'Page'

    def _emit_page_objects(self, suite: TestSuite, pages_dir: Path) -> None:
        """Generate Page Object classes for each distinct page."""
        ensure_directory(pages_dir)
        # For each page, create a class with methods for each action on that page
        for page_name, steps in self.pages.items():
            # Group steps by element selector
            selectors = {}
            for step in steps:
                if step.target:
                    selectors[step.target] = step.action
            content = self._render_page_object(page_name, selectors)
            write_file(pages_dir / f"{page_name.lower()}.page.ts", content)

    def _render_page_object(self, page_name: str, selectors: Dict[str, ActionType]) -> str:
        """Render a Page Object class for the given page."""
        lines = [
            "import { Page, Locator } from '@playwright/test';",
            "",
            f"export class {page_name} {{",
            f"  constructor(private page: Page) {{}}",
            "",
        ]
        # Add goto method if there's a NAVIGATE step
        # We'll infer from the first NAVIGATE step in the suite for this page
        # For simplicity, we'll generate a goto() method that navigates to the URL
        # We don't store URL per page, but we can store it separately.
        # For now, we'll just generate getters for each selector.
        for selector, action in selectors.items():
            # Convert selector to a method name
            method_name = self._selector_to_method(selector)
            lines.append(f"  async {method_name}() {{")
            lines.append(f"    return this.page.locator('{selector}');")
            lines.append("  }")
            lines.append("")
        lines.append("}")
        return "\n".join(lines)

    def _selector_to_method(self, selector: str) -> str:
        """Convert selector string to a camelCase method name."""
        # Remove special characters, keep alphanumeric and underscore
        clean = re.sub(r'[^a-zA-Z0-9]', '_', selector)
        # Convert to camelCase
        parts = clean.split('_')
        if len(parts) == 1:
            return parts[0].lower()
        return parts[0].lower() + ''.join(p.capitalize() for p in parts[1:])

    def _emit_step_defs(self, suite: TestSuite, steps_dir: Path) -> None:
        """Generate reusable step definition functions."""
        ensure_directory(steps_dir)
        # Analyse all steps and create a map of action->step pattern
        # For simplicity, we'll generate common steps like fillField, clickElement, etc.
        content = self._render_step_defs(suite)
        write_file(steps_dir / "common_steps.ts", content)

    def _emit_self_healing_helper(self, output_dir: Path) -> None:
        """Write the self-healing helper module for Playwright tests."""
        content = render_playwright_healer()
        write_file(output_dir / "self_healing.ts", content)

    def _ensure_visual_snapshot_dir(self, output_dir: Path) -> None:
        """Create the baseline snapshot directory for visual assertions."""
        ensure_directory(output_dir / self.quality.visual_snapshot_dir)

    def _render_step_defs(self, suite: TestSuite) -> str:
        lines = [
            "import { Page, expect } from '@playwright/test';",
            "",
            "export async function navigateTo(page: Page, url: string) {",
            "  await page.goto(url);",
            "}",
            "",
            "export async function fillField(page: Page, selector: string, value: string) {",
            "  await page.locator(selector).fill(value);",
            "}",
            "",
            "export async function clickElement(page: Page, selector: string) {",
            "  await page.locator(selector).click();",
            "}",
            "",
            "export async function checkElement(page: Page, selector: string) {",
            "  await page.locator(selector).check();",
            "}",
            "",
            "export async function uncheckElement(page: Page, selector: string) {",
            "  await page.locator(selector).uncheck();",
            "}",
            "",
            "export async function selectOption(page: Page, selector: string, value: string) {",
            "  await page.locator(selector).selectOption(value);",
            "}",
            "",
            "export async function assertVisible(page: Page, selector: string) {",
            "  await expect(page.locator(selector)).toBeVisible();",
            "}",
            "",
            "export async function assertScreenshot(page: Page, path: string) {",
            "  await expect(page).toHaveScreenshot({ path, fullPage: true });",
            "}",
            "",
            "export async function assertHidden(page: Page, selector: string) {",
            "  await expect(page.locator(selector)).toBeHidden();",
            "}",
            "",
            "export async function assertValue(page: Page, selector: string, value: string) {",
            "  await expect(page.locator(selector)).toHaveValue(value);",
            "}",
            "",
            "export async function assertText(page: Page, text: string) {",
            "  await expect(page.locator('body')).toContainText(text);",
            "}",
        ]
        return "\n".join(lines)

    def _render(self, suite: TestSuite, output_dir: Path) -> str:
        """Generate the main test file, possibly using Page Objects and Step Defs."""
        # Determine if we should use page objects or step defs
        use_po = self.quality.use_page_objects
        use_sd = self.quality.generate_step_defs
        # Build imports
        imports = ["import { test, expect } from '@playwright/test';"]
        if self.quality.enable_self_healing:
            imports.append("import { healSelector } from './self_healing';")
        if use_po:
            # Import page objects from relative path
            page_imports = []
            for page_name in self.pages.keys():
                page_imports.append(f"import {{ {page_name} }} from './{self.quality.page_object_dir}/{page_name.lower()}.page';")
            imports.extend(page_imports)
        if use_sd:
            imports.append("import * as steps from './steps/common_steps';")
        imports.append("")
        # Build describe block
        lines = imports + [f"test.describe('{suite.name}', () => {{"]
        for case in suite.cases:
            lines.append(f"  test('{case.name}', async ({{ page }}) => {{")
            # If scenario outline, we need to handle data
            # For simplicity, we'll just render steps as before
            for step in case.steps:
                code = self._translate_step(step, use_po, use_sd)
                for sub_line in code.splitlines():
                    lines.append(f"    {sub_line}")
            lines.append("  });")
        lines.append("});")
        return "\n".join(lines)

    def _translate_step(self, step: TestStep, use_po: bool, use_sd: bool) -> str:
        """Translate a TestStep to Playwright code, optionally using Page Objects or Step Defs."""
        action = step.action
        target = step.target
        value = step.value
        escaped_description = self._escape_string(step.description or "")

        helper_prefix = ""
        helper_target = None
        if self.quality.enable_self_healing and target and self._needs_selector_healing(action):
            escaped_target = self._escape_string(target)
            helper_prefix = f"const healed = await healSelector(page, '{escaped_target}', '{escaped_description}');\n"
            helper_target = "healed"

        # If using page objects, try to use them
        if use_po:
            # Attempt to find a page object that matches the step's URL
            # For simplicity, we'll just use the standard locator style
            pass
        # If using step defs, call the step functions
        if use_sd:
            if action == ActionType.NAVIGATE:
                return f"{helper_prefix}await steps.navigateTo(page, '{self._escape_string(value or '')}');" + self._render_visual_assertion(action, step)
            elif action == ActionType.CLICK:
                selector = helper_target or f"'{self._escape_string(target or '')}'"
                return f"{helper_prefix}await steps.clickElement(page, {selector});" + self._render_visual_assertion(action, step)
            elif action == ActionType.FILL:
                selector = helper_target or f"'{self._escape_string(target or '')}'"
                return f"{helper_prefix}await steps.fillField(page, {selector}, '{self._escape_string(value or '')}');" + self._render_visual_assertion(action, step)
            elif action == ActionType.ASSERT_TEXT:
                return f"await steps.assertText(page, '{self._escape_string(value or '')}');"
            elif action == ActionType.CHECK:
                selector = helper_target or f"'{self._escape_string(target or '')}'"
                return f"{helper_prefix}await steps.checkElement(page, {selector});" + self._render_visual_assertion(action, step)
            elif action == ActionType.UNCHECK:
                selector = helper_target or f"'{self._escape_string(target or '')}'"
                return f"{helper_prefix}await steps.uncheckElement(page, {selector});" + self._render_visual_assertion(action, step)
            elif action == ActionType.SELECT:
                selector = helper_target or f"'{self._escape_string(target or '')}'"
                return f"{helper_prefix}await steps.selectOption(page, {selector}, '{self._escape_string(value or '')}');" + self._render_visual_assertion(action, step)
            elif action == ActionType.SCREENSHOT:
                return f"{helper_prefix}await steps.assertScreenshot(page, '{self.quality.visual_snapshot_dir}/{self._safe_filename(step.description or 'screenshot')}.png');"
            elif action in {ActionType.ASSERT_VISIBLE, ActionType.ASSERT_HIDDEN}:
                selector = helper_target or f"'{self._escape_string(target or '')}'"
                method = 'assertVisible' if action == ActionType.ASSERT_VISIBLE else 'assertHidden'
                return f"{helper_prefix}await steps.{method}(page, {selector});"
            elif action == ActionType.ASSERT_VALUE:
                selector = helper_target or f"'{self._escape_string(target or '')}'"
                return f"{helper_prefix}await steps.assertValue(page, {selector}, '{self._escape_string(value or '')}');"
        # Fallback to inline code
        code = self._inline_translate(step, helper_prefix=helper_prefix, helper_target=helper_target)
        return code + self._render_visual_assertion(action, step)

    def _needs_selector_healing(self, action: ActionType) -> bool:
        return action in {
            ActionType.CLICK,
            ActionType.DOUBLE_CLICK,
            ActionType.RIGHT_CLICK,
            ActionType.HOVER,
            ActionType.FILL,
            ActionType.CHECK,
            ActionType.UNCHECK,
            ActionType.SELECT,
            ActionType.ASSERT_VISIBLE,
            ActionType.ASSERT_HIDDEN,
            ActionType.ASSERT_VALUE,
        }

    def _render_visual_assertion(self, action: ActionType, step: TestStep) -> str:
        if not self.quality.enable_visual_testing:
            return ""
        if action == ActionType.SCREENSHOT:
            return f"\nawait expect(page).toHaveScreenshot('{self.quality.visual_snapshot_dir}/{self._safe_filename(step.description or 'screenshot')}.png');"
        if action not in {
            ActionType.NAVIGATE,
            ActionType.CLICK,
            ActionType.FILL,
            ActionType.CHECK,
            ActionType.UNCHECK,
            ActionType.SELECT,
        }:
            return ""
        snapshot_name = self._safe_filename(step.description or step.target or action.value or action.name)
        snapshot_dir = self.quality.visual_snapshot_dir
        return f"\nawait expect(page).toHaveScreenshot('{snapshot_dir}/{snapshot_name}.png');"

    def _escape_string(self, value: str) -> str:
        return value.replace('\\', '\\\\').replace("'", "\\'").replace('\n', ' ').replace('\r', ' ')

    def _inline_translate(self, step: TestStep, helper_prefix: str = "", helper_target: Optional[str] = None) -> str:
        """Original inline translation (unchanged)."""
        action = step.action
        if helper_target is not None:
            target_expr = helper_target
        else:
            target_expr = f"'{self._escape_string(step.target or '')}'"
        value = step.value
        if action == ActionType.NAVIGATE:
            return f"{helper_prefix}await page.goto('{self._escape_string(value or '')}');"
        elif action == ActionType.CLICK:
            return f"{helper_prefix}await page.locator({target_expr}).click();"
        elif action == ActionType.FILL:
            return f"{helper_prefix}await page.locator({target_expr}).fill('{self._escape_string(value or '')}');"
        elif action == ActionType.ASSERT_TEXT:
            return f"{helper_prefix}await expect(page.locator('body')).toContainText('{self._escape_string(value or '')}');"
        elif action == ActionType.CHECK:
            return f"{helper_prefix}await page.locator({target_expr}).check();"
        elif action == ActionType.UNCHECK:
            return f"{helper_prefix}await page.locator({target_expr}).uncheck();"
        elif action == ActionType.SELECT:
            return f"{helper_prefix}await page.locator({target_expr}).selectOption('{self._escape_string(value or '')}');"
        elif action == ActionType.ASSERT_VISIBLE:
            return f"{helper_prefix}await expect(page.locator({target_expr})).toBeVisible();"
        elif action == ActionType.ASSERT_HIDDEN:
            return f"{helper_prefix}await expect(page.locator({target_expr})).toBeHidden();"
        elif action == ActionType.ASSERT_VALUE:
            return f"{helper_prefix}await expect(page.locator({target_expr})).toHaveValue('{self._escape_string(value or '')}');"
        else:
            return f"{helper_prefix}// UNKNOWN ACTION: {self._escape_string(step.description or '')}"

    def _safe_filename(self, name: str) -> str:
        if name is None:
            name = 'snapshot'
        return re.sub(r'[^a-zA-Z0-9_]', '_', str(name)).lower()