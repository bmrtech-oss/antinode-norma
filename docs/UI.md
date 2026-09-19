# Web UI & Frontend Architecture — Antinode Norma

This document outlines the React Web UI, static SPA mounting, component hierarchy, and user workflows.

For complete route details, see [WEB_UI.md](WEB_UI.md).

---

## 1. Frontend Stack & Architecture

- **Framework**: React 18 + TypeScript + Vite + Tailwind CSS.
- **State & Data**: React Query (TanStack Query) + React Router v6.
- **Charts & Visualizations**: Recharts.
- **Deployment**: Single Page Application (SPA) built to static assets (`ui/dist`) and mounted by FastAPI in `antinode_norma/server/api.py`.

---

## 2. Core Pages & Views

| Page | Path | Description |
|---|---|---|
| **Dashboard** | `/` | Overview of platform KPIs, generation volume, quality pass rates, and active execution status. |
| **Feature Viewer** | `/features` | View Gherkin specs, quality gate scores (Q0–Q10 breakdown), and requirement traceability. |
| **Approval Queue** | `/approvals` | Governance approval workflow allowing reviewers to review, approve, or reject generated features. |
| **Traceability & Audit** | `/traceability` / `/audit` | Requirement matrix mapping and SHA-256 content-hashed immutable audit trail browser. |
| **Analytics** | `/analytics` | Platform trends, cost metrics, pass rate history, and flake analysis. |
| **Admin Settings** | `/admin` | Enterprise settings, OIDC/SAML auth flags, RBAC user role administration, and plugin registry. |

---

## 3. Web UI Accessibility & Performance Standards

- **Accessibility**: WCAG 2.1 AA compliant keyboard navigation and screen-reader support.
- **Performance**: Target Lighthouse Performance score ≥ 90.
