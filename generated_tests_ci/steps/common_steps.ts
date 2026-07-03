import { Page, expect } from '@playwright/test';

export async function navigateTo(page: Page, url: string) {
  await page.goto(url);
}

export async function fillField(page: Page, selector: string, value: string) {
  await page.locator(selector).fill(value);
}

export async function clickElement(page: Page, selector: string) {
  await page.locator(selector).click();
}

export async function checkElement(page: Page, selector: string) {
  await page.locator(selector).check();
}

export async function uncheckElement(page: Page, selector: string) {
  await page.locator(selector).uncheck();
}

export async function selectOption(page: Page, selector: string, value: string) {
  await page.locator(selector).selectOption(value);
}

export async function assertVisible(page: Page, selector: string) {
  await expect(page.locator(selector)).toBeVisible();
}

export async function assertScreenshot(page: Page, path: string) {
  await expect(page).toHaveScreenshot({ path, fullPage: true });
}

export async function assertHidden(page: Page, selector: string) {
  await expect(page.locator(selector)).toBeHidden();
}

export async function assertValue(page: Page, selector: string, value: string) {
  await expect(page.locator(selector)).toHaveValue(value);
}

export async function assertText(page: Page, text: string) {
  await expect(page.locator('body')).toContainText(text);
}