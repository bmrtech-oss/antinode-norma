# ADR-009: Frontend Quality, Design System, and Theme Support

**Status:** Proposed
**Date:** 2026-09-22
**Deciders:** Engineering Lead, UX Lead, QA Architect, Product Owner
**Scope:** `ui/` React application
**Related:** ADR-002 platform hardening, ADR-003 Aegis platform extension
**Target UI score:** >9.0/10, measured against the scorecard in §7

---

## 1. Context

The current UI is a coherent React/Vite dashboard with working surfaces for:

- platform health and dashboard metrics;
- generated feature review;
- approval workflow;
- requirement-to-scenario traceability; and
- audit trail inspection.

The current implementation is a useful functional prototype, but it is not yet a product-grade frontend. The principal gaps are:

- duplicated styling and no shared component primitives;
- dark-only visual treatment with no user-selectable light theme;
- inconsistent loading, empty, error, and mutation feedback states;
- limited search, filtering, sorting, pagination, and detail interactions;
- no shared API/error boundary or query lifecycle abstraction;
- limited keyboard, screen-reader, focus, and contrast validation;
- no frontend unit/component/e2e test strategy;
- no visual regression or responsive acceptance gate; and
- dashboard presentation that is mostly metric cards rather than decision-support analysis.

The UI should improve without changing the backend contract unnecessarily. The design system must support the existing governance-oriented product language while making future Aegis surfaces easier to build consistently.

---

## 2. Decision

We will evolve the `ui/` application into an accessible, tested, responsive product interface using:

1. **Tailwind CSS tokens** as the styling foundation.
2. **Radix UI primitives** for accessible behavior-heavy controls such as dialogs, dropdown menus, tabs, tooltips, popovers, selects, and toasts.
3. **shadcn/ui patterns and generated components** for composable application-owned components built on Radix primitives.
4. **A single theme provider** with system, light, and dark modes, persisted locally and applied before the first paint where practical.
5. **Typed shared API helpers** for request state, response validation, errors, cancellation, and mutation feedback.
6. **Feature-oriented page composition** with reusable layout, table, status, empty-state, error-state, and command/action components.
7. **Evidence-based quality gates** covering accessibility, responsive behavior, tests, performance, and visual consistency.

We will not adopt a large opaque component framework or rewrite the UI into a new frontend architecture. shadcn/ui is treated as an application-owned component pattern, not as a runtime dependency that hides implementation details. Radix is used selectively where accessible interaction behavior is non-trivial.

---

## 3. Goals and non-goals

### 3.1 Goals

- Achieve a measured UI score above 9.0/10.
- Provide light, dark, and system theme modes.
- Preserve the existing dark visual identity as the dark theme baseline.
- Establish semantic design tokens so components do not hard-code slate/indigo colors.
- Make all major workflows usable on desktop, tablet, and mobile widths.
- Make loading, empty, failure, retry, and successful mutation states explicit.
- Improve feature review and approval workflows with practical filtering and detail interactions.
- Add accessible keyboard navigation, focus management, labels, status announcements, and contrast checks.
- Add automated frontend validation and a repeatable visual review process.

### 3.2 Non-goals

- Replacing the FastAPI backend or changing API semantics solely for visual reasons.
- Building a full analytics/data-visualization platform in the first iteration.
- Adding every Radix primitive or creating a component abstraction before a concrete use case exists.
- Introducing a global state library unless measured complexity requires it.
- Making light mode identical to dark mode; both themes should share semantics, not necessarily identical contrast relationships.

---

## 4. Design system decision

### 4.1 Token model

Introduce semantic CSS variables for:

- background, foreground, muted foreground;
- card, popover, border, input, ring;
- primary, secondary, accent, destructive;
- success, warning, info, and status-specific surfaces;
- chart series colors;
- focus and selection states.

Tailwind utilities should consume semantic tokens rather than direct `bg-slate-*`, `text-indigo-*`, and similar palette values in page components.

The token model must define both light and dark values and preserve sufficient contrast for text, controls, borders, and status indicators.

### 4.2 Component layers

Build components in this order:

1. **Foundations:** theme provider, global styles, typography, spacing, focus ring, icon sizing.
2. **Primitives:** button, badge, card, input, textarea, select, tabs, tooltip, dialog, dropdown, toast, skeleton, alert, table.
3. **Application patterns:** page header, metric card, status badge, data table, empty state, error state, loading state, confirmation dialog, audit event row.
4. **Domain surfaces:** dashboard, feature review, approval queue, traceability, audit trail.

Each component should have a narrow API, typed variants, keyboard behavior, and a colocated test where interaction behavior is non-trivial.

### 4.3 Theme behavior

The theme selector must support:

- `system` mode as the default;
- explicit `light` mode;
- explicit `dark` mode;
- persistence using the repository-approved browser storage mechanism;
- no flash of an incorrect theme during initial load where feasible;
- a visible current-mode indicator and accessible label;
- correct behavior when the operating-system preference changes while in `system` mode.

---

## 5. Delivery phases

### Phase UI-1 — Baseline, tokens, and shell

**Goal:** Establish the design-system foundation without changing domain behavior.

| Task | Deliverable | Evidence |
|---|---|---|
| UI-1-T01 | Record current UI baseline, browser support, viewport matrix, and screenshots | Baseline report and checked-in test configuration |
| UI-1-T02 | Add semantic light/dark/system theme tokens | Token implementation and contrast audit |
| UI-1-T03 | Add theme provider and accessible theme switcher | Unit/component tests and manual keyboard check |
| UI-1-T04 | Add shared application shell, page header, navigation, and focus styles | Component tests and responsive screenshots |
| UI-1-T05 | Introduce selected shadcn/Radix primitives | Component inventory with usage guidance |

**Exit criteria:** Existing pages render in dark mode with no intentional behavior regression; light and system modes work from the shell.

### Phase UI-2 — Reliability and accessibility

**Goal:** Make the UI honest and usable under real network and interaction conditions.

| Task | Deliverable | Evidence |
|---|---|---|
| UI-2-T01 | Add typed API client helpers and consistent error normalization | Unit tests for success, HTTP failure, malformed response, and abort |
| UI-2-T02 | Standardize loading skeletons and empty states | Component tests and page screenshots |
| UI-2-T03 | Add retryable errors and mutation feedback to approvals | Tests covering approve, reject, failure, retry, and duplicate submission |
| UI-2-T04 | Add keyboard navigation, focus management, labels, and live status announcements | Automated accessibility checks plus keyboard walkthrough |
| UI-2-T05 | Validate light/dark contrast and non-color status communication | axe/contrast evidence and review checklist |

**Exit criteria:** Every page has explicit loading, empty, error, and success states; critical workflows are keyboard-completable.

### Phase UI-3 — Workflow completeness

**Goal:** Move from dashboard prototype to efficient daily-use product interface.

| Task | Deliverable | Evidence |
|---|---|---|
| UI-3-T01 | Feature review search, status filter, sorting, and detail metadata | Component/e2e tests |
| UI-3-T02 | Approval queue filters, reviewer context, confirmation dialog, and action history | Mutation tests and audit verification |
| UI-3-T03 | Traceability filtering, uncovered-requirement navigation, and responsive table/card view | Responsive tests and screenshots |
| UI-3-T04 | Audit trail filters, expandable payload/hash details, and pagination or bounded loading | Interaction tests and performance check |
| UI-3-T05 | Add useful dashboard trend/health presentation without implying unsupported metrics | API contract review and visual acceptance |

**Exit criteria:** A reviewer can find, inspect, act on, and verify a feature without relying on browser refreshes or hidden state.

### Phase UI-4 — Quality, performance, and release gate

**Goal:** Make frontend quality measurable and repeatable.

| Task | Deliverable | Evidence |
|---|---|---|
| UI-4-T01 | Add unit/component test suite for shared primitives and critical pages | CI test report |
| UI-4-T02 | Add browser e2e coverage for theme switching, feature review, and approval flow | Playwright or repository-approved browser test report |
| UI-4-T03 | Add visual regression coverage for both themes and key viewports | Baseline snapshots and review policy |
| UI-4-T04 | Add lint, typecheck, build, accessibility, and bundle-size checks to CI | Passing CI job with documented thresholds |
| UI-4-T05 | Publish UI runbook and component contribution guide | `docs/UI.md` update and release checklist entry |

**Exit criteria:** UI release checks are automated, failures are visible, and the measured score exceeds 9.0.

---

## 6. Recommended technical sequence

1. Confirm the current Vite/Tailwind setup and add only the dependencies needed for the first primitive set.
2. Add `components.json` and the shadcn-style source layout only if it improves component ownership and generation consistency.
3. Add `src/lib/utils.ts` for class composition and typed shared utilities.
4. Add `src/components/ui/` for primitives and `src/components/app/` for product patterns.
5. Add a theme provider near the root in `main.tsx`.
6. Replace hard-coded page palette classes with semantic token classes.
7. Introduce a shared API layer before adding more page-level fetch logic.
8. Migrate one representative page first—Approval Queue is recommended because it includes reads, writes, confirmation, and failure states.
9. Migrate the remaining pages incrementally, preserving behavior after each migration.
10. Add tests and visual snapshots as each shared primitive/page is migrated.

### Library selection rule

Use **Radix UI directly** when a primitive is small or highly customized. Use **shadcn/ui patterns** when an application-owned implementation, variants, and Tailwind token integration are more valuable. Do not add duplicate primitives from multiple libraries.

---

## 7. Scoring model

The score is measured after implementation, not inferred from task completion.

| Dimension | Weight | Score requirement for >9 overall |
|---|---:|---|
| Visual consistency and design system | 1.5 | 9.0+ |
| Light/dark/system theme quality | 1.0 | 9.0+ |
| Core workflow usability | 2.0 | 9.0+ |
| Accessibility and keyboard support | 1.5 | 9.0+ |
| Loading/error/empty-state reliability | 1.0 | 9.0+ |
| Responsive behavior | 1.0 | 9.0+ |
| Information hierarchy and data clarity | 0.75 | 8.5+ |
| Frontend maintainability and component reuse | 0.75 | 9.0+ |
| Automated validation and regression safety | 0.5 | 9.0+ |
| Performance and perceived responsiveness | 0.5 | 8.5+ |
| **Total** | **10.0** | **>9.0 weighted score** |

### Required evidence

- No critical axe accessibility violations on supported pages.
- All primary actions reachable and operable using keyboard only.
- Theme switcher works in system, light, and dark modes.
- No page uses direct palette classes where a semantic token exists.
- Critical API failures produce actionable user-visible feedback.
- Responsive acceptance passes at minimum 320px, 768px, 1024px, and 1440px widths.
- Build, lint, typecheck, unit/component tests, and browser tests pass.
- No material visual regression is accepted without explicit review.
- Lighthouse or equivalent performance checks meet the project-approved thresholds.

---

## 8. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Theme migration causes visual regressions | Medium | Migrate by page, use semantic tokens, retain screenshot baselines |
| Too many UI dependencies increase bundle size | Medium | Prefer Radix primitives selectively; measure bundle output in CI |
| shadcn-generated code diverges across components | Medium | Keep components application-owned, document variants, review shared primitives |
| Backend response shapes are inconsistent | High | Add typed client normalization and explicit page-level error states |
| Dark/light contrast is treated as a palette swap | High | Perform semantic contrast review for every status and interactive state |
| Scope expands into a full analytics product | Medium | Keep UI-3 dashboard work limited to supported backend metrics |
| Accessibility fixes arrive too late | High | Make axe, keyboard, and focus checks part of each phase exit criteria |

---

## 9. Rollout and rollback

- Ship the design-system foundation behind normal branch/review controls.
- Preserve dark mode as the default during the first rollout to reduce user disruption.
- Introduce the theme switcher after token migration is complete.
- Migrate pages incrementally; avoid a flag that allows two divergent component systems to persist indefinitely.
- If a migration causes a functional regression, revert the affected page migration while retaining independently safe token and primitive work.
- Do not remove existing backend endpoints or change their semantics as part of the frontend migration.

---

## 10. Definition of done

This ADR is complete only when:

1. The UI supports system, light, and dark themes with persistence and no material first-paint flash.
2. Shared primitives and semantic tokens cover all primary application surfaces.
3. Feature review, approvals, traceability, and audit workflows have complete loading, empty, error, success, and responsive states.
4. Critical actions have accessible confirmation, focus, keyboard, and status behavior.
5. Unit/component, browser, accessibility, visual, lint, typecheck, build, and performance checks are automated.
6. `docs/UI.md` reflects the delivered behavior and dependency choices.
7. The weighted scorecard records a measured score above 9.0/10 with evidence links.
8. UX Lead, QA Architect, and Engineering Lead approve the release evidence.
