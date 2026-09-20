# Antinode Norma BDD Platform - Authentication & Authorization Documentation

This document describes the authentication (OIDC, SAML 2.0) and role-based access control (RBAC) architecture for the Antinode Norma BDD Platform.

---

## 1. Authentication Mechanisms

### OIDC (Primary SSO)
- **Protocol:** Authorization Code Flow + PKCE (S256 challenge).
- **Endpoints:**
  - `GET /api/auth/oidc/login` — Initiates OIDC authorization request.
  - `POST /api/auth/oidc/callback` — Exchanges code for tokens and maps claims to `User`.
  - `GET /api/auth/oidc/me` — Returns current authenticated user state.

### SAML 2.0 (Secondary SSO, Feature-Flagged)
- **Flag:** `features.auth_saml: true` in `norma.config.yml` or `NORMA_FEATURE_AUTH_SAML=true`.
- **Endpoints:**
  - `GET /api/auth/saml/login` — Generates SAML AuthNRequest redirect.
  - `POST /api/auth/saml/acs` — Parses Assertion Consumer Service response claims.
  - `GET /api/auth/saml/metadata` — Provides SP SAML metadata XML.

---

## 2. Role-Based Access Control (RBAC) Matrix

Platform roles: `admin`, `reviewer`, `generator`, `viewer`.

| Permission | Description | admin | reviewer | generator | viewer |
|---|---|:---:|:---:|:---:|:---:|
| `feature:read` | View BDD features & scenarios | ✅ | ✅ | ✅ | ✅ |
| `feature:write` | Generate & edit Gherkin features | ✅ | ❌ | ✅ | ❌ |
| `approval:action` | Approve/reject feature requests | ✅ | ✅ | ❌ | ❌ |
| `audit:read` | View immutable audit trail | ✅ | ✅ | ✅ | ✅ |
| `admin:write` | Update platform settings | ✅ | ❌ | ❌ | ❌ |

---

## 3. Route Security & Permission Middleware

Endpoints are protected using FastAPI route dependencies:

```python
from antinode_norma.auth.middleware import requires_permission
from antinode_norma.auth.roles import ADMIN_WRITE

@router.get("/settings", dependencies=[Depends(requires_permission(ADMIN_WRITE))])
async def get_settings():
    ...
```

- Unauthenticated requests return `401 Unauthorized`.
- Authenticated requests lacking required permissions return `403 Forbidden`.

---

## 4. User Action Audit Trail

All mutating user operations are recorded into a tamper-evident SHA-256 hash-chained audit log (`AuditLog`):

Recorded attributes:
- `user_id` / `actor`
- `action` (e.g. `feature:approve`, `admin:settings_update`)
- `resource`
- `result` (`success` / `failure`)
- `ip` (client IP)
- `user_agent`
- `payload` (action details / state diff)

Integrity verification is available at `GET /api/audit/verify`.

---

## 5. Admin Settings API

Platform settings management endpoints:
- `GET /api/admin/settings` (Requires `admin:write`)
- `PUT /api/admin/settings` (Requires `admin:write`)
