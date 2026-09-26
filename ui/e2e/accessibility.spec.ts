import { expect, test } from '@playwright/test'

async function mockApi(page: import('@playwright/test').Page) {
  await page.route('**/api/auth/me', (route) =>
    route.fulfill({
      json: {
        user: {
          id: 'e2e-user',
          username: 'e2e_tester',
          email: 'tester@norma.local',
          roles: ['admin'],
          is_active: true,
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
        permissions: ['feature:read', 'feature:write', 'approval:action', 'audit:read', 'admin:write'],
        session_expires_at: '2026-12-31T23:59:59Z',
      },
    }),
  )
  await page.route('**/health', (route) => route.fulfill({ json: { status: 'ok', version: '1.2.3', timestamp: new Date().toISOString() } }))
  await page.route('**/api/dashboard', (route) => route.fulfill({ json: { summary: {} } }))
  await page.route('**/api/features', (route) => route.fulfill({ json: [] }))
  await page.route('**/api/approvals', (route) => route.fulfill({ json: [] }))
}

test.beforeEach(async ({ page }) => {
  await mockApi(page)
  await page.goto('/')
})

test('supports keyboard-only navigation with a visible skip link and focusable controls', async ({ page }) => {
  const skipLink = page.getByRole('link', { name: 'Skip to main content' })
  await skipLink.focus()
  await expect(skipLink).toBeFocused()
  await expect(skipLink).toBeVisible()
  await page.keyboard.press('Enter')
  await expect(page.getByRole('main')).toBeFocused()

  await page.getByRole('button', { name: 'Open settings' }).focus()
  await expect(page.getByRole('button', { name: 'Open settings' })).toBeFocused()
  await page.keyboard.press('Enter')
  await expect(page.getByRole('region', { name: 'Settings' })).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(page.getByRole('region', { name: 'Settings' })).toBeHidden()
})

test('exposes navigation, form controls, and status semantics to assistive technology', async ({ page }) => {
  const navigation = page.getByRole('tablist', { name: 'Primary navigation' }).first()
  await expect(navigation.getByRole('tab')).toHaveCount(6)
  await expect(page.getByRole('main')).toHaveAttribute('id', 'main-content')
  await expect(page.getByRole('status').filter({ hasText: 'API:' })).toBeVisible()

  await page.getByRole('tab', { name: 'Generation' }).click()
  await expect(page.getByLabel('Choose a CSV or XLSX file')).toHaveAttribute('accept', /csv/)
  await expect(page.getByRole('button', { name: 'Upload and validate' })).toBeVisible()
  await expect(page.getByRole('status')).toContainText('Online')
})

test('keeps responsive navigation keyboard and screen-reader usable', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 720 })
  const menuButton = page.getByRole('button', { name: 'Open navigation menu' })
  await menuButton.focus()
  await page.keyboard.press('Enter')
  await expect(menuButton).toHaveAttribute('aria-expanded', 'true')

  const mobileNavigation = page.locator('#mobile-navigation')
  await expect(mobileNavigation).toBeVisible()
  await expect(mobileNavigation.getByRole('tab', { name: 'Feature Review' })).toBeVisible()
  await mobileNavigation.getByRole('tab', { name: 'Feature Review' }).focus()
  await page.keyboard.press('Enter')
  await expect(mobileNavigation).toBeHidden()
  await expect(page.getByRole('heading', { name: 'Feature Review' })).toBeVisible()
})
