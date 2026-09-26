# Antinode Norma BDD Platform - Authentication & Authorization Documentation

This document describes the authentication (OIDC, SAML 2.0) and role-based access control (RBAC) architecture for the Antinode Norma BDD Platform.

> **Implementation status:** Authentication routes, OIDC discovery, PKCE code
> exchange, database-backed opaque session cookies, RBAC route security matrix,
> OIDC claim-to-role mapping, typed UI auth context and guards, 401/403 event bus,
> open-redirect prevention, and permission-aware UI navigation/controls are fully
> implemented across Phases AUTH-0 through AUTH-3 per [ADR-014](adr/ADR-014-ui-authentication.md).
>
> The recommended identity provider is **Authentik**. The one-time OIDC transaction
> store remains process-local (suitable for single-replica or sticky sessions);
> PostgreSQL runtime verification, back-channel logout, and SAML signature validation
> remain as documented operational milestones.

The intended production model uses an open-source OIDC provider (candidate
evaluation: Keycloak or Authentik). Sign-in and IdP account management remain on
the provider-hosted pages; Norma does not collect IdP passwords or replace IdP
user administration. The IdP Admin owns provider configuration, role/group
claim mapping, and production authentication sign-off. Local development may
set `NORMA_AUTH_MODE=disabled`; production must reject that mode. `X-User-ID` /
`X-Tenant-ID` identity simulation is disabled by default and is accepted only
when `NORMA_AUTH_ALLOW_IDENTITY_HEADERS=true` is explicitly set in a
non-production auth-disabled environment. Production and OIDC mode reject this
setting; these headers are never production credentials.

---

## 1. Authentication Mechanisms

### OIDC (Primary SSO)
- **Intended protocol:** Authorization Code Flow + PKCE (S256 challenge).
- **Provider UX:** Redirect to the configured IdP-hosted sign-in and account-management pages.
- **Session policy:** Follow the selected IdP's session, refresh, and logout capabilities; Norma's application session must not outlive the validated upstream session.
- **Deployment:** Same-origin is supported; separately hosted UI/API is also a target, with exact-origin credentialed CORS, secure cookies, and CSRF defenses. Cross-site browser cookie restrictions may require a same-origin BFF/reverse proxy.
- **Browser session:** The callback sets an HttpOnly `norma_session` cookie and a JavaScript-readable, session-bound `norma_csrf` cookie. Mutating requests echo the CSRF value in `X-CSRF-Token`; the API validates the configured `Origin` and session-bound token. Production split-origin sessions use `SameSite=None; Secure`; local development uses `SameSite=Lax`.
- **OIDC routes currently present (UI and production hardening remain incomplete):**
  - `GET /api/auth/oidc/login` — Loads provider discovery metadata and returns an authorization URL; the PKCE verifier and nonce stay server-side.
  - `GET /api/auth/oidc/callback` — Exchanges the code, validates signing key, issuer, audience, expiry, and nonce, then creates a database-backed session and sets an HttpOnly cookie.
  - `GET /api/auth/me` — Returns the session-bound user, effective permissions, and expiry; anonymous calls receive `401`.
  - `POST /api/auth/logout` — Revokes the server-side session and clears the cookie.

### SAML 2.0 (Secondary SSO, Feature-Flagged)
- **Flag:** `features.auth_saml: true` in `norma.config.yml` or `NORMA_FEATURE_AUTH_SAML=true`.
- **Prototype routes currently present (not production SAML):**
  - `GET /api/auth/saml/login` — Generates SAML AuthNRequest redirect.
  - `POST /api/auth/saml/acs` — Currently parses selected XML fields without signature or protocol validation.
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

Routes that declare a permission dependency use FastAPI route-level checks:

```python
from antinode_norma.auth.middleware import requires_permission
from antinode_norma.auth.roles import ADMIN_WRITE

@router.get("/settings", dependencies=[Depends(requires_permission(ADMIN_WRITE))])
async def get_settings():
    ...
```

- On those protected routes, unauthenticated requests return `401 Unauthorized`.
- On those protected routes, authenticated requests lacking required permissions return `403 Forbidden`.

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

---

## 6. Authentik Integration & Operational Runbooks

### Authentik Setup & Configuration
1. **OIDC Provider Setup**:
   - In Authentik, create an OAuth2/OpenID Provider under **Applications > Providers**.
   - Select **Authorization Code** flow and configure PKCE (S256).
   - Configure an **Asymmetric Signing Key** (e.g., RS256). Norma's JWKS validator requires asymmetric public key signatures.
   - Configure the Redirect URI: `https://<norma-domain>/api/auth/oidc/callback`.
2. **Back-Channel Logout Setup**:
   - Set the Back-Channel Logout URI: `https://<norma-domain>/api/auth/backchannel-logout`.
   - Ensure the provider sends signed Logout Tokens containing `sub` or `sid` and `http://schemas.openid.net/event/backchannel-logout`.

### Role & Claim Mapping
Norma parses claims from `groups`, `roles`, `norma_roles`, or `realm_access.roles`:
- `norma-admins` or `admin` -> `Role.ADMIN`
- `norma-reviewers` or `reviewer` -> `Role.REVIEWER`
- `norma-generators` or `generator` -> `Role.GENERATOR`
- `norma-viewers` or `viewer` -> `Role.VIEWER`
- Unmapped/unknown claims default to least-privilege `Role.VIEWER`.
- Inactive users (`active: false` or `enabled: false`) are denied access.

### IdP Certificate & Key Rotation Runbook
1. Generate or upload the new signing certificate/key pair in Authentik.
2. Update the Provider's Signing Key selection in Authentik.
3. Authentik automatically updates its JWKS endpoint (`/.well-known/jwks.json`).
4. Norma fetches keys dynamically from the JWKS endpoint upon receiving ID tokens; no Norma API restart is required unless JWKS caching is enabled.

### Local Development (No-Auth Mode)
For local offline development, set in `.env`:
```env
NORMA_AUTH_MODE=disabled
NORMA_AUTH_ALLOW_IDENTITY_HEADERS=true
```
- In `NORMA_AUTH_MODE=disabled`, authentication dependencies inject a default viewer identity or accept simulated `X-User-ID` / `X-Tenant-ID` headers.
- **Production Safety Gate**: Production mode (`NORMA_ENVIRONMENT=production`) strictly rejects `NORMA_AUTH_MODE=disabled` and `NORMA_AUTH_ALLOW_IDENTITY_HEADERS=true` at startup.

### Session & Recovery Runbook
- **Session Expiry**: Sessions expire after the configured TTL (`NORMA_AUTH_SESSION_TTL_HOURS`, default 24h).
- **Session Revocation**: Admin deactivations in Authentik trigger a Back-Channel Logout token sent to `/api/auth/backchannel-logout`, revoking all active Norma sessions for that subject.
- **Manual Revocation**: Execute `DELETE FROM auth_sessions WHERE user_id = '<user-id>'` in the Norma PostgreSQL database to immediately force user re-authentication.
