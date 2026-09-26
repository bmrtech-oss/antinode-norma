import { test, expect } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';

const csv = fs.readFileSync(path.join(__dirname, 'sample.csv'), 'utf8');
const [, ...rows] = csv.trim().split(/\r?\n/);

for (const row of rows) {
  const [id, title, message] = row.split(',');
  test(`${id}: ${title}`, async ({ page }) => {
    await page.goto(`data:text/html,<main>${encodeURIComponent(message)}</main>`);
    await expect(page.locator('main')).toHaveText(message);
  });
}
