import { test, expect } from "@playwright/test";

test.describe("User Login", () => {
  test("Successful login with valid credentials", async ({ page }) => {
    await page.goto("https://example.com/login");
    await page.locator("#email").waitFor({ state: "visible", timeout: 10000 });
    await page.locator("#email").fill("testuser@example.com");
    await page
      .locator("#password")
      .waitFor({ state: "visible", timeout: 10000 });
    await page.locator("#password").fill("SecurePass123");
    await page
      .locator("#login-button")
      .waitFor({ state: "visible", timeout: 10000 });
    await page.locator("#login-button").click();
    await expect(page.locator("body")).toContainText("Welcome back, Test User");
    // UNKNOWN ACTION: And the URL should be "https://example.com/dashboard"
  });
  test("Failed login with invalid password", async ({ page }) => {
    await page.goto("https://example.com/login");
    await page.locator("#email").waitFor({ state: "visible", timeout: 10000 });
    await page.locator("#email").fill("testuser@example.com");
    await page
      .locator("#password")
      .waitFor({ state: "visible", timeout: 10000 });
    await page.locator("#password").fill("WrongPass");
    await page
      .locator("#login-button")
      .waitFor({ state: "visible", timeout: 10000 });
    await page.locator("#login-button").click();
    await expect(page.locator("body")).toContainText("Invalid credentials");
    // UNKNOWN ACTION: And the URL should be "https://example.com/login"
  });
});
