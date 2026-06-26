# Visual Testing (Phase 4)

This document describes how Antinode Norma integrates visual testing into generated Playwright tests and how to create baseline snapshots.

Summary
- Generator: emits `expect(page).toHaveScreenshot('...')` assertions when `enable_visual_testing` is enabled.
- CLI flags: `--enable-visual-testing` and `--visual-snapshot-dir` control assertions and the preferred snapshot path.
- Baselines: Playwright writes snapshot PNGs when you run tests with `--update-snapshots`.

How it works
- The Playwright emitter injects inline `expect(page).toHaveScreenshot('<relative-path>.png')` calls for supported step types.
- During test execution, Playwright will write actual snapshot images and, when run with `--update-snapshots`, will populate baseline PNGs.

Typical workflow
1. Generate tests with visual assertions enabled:

```bash
python -m antinode_norma.codegen.cli.commands generate \
  -f features/login.feature \
  --enable-visual-testing \
  --visual-snapshot-dir visual-snapshots \
  -fw playwright \
  -o generated_tests
```

2. Install Node deps and browsers (once):

```bash
npm install
npx playwright install --with-deps
```

3. Run Playwright to create baseline snapshots (writes PNG baselines):

```bash
# Run all generated Playwright tests and update snapshots
npx playwright test generated_tests/playwright --project=chromium --update-snapshots
```

4. Export the JSON report and teach Norma from failures:

```bash
npx playwright test generated_tests/playwright --project=chromium --reporter=json > playwright-report.json
python -m antinode_norma.cli learn --report-file playwright-report.json --show-recent --show-suggestions
```

This command stores failure patterns in a local SQLite database and helps the generator avoid repeated failure modes. The `--show-suggestions` flag prints step-level healing recommendations based on the stored failure patterns.

Notes about snapshot locations
- Playwright may place snapshots in per-spec snapshot folders named like `your.spec.ts-snapshots/` and/or under the configured path used in the emitted assertion (for example `visual-snapshots/`).
- The emitter attempts to use the configured `visual_snapshot_dir` (relative to the emitter output dir). If your project prefers a single snapshot folder, set `--visual-snapshot-dir visual-snapshots` when generating.
- The generator cannot produce PNGs itself; you must run Playwright to create baselines.

Git & CI recommendations
- Ignore transient Playwright outputs in Git (see `.gitignore`).
- Commit baseline snapshots intentionally: once you have reviewed and approved the generated baselines, add them to source control (or store them in a snapshot artifacts bucket).
- In CI, run Playwright tests with `--update-snapshots` in a controlled job when approving new baselines, then use snapshot comparison in subsequent runs.

Troubleshooting
- If locators time out during generated tests, the generator may have used simple CSS selectors for example pages; adjust selectors via `codegen.yaml` (`selector_strategy`) or edit the generated `steps/common_steps.ts`.
- If snapshots are not written where you expect, re-run generation with `--visual-snapshot-dir` set and re-run Playwright with `--update-snapshots`.

Example: create baselines and collect them into a central folder

```bash
# 1) Generate with a visual snapshot dir
python -m antinode_norma.codegen.cli.commands generate -f features/login.feature --enable-visual-testing --visual-snapshot-dir visual-snapshots -o generated_tests -fw playwright

# 2) Run Playwright to write baselines
npx playwright test generated_tests/playwright --project=chromium --update-snapshots

# 3) (Optional) gather per-spec snapshots into one place (example)
# This step is repository-specific. A simple approach is to copy all PNGs from *-snapshots/ folders into generated_tests/playwright/visual-snapshots/
```

If you need help integrating visual testing into your CI pipeline, I can add a small helper script and CI job example. 