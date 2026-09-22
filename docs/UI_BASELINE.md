# UI Baseline — UI-1-T01

**ADR:** [ADR-009](adr/ADR-009-frontend-quality-and-theming.md)
**Captured:** 2026-09-22
**Scope:** `ui/` React application before design-system and theme migration
**Purpose:** Establish a reproducible baseline for the >9/10 frontend improvement target.

## 1. Current implementation baseline

| Area | Current state |
|---|---|
| Framework | React 18, TypeScript, Vite |
| Styling | Tailwind CSS utility classes |
| Runtime dependencies | React, React DOM, Lucide React |
| Application shell | Single `App` component with tab-based navigation |
| Views | Dashboard, Feature Review, Approval Queue, Traceability, Audit Trail |
| Theme | System, light, and dark modes with persisted preference and accessible switcher |
| Routing | No React Router; views are selected from local component state |
| Data access | Page-level `fetch` calls with local loading state |
| Shared components | No shared UI primitive layer |
| Test tooling | Vitest and Testing Library component tests are configured |
| Linting | Script exists, but ESLint is not declared/available in the current UI install |
| Build | `npm --prefix ui run build` passes |

The current source of truth for the implementation is the `ui/src/` tree. Existing documentation that describes React Query, React Router, Recharts, or routes such as `/features` and `/analytics` should be treated as target-state documentation until those surfaces exist in code.

## 2. Baseline commands and results

Commands run from the repository root:

```text
npm --prefix ui run build
```

Result:

```text
PASS — TypeScript compilation and Vite production build
Output — ui/dist/assets/index-xIMV5YIt.js
Gzip size — 51.03 kB
```

```text
npm --prefix ui run test
```

Result:

```text
PASS — 4 test files, 8 component tests
Coverage — Button, AsyncState, ConfirmationDialog, ThemeSwitcher
```

```text
cd ui && npm run test:e2e
```

Result:

```text
PASS — 3 Chromium workflows covering theme persistence, feature filtering, and approval confirmation.
```

```text
npm --prefix ui run lint
npm --prefix ui run typecheck
npm --prefix ui run test
npm --prefix ui run test:e2e
npm --prefix ui run build
```

Result:

```text
PASS — UI quality gates are now configured and enforced locally and in CI.
```

The lint and type-checking gap has been resolved as part of UI-4-T04. The UI now runs a measured quality gate that includes lint, typecheck, unit tests, browser E2E/visual checks, and a production build.

## 3. Browser support matrix

The acceptance matrix is checked in at [`ui/ui-baseline.config.json`](../ui/ui-baseline.config.json).

| Browser engine | Baseline role |
|---|---|
| Chromium | Primary acceptance browser |
| Firefox | Secondary acceptance browser |
| WebKit | Secondary acceptance browser |

The application should continue to support the latest stable versions available in the project’s approved browser-test environment. Exact browser versions should be pinned when browser automation is introduced.

## 4. Viewport matrix

| Name | Width | Height | Intended coverage |
|---|---:|---:|---|
| Mobile | 320 | 720 | Minimum narrow layout and overflow checks |
| Tablet | 768 | 1024 | Responsive navigation and table behavior |
| Desktop | 1024 | 768 | Standard application workspace |
| Wide | 1440 | 900 | Full dashboard and content density |

Each primary view must be reviewed at every viewport before the UI-1 exit gate is accepted. The current baseline captures dark mode only; the light token set is now available, while system selection and the user-facing theme switcher are introduced by UI-1-T03.

## 5. Baseline screenshot set

The checked-in capture configuration defines the screenshot set:

- Dashboard
- Feature Review
- Approval Queue
- Traceability
- Audit Trail

The visual regression suite captures Dashboard, Feature Review, and Approval Queue at the mobile and wide viewports in both light and dark themes. Baselines are stored under `docs/ui-baseline/` and reviewed in pull requests. The full viewport matrix remains the manual responsive acceptance matrix; adding a new baseline requires updating both the Playwright visual spec and this configuration.

## 6. Baseline observations

### Strengths

- The primary product areas are visible from a single shell.
- The production build is currently passing.
- The UI has a clear governance-oriented information architecture.
- Existing dark styling provides a usable visual starting point for semantic token migration.

### Gaps to address

- Review semantic light/dark color tokens at every primary surface and migrate remaining hard-coded page colors.
- Add a shared component layer instead of repeating page-level utility combinations.
- Add explicit API error and retry states.
- Add accessible focus, labels, keyboard navigation, and status announcements.
- Add responsive table/card behavior for traceability and audit views.
- Add browser, component, accessibility, and visual regression checks.
- Add ESLint to the UI dependency/tooling path and make lint a passing CI gate.

## 7. UI-1-T01 exit criteria

- [x] Current UI structure and implementation limits documented.
- [x] Browser matrix documented.
- [x] Viewport matrix documented.
- [x] Baseline capture configuration checked in.
- [x] Production build executed and result recorded.
- [x] Lint/tooling gap recorded without silently ignoring the failure.
- [x] Semantic light/dark token foundation added while preserving dark mode as the default.
- [x] Theme provider, persisted mode, system preference handling, and accessible switcher added.
- [x] Shared application shell, navigation metadata, status region, and responsive shell layout extracted.
- [x] Application-owned shadcn-style primitives added for buttons, badges, cards, skeletons, and alerts.
- [x] Shared typed JSON API client added with normalized HTTP errors and abort-signal support.
- [x] Shared loading, empty, and retryable error states adopted across primary views.
- [x] Approval mutations include confirmation, progress, success/error feedback, and duplicate-submission protection.
- [x] Keyboard skip navigation, view focus restoration, tab semantics, and live/busy status regions added.
- [x] Contrast/status audit documented and primary status indicators include text plus icons rather than color alone.
- [x] Feature review supports search, status filtering, deterministic sorting, result counts, and detail metadata.
- [x] Approval queue supports search/status filters, reviewer context, accessible confirmation, and action history.
- [x] Traceability supports filtering, uncovered-requirement navigation, and responsive table/card presentation.
- [x] Audit trail supports action/actor filters, bounded pagination, and expandable payload/hash details.
- [x] Dashboard presents supported KPI snapshots, approval distribution, operational context, and avoids unsupported historical trends.
- [x] Shared component tests cover buttons, asynchronous states, confirmation dialogs, and theme switching.
- [x] Browser workflows cover theme persistence, feature review filtering, and approval confirmation.
- [x] Light/dark visual snapshots captured for the key mobile and wide viewports.

The final unchecked item is intentionally carried into the visual-regression setup work. It must be completed before UI-4-T03 is accepted.
