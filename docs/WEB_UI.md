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

## Production Build

Build and verify the SPA from the repository root:

```text
cd ui
npm ci
npm run lint
npm run typecheck
npm run test
npm run build
```

The production bundle is written to `ui/dist/`. When `ui/dist/` exists, the
FastAPI application serves it as the root SPA while API routes remain under
`/api` and `/v1`.

## Container Deployment

The root `Dockerfile` uses a Node build stage to compile the UI and copies the
result into the Python image at `ui/dist/`. Build and run it with:

```text
docker build -t antinode-norma .
docker run --rm -p 8000:8000 antinode-norma uvicorn antinode_norma.server.api:app --host 0.0.0.0 --port 8000
```

Verify the deployment at `/health` and open `/` for the SPA. Configure API,
authentication, and provider secrets through the runtime environment; do not
embed secrets in the frontend bundle.
