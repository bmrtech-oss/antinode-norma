"""Generate reusable step definition functions."""

from pathlib import Path

from .base import Emitter
from ..models.test_model import TestSuite


class StepDefEmitter(Emitter):
    def emit(self, suite: TestSuite, output_dir: Path) -> None:
        self._ensure_output_dir(output_dir)
        content = self._render(suite)
        self._write_file(output_dir / "common_steps.ts", content)

    def _render(self, suite: TestSuite) -> str:
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
            "export async function assertHidden(page: Page, selector: string) {",
            "  await expect(page.locator(selector)).toBeHidden();",
            "}",
            "",
            "export async function assertText(page: Page, expected: string) {",
            "  await expect(page.locator('body')).toContainText(expected);",
            "}",
            "",
            "export async function assertValue(page: Page, selector: string, expected: string) {",
            "  await expect(page.locator(selector)).toHaveValue(expected);",
            "}",
            "",
            "export async function assertScreenshot(page: Page, path: string) {",
            "  await expect(page).toHaveScreenshot({ path, fullPage: true });",
            "}",
            "",
            f"// Generated from {suite.name}.",
        ]
        return "\n".join(lines)
