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
  await page.route('**/api/auth/me', async (route) => {
    await route.fulfill({
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
    })
  })
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

test('uploads a CSV and downloads a generated artifact', async ({ page }) => {
  let generated = false
  const job = {
    id: 'generation-1',
    import_id: 'import-1',
    status: 'completed',
    result: { valid: true, errors: [] },
    created_at: '2026-09-22T10:00:00Z',
    total_rows: 1,
    processed_rows: 1,
    successful_rows: 1,
    warning_rows: 0,
    failed_rows: 0,
    current_item: null,
    progress_percent: 100,
    error: null,
    source_filename: 'cases.csv',
  }
  const artifact = {
    id: 'result-1',
    row_number: 1,
    case_id: 'TC-1',
    status: 'completed',
    artifact_name: 'TC-1.feature',
    warnings: [],
    error: null,
    content: 'Feature: Login\n\n  Scenario: Login',
  }

  await page.route('**/v1/imports**', async (route) => {
    const request = route.request()
    if (request.method() === 'POST' && request.url().endsWith('/v1/imports')) {
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'import-1',
          filename: 'cases.csv',
          format: 'csv',
          status: 'uploaded',
          row_count: 1,
          columns: ['ID', 'Summary', 'Action'],
          worksheet_names: [],
          worksheet: null,
          mapping: {},
          created_at: '2026-09-22T10:00:00Z',
        }),
      })
      return
    }
    if (request.url().includes('/preview')) {
      await route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'import-1',
          filename: 'cases.csv',
          format: 'csv',
          row_count: 1,
          columns: ['ID', 'Summary', 'Action'],
          worksheet_names: [],
          worksheet: null,
          mapping: {},
          truncated: false,
          rows: [{ source_row: 2, values: { ID: 'TC-1', Summary: 'Login', Action: 'log in' } }],
        }),
      })
      return
    }
    if (request.url().includes('/validate')) {
      await route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({ import_id: 'import-1', valid: true, row_count: 1, errors: [] }),
      })
      return
    }
    await route.continue()
  })

  await page.route('**/v1/generation-jobs**', async (route) => {
    const request = route.request()
    const url = request.url()
    if (request.method() === 'POST' && url.endsWith('/v1/generation-jobs')) {
      generated = true
      await route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify(job) })
      return
    }
    if (url.includes('/results/') && url.endsWith('/download')) {
      await route.fulfill({
        contentType: 'text/plain',
        headers: { 'Content-Disposition': 'attachment; filename="TC-1.feature"' },
        body: artifact.content,
      })
      return
    }
    if (url.endsWith('/results')) {
      await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ job_id: job.id, results: [artifact], count: 1 }) })
      return
    }
    if (url.endsWith('/generation-jobs') || url.includes('/generation-jobs?')) {
      await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ items: generated ? [job] : [], total: generated ? 1 : 0, offset: 0, limit: 20 }) })
      return
    }
    if (url.endsWith('/generation-1')) {
      await route.fulfill({ contentType: 'application/json', body: JSON.stringify(job) })
      return
    }
    await route.continue()
  })

  await page.getByRole('tab', { name: 'Generation' }).click()
  await page.locator('input[type="file"]').setInputFiles({
    name: 'cases.csv',
    mimeType: 'text/csv',
    buffer: Buffer.from('ID,Summary,Action\nTC-1,Login,log in\n'),
  })
  await page.getByRole('button', { name: 'Upload and validate' }).click()
  await expect(page.getByText('Import validation')).toBeVisible()
  await page.getByRole('button', { name: 'Validate import' }).click()
  await expect(page.getByText('Passed')).toBeVisible()
  await page.getByRole('button', { name: 'Start generation' }).click()
  await expect(page.getByRole('heading', { name: 'Generation job' })).toBeVisible()
  await expect(page.getByText('TC-1 · row 1')).toBeVisible()

  await page.getByRole('button', { name: 'Preview' }).click()
  await expect(page.getByText('Feature: Login')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Download' })).toHaveCount(2)
  const downloadRequest = page.waitForRequest(/\/v1\/generation-jobs\/generation-1/)
  await page.getByRole('button', { name: 'Download' }).nth(1).click()
  await expect((await downloadRequest).url()).toContain('/results/result-1/download')
})
