import { defineConfig, devices } from '@playwright/test'

const devPort = process.env.PLAYWRIGHT_DEV_PORT ?? '3000'
const baseURL = `http://localhost:${devPort}`

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? 'html' : 'list',
  snapshotPathTemplate: '{testDir}/../../docs/ui-baseline/{testFilePath}/{arg}{ext}',
  use: {
    baseURL,
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: `npm run dev -- --port ${devPort}`,
    url: baseURL,
    reuseExistingServer: !process.env.CI,
  },
})
