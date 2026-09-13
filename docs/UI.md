# Web UI Architecture & Spike Report (ADR-001 §5.7 & Task P0-T06)

This document specifies the frontend technology stack, authentication integration, state management, accessibility compliance, and Phase P0 UI spike evaluation for Antinode Norma.

---

## 1. Technical Architecture Stack

- **Framework**: React 18 + TypeScript + Vite
- **Styling**: Tailwind CSS
- **State & Data Fetching**: React Query (TanStack Query) for server state management
- **Charts / Dashboards**: Recharts
- **Deployment**: Static build served via FastAPI or nginx

---

## 2. Authentication & Security (ADR-001 §5.7 & §12)

- **Flow**: OIDC Authorization Code Flow with PKCE.
- **Token Security**: Tokens (Access & Refresh) stored **strictly in memory**, never in `localStorage` or `sessionStorage`.
- **Session Transport**: HttpOnly, Secure, SameSite=Lax cookies for session identification.

---

## 3. Accessibility & Quality Targets

- **Standard**: WCAG 2.1 Level AA compliance across all pages.
- **Performance & Audits**: Lighthouse audit score ≥ 90 across Performance, Accessibility, Best Practices, and SEO.

---

## 4. UI Spike Evaluation & Recommendation (Task P0-T06)

### Spike Findings (`spike/ui/`)
- Proof-of-Concept scaffold created in `spike/ui/`.
- Validated component structure for user story input, real-time status reporting, and Gherkin feature preview.
- FastAPI backend integration model verified; static assets build cleanly via Vite.

### Go / No-Go Recommendation
- **Recommendation**: **GO** for Track C (Phase P9 Web UI, Phase P10 SSO/RBAC).
- **Justification**: React + Vite + React Query provides a lightweight, performant, and maintainable architecture meeting enterprise requirements.
