import { test, expect } from '@playwright/test';
import { LoginPage } from './pages/loginpage.page';
import { ResetPage } from './pages/resetpage.page';
import { HomePage } from './pages/homepage.page';
import { DashboardPage } from './pages/dashboardpage.page';
import * as steps from './steps/common_steps';

test.describe('Password reset for registered users', () => {
  test('Forgot Password link is displayed on the login page', async ({ page }) => {
    await steps.navigateTo(page, 'https://example.com/login');
    await steps.assertText(page, 'Forgot Password');
  });
  test('Receive password reset email within 2 minutes', async ({ page }) => {
    await steps.navigateTo(page, 'https://example.com/login');
    await steps.clickElement(page, 'text=Forgot password');
    await steps.fillField(page, '#email', 'user@example.com');
    await steps.assertText(page, 'reset email sent');
    await steps.assertText(page, 'email received');
  });
  test('Reset link is secure and expires after 1 hour', async ({ page }) => {
    await steps.navigateTo(page, 'https://example.com/reset');
    await steps.clickElement(page, 'text=reset link in the email');
    await steps.assertText(page, 'reset link secure');
    await steps.assertText(page, 'reset link expires');
  });
  test('Set a new password and receive confirmation', async ({ page }) => {
    await steps.navigateTo(page, 'https://example.com/reset');
    await steps.fillField(page, '#new-password', 'new_secure_password');
    await steps.assertText(page, 'password updated');
    await steps.assertText(page, 'password set confirmation');
  });
  test('Login with the new password', async ({ page }) => {
    await steps.navigateTo(page, 'https://example.com');
    await steps.navigateTo(page, 'https://example.com/dashboard');
    await steps.assertText(page, 'login successful');
  });
});