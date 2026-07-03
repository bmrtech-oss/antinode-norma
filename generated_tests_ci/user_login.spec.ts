import { test, expect } from '@playwright/test';
import { LoginPage } from './pages/loginpage.page';
import * as steps from './steps/common_steps';

test.describe('User Login', () => {
  test('Successful login with valid credentials', async ({ page }) => {
    await steps.navigateTo(page, 'https://example.com/login');
    await steps.fillField(page, '#email', 'testuser@example.com');
    await steps.fillField(page, '#password', 'SecurePass123');
    await steps.clickElement(page, '#login-button');
    await steps.assertText(page, 'Welcome back, Test User');
    // UNKNOWN ACTION: And the URL should be "https://example.com/dashboard"
  });
  test('Failed login with invalid password', async ({ page }) => {
    await steps.navigateTo(page, 'https://example.com/login');
    await steps.fillField(page, '#email', 'testuser@example.com');
    await steps.fillField(page, '#password', 'WrongPass');
    await steps.clickElement(page, '#login-button');
    await steps.assertText(page, 'Invalid credentials');
    // UNKNOWN ACTION: And the URL should be "https://example.com/login"
  });
});