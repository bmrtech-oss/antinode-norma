import { expect, test } from '@playwright/test'

test.describe('OIDC Login, User Identity & Logout E2E Flow', () => {
  test('renders LoginPage when unauthenticated and redirects on sign in', async ({ page }) => {
    // Mock /api/auth/me returning 401 Unauthorized
    await page.route('**/api/auth/me', (route) => route.fulfill({ status: 401, json: { detail: 'Unauthenticated' } }))
    await page.route('**/health', (route) => route.fulfill({ json: { status: 'ok', version: '1.0.0' } }))

    let loginRequested = false
    await page.route('**/api/auth/oidc/login*', (route) => {
      loginRequested = true
      return route.fulfill({ json: { authorization_url: 'https://auth.example.com/login?state=test123', state: 'test123' } })
    })

    await page.goto('/')

    await expect(page.getByText('Sign in to Antinode Norma')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Sign in with Identity Provider' })).toBeVisible()

    await page.getByRole('button', { name: 'Sign in with Identity Provider' }).click()

    expect(loginRequested).toBe(true)
  })

  test('displays UserMenu for authenticated user and performs logout', async ({ page }) => {
    let loggedIn = true

    await page.route('**/api/auth/me', (route) => {
      if (loggedIn) {
        return route.fulfill({
          json: {
            user: {
              id: 'u-e2e',
              username: 'e2e_admin',
              email: 'admin@norma.local',
              roles: ['admin', 'reviewer'],
              display_name: 'E2E Admin User',
              is_active: true,
              created_at: '2026-01-01',
              updated_at: '2026-01-01',
            },
            permissions: ['feature:read', 'admin:write'],
            session_expires_at: '2026-12-31T23:59:59Z',
          },
        })
      }
      return route.fulfill({ status: 401, json: { detail: 'Logged out' } })
    })

    await page.route('**/health', (route) => route.fulfill({ json: { status: 'ok', version: '1.0.0' } }))
    await page.route('**/api/dashboard', (route) => route.fulfill({ json: { summary: {} } }))

    await page.route('**/api/auth/logout', (route) => {
      loggedIn = false
      return route.fulfill({ json: { status: 'logged_out' } })
    })

    await page.goto('/')

    // UserMenu button displays in header
    const userMenuButton = page.getByRole('button', { name: /User menu for E2E Admin User/ })
    await expect(userMenuButton).toBeVisible()

    // Open UserMenu
    await userMenuButton.click()
    await expect(page.getByRole('menu')).toBeVisible()
    await expect(page.getByText('admin@norma.local')).toBeVisible()
    await expect(page.getByText('admin', { exact: true })).toBeVisible()

    // Click Sign Out
    await page.getByRole('menuitem', { name: 'Sign Out' }).click()

    // User is signed out and redirected to LoginPage
    await expect(page.getByText('Sign in to Antinode Norma')).toBeVisible()
  })
})
