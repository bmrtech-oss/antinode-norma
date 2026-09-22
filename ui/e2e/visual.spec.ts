import { expect, test, type Page } from '@playwright/test'

const viewports = [
  { name: 'mobile', width: 320, height: 720 },
  { name: 'wide', width: 1440, height: 900 },
]

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

async function mockApi(page: Page) {
  await page.route('**/health', async (route) => {
    await route.fulfill({ json: { status: 'ok', version: '1.2.3', timestamp: '2026-09-22T10:00:00Z' } })
  })
  await page.route('**/api/features', async (route) => {
    await route.fulfill({ json: features })
  })
  await page.route('**/api/approvals', async (route) => {
    await route.fulfill({ json: approvals })
  })
  await page.route('**/api/dashboard', async (route) => {
    await route.fulfill({
      json: {
        summary: {
          total_features: 24,
          total_approvals: 8,
          pending_approvals: 2,
          approved_count: 5,
          rejected_count: 1,
          total_audit_events: 42,
          quality_gate_pass_rate: 0.875,
          system_status: 'operational',
        },
      },
    })
  })
}

const views = [
  { name: 'dashboard', tab: null, heading: 'Norma BDD Platform Overview' },
  { name: 'feature-review', tab: 'Feature Review', heading: 'Feature Review' },
  { name: 'approval-queue', tab: 'Approval Queue', heading: 'Governance Approval Queue' },
]

for (const theme of ['dark', 'light'] as const) {
  for (const viewport of viewports) {
    for (const view of views) {
      test(`${theme} ${viewport.name} ${view.name}`, async ({ page }) => {
        await page.setViewportSize({ width: viewport.width, height: viewport.height })
        await page.addInitScript((selectedTheme) => {
          window.localStorage.setItem('norma-ui-theme', selectedTheme)
        }, theme)
        await mockApi(page)
        await page.goto('/')

        if (view.tab) {
          if (viewport.name === 'mobile') {
            await page.getByRole('button', { name: 'Open navigation menu' }).click()
          }
          await page.getByRole('tab', { name: view.tab }).click()
        }
        await expect(page.getByRole('heading', { name: view.heading })).toBeVisible()
        await expect(page).toHaveScreenshot(`${theme}-${viewport.name}-${view.name}.png`, {
          fullPage: true,
          animations: 'disabled',
        })
      })
    }
  }
}
