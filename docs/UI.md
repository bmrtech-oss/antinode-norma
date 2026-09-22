# Web UI & Frontend Runbook — Antinode Norma

This document is the current implementation guide for the React frontend in `ui/`. It reflects the code that exists today and is the source of truth for local development, component work, and release checks.

Related references:
- [WEB_UI.md](WEB_UI.md) — product-oriented overview of the web UI.
- [UI_BASELINE.md](UI_BASELINE.md) — baseline, viewport matrix, and acceptance evidence.
- [UI_CONTRAST_AUDIT.md](UI_CONTRAST_AUDIT.md) — semantic token and contrast audit.

---

## 1. Current architecture

The frontend is a single-page React app that runs in Vite during development and builds to static assets for deployment.

- **App shell**: `ui/src/App.tsx` and `ui/src/components/AppShell.tsx`
- **Theme system**: `ui/src/theme.tsx` with `system`, `light`, and `dark` modes plus persisted preference
- **Styling**: Tailwind CSS with semantic color tokens defined in `ui/src/index.css`
- **Data access**: `ui/src/lib/api.ts` wraps JSON fetches with normalized error handling and abort support
- **Navigation**: local tab state inside the app shell; there is no React Router in the current implementation. Desktop uses a collapsible sidebar; mobile uses an accessible slide-out menu.
- **Primary views**: Dashboard, Feature Review, Approval Queue, Traceability, and Audit Trail in `ui/src/components/`
- **Primitive layer**: app-owned UI components in `ui/src/components/ui/` instead of app-specific ad hoc markup

The current implementation deliberately avoids unsupported target-state features such as a router, React Query, or a static analytics dashboard unless those files are actually present in the codebase.

---

## 2. Local development runbook

### Install dependencies

```bash
cd ui
npm install
```

### Start the dev server

```bash
cd ui
npm run dev
```

The Vite app runs on port `3000` and proxies `/api` and `/health` to the FastAPI backend at `http://localhost:8000` via `ui/vite.config.ts`.

### Quality gate commands

```bash
cd ui
npm run lint
npm run typecheck
npm run test
npm run test:e2e
npm run build
```

The consolidated local gate is:

```bash
cd ui
npm run ci:ui
```

---

## 3. Component contribution guide

### 3.1 Use app-owned primitives first

Add reusable UI behavior to `ui/src/components/ui/` before inlining repeated markup into feature components. Shared primitives include `Button`, `Badge`, `Card`, `Alert`, `AsyncState`, and `ConfirmationDialog`.

### 3.2 Prefer semantic design tokens

Do not add ad hoc hard-coded colors when the interface already has semantic tokens. Use the Tailwind classes mapped in `ui/src/index.css`, such as `bg-background`, `text-foreground`, `border-border`, `bg-success`, and `text-muted-foreground`.

### 3.3 Keep API access centralized

All JSON requests should flow through `getJson` and `postJson` in `ui/src/lib/api.ts`. Avoid direct `fetch()` calls in page-level components.

### 3.4 Model async states consistently

For any data-fetching view, handle the following states explicitly:
- loading
- empty
- error with retry
- successful content

Use the shared patterns in `ui/src/components/ui/AsyncState.tsx`.

### 3.5 Accessibility is a release requirement

Every new interactive element should consider:
- visible focus style
- accessible name/label
- keyboard operation
- `aria-live`/status messaging for async updates
- dialog semantics for confirmation flows

### 3.6 Test expectations

Component work should be validated with the relevant test level:
- unit/component tests for shared primitives and mode logic under `ui/src/components/**/*.test.tsx`
- browser E2E tests for workflow flows under `ui/e2e/`
- visual regression snapshots for key pages and themes under `docs/ui-baseline/`

---

## 4. Release checklist entry

Before a frontend release is signed off, confirm all of the following:

- [ ] `npm --prefix ui run ci:ui` passes locally
- [ ] visual baselines under `docs/ui-baseline/` are reviewed and accepted
- [ ] UI snapshots remain within the approved viewport/theme matrix
- [ ] no stale UI documentation describes features that are not present in code
- [ ] accessibility and theme changes have been checked in both light and dark modes

This checklist item should be recorded in the release sign-off process in [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md).
