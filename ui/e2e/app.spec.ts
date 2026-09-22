import { expect, test } from '@playwright/test'

const features = [
  {
    id: 'feature-login',
    title: 'User login',
    gherkin: 'Feature: User login',
    status: 'READY',
    created_at: '2026-09-22T10:00:00Z',
  },
  {
    id: 'feature-export',
    title: 'Export report',
    gherkin: 'Feature: Export report',
    status: 'DRAFT',
    created_at: '2026-09-21T10:00:00Z',
  },
]

const approvals = [
  {
    id: 'approval-1',
    feature_id: 'feature-login',
    gherkin_text: 'Feature: User login',
    status: 'PENDING',
    requested_by: 'author',
    created_at: '2026-09-22T10:00:00Z',
  },
]

async function mockApi(page: import('@playwright/test').Page) {
  await page.route('**/health', async (route) => {
    await route.fulfill({ json: { status: 'ok', version: '1.2.3', timestamp: new Date().toISOString() } })
  })
  await page.route('**/api/features', async (route) => {
    await route.fulfill({ json: features })
  })
  await page.route('**/api/approvals', async (route) => {
    await route.fulfill({ json: approvals })
  })
  await page.route('**/api/dashboard', async (route) => {
    await route.fulfill({ json: { summary: {} } })
  })
}

test.beforeEach(async ({ page }) => {
  await mockApi(page)
  await page.goto('/')
})

test('switches theme and persists the selected mode', async ({ page }) => {
  await expect(page.locator('main')).toBeFocused()
  await page.getByRole('button', { name: 'Open settings' }).click()
  await page.getByRole('button', { name: /Theme:.*Switch to Light theme/ }).click()
  await expect(page.locator('html')).toHaveClass(/light/)
  await expect(page.getByRole('button', { name: /Theme: Light theme/ })).toBeVisible()

  await page.reload()
  await page.getByRole('button', { name: 'Open settings' }).click()
  await expect(page.locator('html')).toHaveClass(/light/)
})

test('filters feature review results', async ({ page }) => {
  await page.getByRole('tab', { name: 'Feature Review' }).click()
  await expect(page.getByRole('heading', { name: 'Feature Review' })).toBeVisible()
  await expect(page.getByText('Showing 2 of 2 features')).toBeVisible()

  await page.getByLabel('Search features').fill('export')
  await expect(page.getByText('Showing 1 of 2 features')).toBeVisible()
  await expect(page.getByRole('button', { name: /Export report/ })).toBeVisible()
  await expect(page.getByRole('button', { name: /User login/ })).toHaveCount(0)
})

test('opens the mobile sidebar and selects a view', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 720 })
  await page.getByRole('button', { name: 'Open navigation menu' }).click()
  await expect(page.locator('#mobile-navigation')).toBeVisible()
  await page.getByRole('tab', { name: 'Feature Review' }).click()
  await expect(page.locator('#mobile-navigation')).toBeHidden()
  await expect(page.getByRole('heading', { name: 'Feature Review' })).toBeVisible()
})

test('confirms and completes an approval action', async ({ page }) => {
  await page.getByRole('tab', { name: 'Approval Queue' }).click()
  await expect(page.getByRole('heading', { name: 'Governance Approval Queue' })).toBeVisible()
  await page.getByRole('button', { name: 'Approve Feature' }).click()

  const dialog = page.getByRole('dialog')
  await expect(dialog).toBeVisible()
  await expect(dialog).toContainText('Approve feature?')
  await expect(dialog).toContainText('This will approve feature-login')

  await page.route('**/api/approvals/approval-1/approve', async (route) => {
    await route.fulfill({ json: { ...approvals[0], status: 'APPROVED' } })
  })
  const approvalResponse = page.waitForResponse('**/api/approvals/approval-1/approve')
  await dialog.getByRole('button', { name: 'Approve feature' }).click()
  await expect((await approvalResponse).status()).toBe(200)
  await expect(dialog).toBeHidden()
  await expect(page.getByRole('alert')).toContainText('feature-login was approved.')
})
