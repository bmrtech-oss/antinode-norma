# Web UI Documentation — Antinode Norma BDD Platform

## Overview
The Antinode Norma Web UI is a React 18 SPA built with TypeScript, Vite, Tailwind CSS, and Lucide React icons. It provides collaborative feature review, approval workflow management, quality gate traceability, audit logging, and executive platform dashboards.

## Architecture
- **Frontend Stack:** React 18, TypeScript, Vite, Tailwind CSS, Lucide icons.
- **Backend API:** FastAPI application server in `antinode_norma/server/api.py`.
- **Routes:**
  - `/health`: Health status check.
  - `/api/features`: Feature viewer and review endpoint.
  - `/api/approvals`: Approval queue endpoint.
  - `/api/audit`: Cryptographic audit log endpoint.
  - `/api/traceability`: Matrix traceability endpoint.
  - `/api/dashboard`: Executive metrics endpoint.
  - `/api/auth/oidc/*`: OIDC authentication routes.
  - `/api/auth/saml/*`: SAML 2.0 authentication routes (flagged).

## Running Locally
1. Start API Server: `poetry run uvicorn antinode_norma.server.api:app --reload`
2. Start Frontend Dev Server: `cd ui && npm run dev`
