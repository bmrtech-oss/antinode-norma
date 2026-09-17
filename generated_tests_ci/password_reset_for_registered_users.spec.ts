import { test, expect } from "@playwright/test";

test.describe("Password reset for registered users", () => {
  test("Forgot Password link is displayed on the login page", async ({
    page,
  }) => {
    await page.goto("https://example.com/login");
    await expect(page.locator("body")).toContainText("Forgot Password");
  });
  test("Receive password reset email within 2 minutes", async ({ page }) => {
    await page.goto("https://example.com/login");
    const forgotLocator = page.locator("text=Forgot password");
    await forgotLocator.waitFor({ state: "visible", timeout: 10000 });
    await forgotLocator.click();
    const emailLocator = page.locator("#email");
    await emailLocator.waitFor({ state: "visible", timeout: 10000 });
    await emailLocator.fill("user@example.com");
    await expect(page.locator("body")).toContainText("reset email sent");
    await expect(page.locator("body")).toContainText("email received");
  });
  test("Reset link is secure and expires after 1 hour", async ({ page }) => {
    await page.goto("https://example.com/reset");
    const linkLocator = page.locator("text=reset link in the email");
    await linkLocator.waitFor({ state: "visible", timeout: 10000 });
    await linkLocator.click();
    await expect(page.locator("body")).toContainText("reset link secure");
    await expect(page.locator("body")).toContainText("reset link expires");
  });
  test("Set a new password and receive confirmation", async ({ page }) => {
    await page.goto("https://example.com/reset");
    const passLocator = page.locator("#new-password");
    await passLocator.waitFor({ state: "visible", timeout: 10000 });
    await passLocator.fill("new_secure_password");
    await expect(page.locator("body")).toContainText("password updated");
    await expect(page.locator("body")).toContainText(
      "password set confirmation",
    );
  });
  test("Login with the new password", async ({ page }) => {
    await page.goto("https://example.com");
    await page.goto("https://example.com/dashboard");
    await expect(page.locator("body")).toContainText("login successful");
  });
});
