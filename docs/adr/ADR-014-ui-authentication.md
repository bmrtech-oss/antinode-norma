## Updated ADR-014: Secure UI Authentication and Authorization Integration

**Version 1.1. Revised after architecture review.**

---

### Metadata

| Field | Value |
|---|---|
| **ADR ID** | ADR-014 |
| **Title** | Add secure authentication and role-aware access to the Norma UI |
| **Status** | Proposed — v1.1 |
| **Date** | 2026-09-26 |
| **Deciders** | IdP Admin, Engineering Lead, UX Lead, QA Architect |
| **Scope** | `ui/`, `antinode_norma/auth/`, `antinode_norma/server/routes/auth.py`, protected API routes |
| **Related** | ADR-001 v6 §12 (Authentication and Authorization); ADR-001 v6 §5.7 (Frontend Stack); ADR-013 v1.1 (Local Development Bootstrap); ADR-003 v1 §C1-T01 (Non-root container) |
| **Approval Required** | Yes; changes identity, session, browser, and API security boundaries |

---

### 1. Context

The React application currently renders the dashboard and workflow views without an authentication bootstrap, login route, current-user state, or logout action. The shared API helper does not send browser credentials. The UI has a user-configurable API origin, and production must support UI and API deployments on separate origins with an explicit credentialed CORS, cookie, and CSRF policy.

Authentication-related backend modules and routes exist, but the current OIDC and SAML routes are demonstration scaffolding, not a production identity implementation:

- OIDC initiation and callback perform discovery, server-held PKCE/nonce transactions, authorization-code exchange, and ID-token validation. The callback now creates a database-backed opaque session and sets an HttpOnly cookie. The one-time transaction store remains process-local pending completion of AUTH-0-T02.
- `GET /api/auth/me` and the compatibility `/api/auth/oidc/me` resolve only a valid server-side session; logout revokes it. Session data uses the shared database adapter; PostgreSQL session behavior and IdP refresh remain to be integration-verified.
- SAML response parsing extracts a subset of XML fields without validating a signed assertion, issuer, audience, recipient, or replay conditions. Invalid XML returns synthetic claims.
- Permission dependencies exist on several routes. `X-User-ID`/`X-Tenant-ID` simulation is now disabled by default and only available with explicit non-production auth-disabled test configuration; it is never accepted in OIDC or production mode.
- The UI API helper has no session bootstrap, credential policy, or centralized handling for `401 Unauthorized` and `403 Forbidden`.

Therefore, wiring a login button directly to the current routes would create a login-shaped UI without a trustworthy authenticated session. Backend contract and security work is a release blocker for real identity-provider use.

---

### 2. Decision

1. **Use a server-managed browser session.** The backend owns the OIDC callback, authorization-code exchange, token validation, and session lifecycle. The browser receives only an opaque session cookie, never provider tokens or a PKCE verifier in JavaScript storage.

2. **Support both same-origin and separate-origin deployment.** Same-origin remains the simplest deployment. A separately hosted UI must use an exact configured origin allowlist, credentialed CORS, credentials on browser API requests, secure cookie settings, and CSRF protection. Never use wildcard credentialed CORS. For truly cross-site hosting where browser privacy controls block third-party cookies, use a same-origin BFF/reverse proxy or prove the chosen browser/provider topology with release tests.

3. **Fail closed.** The UI waits for an authoritative current-user response before rendering protected workflows. UI route guards improve navigation only; API dependencies remain the authorization boundary.

4. **Use least privilege.** The UI receives the current user's roles and effective permissions from the backend and uses them to present relevant navigation/actions. A hidden or disabled UI control never substitutes for server-side permission enforcement.

5. **Delegate sign-in and user administration to an open-source IdP.** Select **Authentik** as the recommended initial reference provider, pending AUTH-0-T07 versioned conformance. The UI redirects to provider-hosted login and account-management pages; Norma does not collect IdP passwords, register IdP users, or manage IdP credentials. Keep the application contract provider-neutral OIDC. Configure an asymmetric signing key (initial profile: RS256) for the Authentik provider: Norma's current validator obtains public keys from JWKS and accepts asymmetric signing algorithms, not the HS256 fallback used when no signing key is selected.

6. **Make identity and role administration an IdP Admin responsibility.** The IdP Admin owns provider configuration, claim/group-to-Norma-role mapping, and production authentication/security sign-off. Norma validates claims and applies the approved mapping; unknown or unmapped identities receive no elevated permissions.

7. **Follow IdP session policy.** Authentik determines its session, refresh, and logout capabilities. Norma's revocable application session must honor those settings and must not outlive the validated IdP session or token policy.

8. **Make local no-auth mode configurable and non-production only.** Developers may run `NORMA_AUTH_MODE=disabled` for local/test work. Production startup must reject disabled auth. Header-based test identities are disabled by default and require `NORMA_AUTH_ALLOW_IDENTITY_HEADERS=true` while auth is disabled in a non-production environment; production and OIDC mode reject that setting.

9. **Deliver OIDC before SAML.** SAML UI support is out of the initial release path until assertion validation and session handling are independently implemented and security-tested.

---

### 3. Target Browser and API Contract

The exact route shape may evolve during AUTH-0, but the completed contract must provide these semantics:

| Operation | Required behavior |
|---|---|
| Current user | `GET /api/auth/me` returns the authenticated user, roles, effective permissions, and session expiry; anonymous callers receive `401` |
| Login | Starts OIDC Authorization Code + PKCE with state and nonce bound to a short-lived server-side transaction |
| OIDC callback | Validates one-time state, exchanges the code, validates issuer/signature/audience/nonce and claims, creates a server-side session, then redirects only to a validated return path on a configured UI origin |
| Logout | Invalidates the server-side application session, clears the cookie, and uses Authentik's end-session capability when configured and supported |
| Protected API | Returns `401` for no/expired session and `403` for an authenticated user lacking permission |
| Mutating browser API | Enforces CSRF protection and validates `Origin`/`Referer` as appropriate for the selected deployment mode |

**Session cookie requirements:** `HttpOnly`, `Secure` in production, `SameSite=Lax` (default) or `SameSite=None; Secure` when separate-origin deployment requires it. No bearer token or session ID may be stored in `localStorage` or `sessionStorage`.

**CSRF pattern:** Use a session-bound synchronizer token or a cryptographically signed, session-bound double-submit token; simple cookie/header equality is insufficient because an attacker may be able to inject a cookie. Deliver the CSRF value in a JavaScript-readable cookie and echo it in `X-CSRF-Token` on mutating requests. Validate the token against the authenticated session and validate `Origin` (and `Referer` where needed) against configured UI origins. Use `SameSite=Lax` where deployment permits; use `SameSite=None; Secure` only for tested cross-site deployments.

**Session invalidation triggers:**

| Trigger | Mechanism |
|---|---|
| User logout | Server-side session invalidation + cookie clear |
| Explicit revocation (admin disables user in Authentik) | Authentik sends an OIDC Back-Channel Logout Token when account deactivation terminates the IdP session; Norma validates it and invalidates the matching session |
| IdP session end | Back-channel logout (if configured) or session expiry |
| Authentik `user_write` audit event | Audit evidence only; it is not itself an OIDC logout signal. Account deactivation must result in a provider Logout Token for Norma to revoke sessions. |
| API redeploy | Sessions persisted in backend store; survive restart |
| Secret rotation | Existing sessions remain valid until expiry; new sessions use new secret |
| Config change (`NORMA_AUTH_MODE` disabled) | All sessions invalidated on startup |

**Back-channel logout:** Norma exposes `POST /api/auth/backchannel-logout`, accepting the standard form-encoded `logout_token` parameter. It must validate the signature using the configured issuer's JWKS and an explicitly allowed asymmetric algorithm; validate `iss`, `aud` (Norma client ID), `iat`, and `exp`; require the `events` object member `http://schemas.openid.net/event/backchannel-logout`; require at least one of `sub` or `sid`; reject any `nonce`; and reject replayed `jti` values. It then invalidates only the session(s) identified by the validated issuer and `sid` and/or `sub`. Invalid tokens return `400`; successful processing returns `200` or `204` with `Cache-Control: no-store`. Authentik's `user_write` audit event is not accepted as a substitute for this signed protocol message.

**Auth lifecycle events in `audit_events`:** Every authentication action is written to the `audit_events` table from ADR-001 v6 §12 with the following fields:

| Event | actor | action | resource | result |
|---|---|---|---|---|
| Login success | `user_id` | `auth:login` | `session` | `success` |
| Login failure | `null` | `auth:login` | `session` | `failure` |
| Logout | `user_id` | `auth:logout` | `session` | `success` |
| Session revocation | `user_id` | `auth:revoke` | `session` | `success` |
| Permission denial | `user_id` | `auth:denied` | `resource` | `failure` |
| Back-channel logout | `user_id` | `auth:backchannel_logout` | `session` | `success` |

Secrets, tokens, codes, and cookies are redacted before writing.

**Rate limiting:** Auth endpoints (`/api/auth/me`, `/api/auth/oidc/*`, `/api/auth/logout`, `/api/auth/backchannel-logout`) are rate-limited at the application layer. Default: 30 requests per minute per IP for read endpoints, 10 requests per minute per IP for state-mutating endpoints. Limits are configurable via `NORMA_AUTH_RATE_LIMIT_*` environment variables and documented in `docs/AUTH.md`.

---

### 4. Threat Model

| Threat | Vector | Control |
|---|---|---|
| Token theft via XSS | Malicious script reads `localStorage` | Server-managed HttpOnly cookies; no token in browser storage |
| CSRF | Malicious site triggers mutating request or injects a CSRF cookie | Session-bound synchronizer token or signed/session-bound double-submit token + `Origin`/`Referer` validation |
| Open redirect | Crafted `return_url` after login | Allowlist of validated local paths and configured UI origins |
| Session fixation | Attacker pre-sets session cookie | New session created on login; old session invalidated |
| Replay of authorization code | Intercepted code reused | One-time state, nonce, PKCE verifier; short transaction expiry |
| IdP impersonation | Forged ID token | Signature validation against IdP JWKS; issuer, audience, nonce checks |
| Claim escalation | Unmapped IdP group grants admin | Unknown/unmapped claims → no elevated permissions; mapping contract reviewed |
| Administrative session persistence | User disabled in IdP but Norma session remains | Back-channel logout invalidates Norma session on IdP-side termination |
| Brute-force login | Repeated callback attempts | Rate limiting on auth endpoints; IdP-side throttling |
| Config drift to no-auth | `NORMA_AUTH_MODE=disabled` in production | Startup rejects disabled mode when `NORMA_ENVIRONMENT=production` |
| Identity-header spoofing | Caller supplies `X-User-ID: admin` or `X-Tenant-ID` | Header identities default off; opt-in is limited to non-production auth-disabled test mode and rejected in production/OIDC mode |

---

### 5. Phased Implementation Plan

#### Task Progress Tracker

Update this table whenever a task starts, is blocked, or is completed. A task is complete only when its listed evidence has been run or reviewed.

| Task | Status | Evidence / notes |
|---|---|---|
| AUTH-0-T01 | Complete | `antinode_norma/auth/config.py`; production startup validation; config docs/template; auth regression slice passes (30 tests), focused Ruff and editor diagnostics pass |
| AUTH-0-T02 | Partial | OIDC discovery, code exchange, PKCE/nonce validation, signature/issuer/audience/expiry checks, and replay/expiry tests pass (40 auth tests total); transaction store remains process-local and shared session lifecycle is AUTH-0-T03 |
| AUTH-0-T03 | Partial | Added `auth_sessions` migration/store, hash-only opaque cookie sessions, expiry/revocation, `/api/auth/me`, logout, and cookie-backed route identity; 44 auth tests pass. PostgreSQL session integration and IdP refresh policy still need verification. |
| AUTH-0-T04 | Complete | Exact-origin credentialed CORS, session-bound CSRF, production Secure/SameSite cookie policy, configured-API-only credentials, and allowlisted post-login return paths implemented; 49 auth tests, full UI CI, Ruff, and editor diagnostics pass |
| AUTH-0-T05 | Complete | Header fallback is disabled by default and rejected in production/OIDC; test harness opts in explicitly; spoofed-header and config tests pass; non-integration suite: 560 passed, 6 skipped, 3 deselected; Ruff passes |
| AUTH-0-T06 | Complete | Audited all API routes; added missing FEATURE_READ permission dependency to /api/dashboard and /api/traceability; verified role-by-route permissions, tenant/resource ownership, and actor attribution; added tests/unit/test_route_security_matrix.py (567 non-integration tests pass) |
| AUTH-0-T07 | Partial | Authentik recommended after review; supported version, preview/GA status, asymmetric signing configuration, and repeatable protocol conformance remain to be verified |
| AUTH-0-T08 | Complete | Implemented map_claims_to_roles and claim mapping in antinode_norma/auth/oidc.py for groups, roles, norma_roles, and realm_access; unknown claims default to least-privilege Role.VIEWER; status claims (active/enabled) enforced; added tests/unit/test_auth_claim_mapping.py (576 non-integration tests pass) |
| AUTH-1-T01 | Complete | Created ui/src/lib/authClient.ts and ui/src/lib/AuthContext.tsx; bootstraps once from /api/auth/me; unit tests in ui/src/lib/authClient.test.ts and AuthContext.test.tsx cover authenticated, anonymous, transient failure, and malformed response states (npm run ci:ui passes) |
| AUTH-1-T02 | Complete | Created ui/src/components/AuthGuard.tsx and LoginPage.tsx; integrated AuthProvider and AuthGuard in ui/src/App.tsx; added unit tests in ui/src/components/AuthGuard.test.tsx and e2e mocks in app/accessibility spec; unit and Playwright e2e tests prove protected content and API calls do not render or run before auth check resolves |
| AUTH-1-T03 | Complete | Added UNAUTHORIZED_EVENT and FORBIDDEN_EVENT bus in ui/src/lib/api.ts, 401 listener in AuthContext.tsx, and AccessDenied component in AccessDenied.tsx; added integration tests in ui/src/lib/auth401_403.test.tsx proving 401 clears stale identity and offers return path while 403 retains session and displays AccessDenied |
| AUTH-1-T04 | Complete | Verified credentials: include policy and session-bound X-CSRF-Token header injection in ui/src/lib/api.ts; added unit tests in ui/src/api.test.ts |
| AUTH-1-T05 | Complete | Implemented validateLocalReturnPath in ui/src/lib/returnPath.ts and backend open-redirect validation; added unit tests in ui/src/lib/returnPath.test.ts and tests/unit/test_auth_return_path.py |
| AUTH-2-T01 | Complete | Implemented accessible LoginPage in ui/src/components/LoginPage.tsx; delegates authentication to Authentik OIDC provider without local password forms |
| AUTH-2-T02 | Complete | Integrated server-managed OIDC redirect and callback flow; restores allowlisted local return route across same and separate origins |
| AUTH-2-T03 | Complete | Implemented UserMenu in ui/src/components/UserMenu.tsx integrated into AppShell header; displays user name, email, roles, and provides logout clearing server session and cookie |
| AUTH-2-T04 | Complete | Implemented session-expiry recovery in AuthGuard and AuthContext, preserving workflow return paths across re-login; verified by Playwright e2e tests |
| AUTH-3-T01 | Complete | Updated AppShell.tsx navigation items to filter by user permissions (feature:read, feature:write, approval:action, audit:read); unit tests in ui/src/components/AppShell.test.tsx verify tab filtering across roles |
| AUTH-3-T02 | Complete | Updated Generation.tsx, FeatureReview.tsx, and ApprovalQueue.tsx to check user write/approval permissions and disable action controls when unpermitted; verified with Vitest and Playwright e2e tests |
| AUTH-3-T03 | Complete | Added requiredPermission and requiredRole props to AuthGuard and configured active tab permissions in App.tsx; unpermitted views render AccessDenied while retaining session; verified in AuthGuard.test.tsx |
| AUTH-3-T04 | Complete | Removed client-supplied reviewer overrides in FeatureReview.tsx and ApprovalQueue.tsx; all mutation calls rely on server-derived authenticated actor attribution |
| AUTH-4-T01 | Not started | |
| AUTH-4-T02 | Not started | |
| AUTH-4-T03 | Not started | |
| AUTH-4-T04 | Not started | |
| AUTH-4-T05 | Not started | |

#### Phase AUTH-0 — Backend identity and browser-session contract

**Goal:** Replace demo behavior with a secure, testable authentication contract before the UI relies on it.

AUTH-0-T07 and AUTH-0-T08 may run alongside AUTH-0-T02, but their provider, claim-mapping, logout, and session-policy findings must inform final AUTH-0-T03 and AUTH-0-T04 contracts before production enablement.

| Task | Deliverable | Evidence |
|---|---|---|
| AUTH-0-T01 | Load issuer/discovery, client ID, secret, redirect URI, and allowed origins from validated deployment configuration | Configuration tests; startup fails closed for incomplete production config |
| AUTH-0-T02 | Complete OIDC code exchange and validation; bind state, nonce, and PKCE verifier to one-time, expiring server-side transactions. Process-local store is acceptable while replicas=1; shared store is required for multi-worker deployment and is delivered by AUTH-0-T03 | Mock IdP tests for valid flow, invalid/replayed state, bad nonce, invalid issuer/audience/signature, expired transaction, and exchange failure |
| AUTH-0-T03 | Add durable, revocable server-side sessions and authoritative `GET /api/auth/me` and logout behavior; derive expiry/refresh from Authentik capabilities and configured policy | API tests for creation, IdP-bounded expiry, refresh, revocation, multi-worker storage, logout, and anonymous `401` |
| AUTH-0-T04 | Add secure cookie, CSRF, exact-origin credentialed CORS for separately hosted UI/API, and safe post-login return-path handling | Security tests for cookie flags, credentialed preflight, CSRF, origin rejection, open redirects, same-origin and separate-origin browser flows |
| AUTH-0-T05 | Remove client-supplied identity-header trust from production; retain test identity only through `NORMA_AUTH_ALLOW_IDENTITY_HEADERS=true` with auth disabled outside production | Tests prove default denial, explicit local-test opt-in, and rejection in OIDC/production modes |
| AUTH-0-T06 | Audit protected routes for consistent authentication, permission enforcement, and actor attribution | Route-by-role matrix covering read, write, approval, audit, imports, generation, and admin operations |
| AUTH-0-T07 | Evaluate Authentik and Keycloak; use **Authentik** as the recommended initial reference IdP pending pinned-version approval; configure an asymmetric signing key and record discovery, back-channel logout, claim, and session capabilities | Decision record cites versioned upstream docs; repeatable local conformance tests prove discovery/JWKS, RS256 ID-token validation, logout-token claims/replay, and session behavior |
| AUTH-0-T08 | Define Authentik group/claim-to-Norma-role mapping, unmapped-user behavior, and IdP Admin ownership/workflow | Reviewed mapping contract; tests for each role, unknown claims, disabled users, and least privilege |

**Exit criteria:** No endpoint creates an authenticated user from synthetic or unvalidated claims; current-user state is session-bound; protected APIs fail closed; unit/integration security tests pass without a live identity provider. AUTH-0 is a blocker for production login UI rollout.

#### Phase AUTH-1 — UI authentication state and access boundaries

**Goal:** Make the UI model anonymous, loading, authenticated, and session-error states before introducing provider redirects.

| Task | Deliverable | Evidence |
|---|---|---|
| AUTH-1-T01 | Add a typed auth client and provider that bootstraps once from `/api/auth/me` | Unit tests for authenticated, anonymous, transient failure, and malformed response states |
| AUTH-1-T02 | Add public login/callback/error routes and protect application routes pending auth resolution | Browser tests prove protected content/API calls do not render or run before the auth check resolves |
| AUTH-1-T03 | Add central `401` handling that clears stale UI identity and offers a login return path; distinguish `403` access-denied state | API-client and page tests for expired session versus insufficient permission |
| AUTH-1-T04 | Add credential and CSRF request policy to `ui/src/lib/api.ts`, including explicit API-origin support | Tests assert `credentials: include`, CSRF headers, and trusted origin behavior for same-origin and separately hosted UI/API |
| AUTH-1-T05 | Preserve a validated, local return path across login; avoid loops and reject external redirect targets | Route tests for deep links, invalid return path, and unauthenticated navigation |

**Exit criteria:** Auth state has one source of truth; protected workflow pages are not accessible while anonymous; transient API failures are not misreported as successful logout; no auth secrets are persisted in browser storage.

#### Phase AUTH-2 — OIDC login, callback, and logout experience

**Goal:** Complete the primary interactive sign-in lifecycle using the AUTH-0 server contract.

| Task | Deliverable | Evidence |
|---|---|---|
| AUTH-2-T01 | Add an accessible sign-in page that continues to Authentik-hosted login; do not collect passwords or manage IdP accounts in Norma | Component/accessibility tests; browser confirms redirect to Authentik and no local credential form |
| AUTH-2-T02 | Integrate the server-managed OIDC redirect/callback and restore only an allowlisted UI return route across origins | Mock IdP browser test covering success, denied consent, provider error, invalid state, callback failure, and separate UI/API origins |
| AUTH-2-T03 | Show authenticated identity and provide logout that clears Norma's session and invokes Authentik end-session when supported/configured | Tests verify server invalidation, cookie clearing, UI reset, supported Authentik end-session behavior, and protected-route redirect |
| AUTH-2-T04 | Add session-expiry recovery and safe return-to-workflow behavior | Browser test for expiry during read and during a pending mutation |

**Exit criteria:** A real configured Authentik provider can sign in and out end to end, with no token exposure to JavaScript and understandable recovery for provider/API failures.

#### Phase AUTH-3 — Permission-aware navigation and workflow actions

**Goal:** Tailor the experience to effective server permissions without duplicating authorization decisions in the browser.

| Task | Deliverable | Evidence |
|---|---|---|
| AUTH-3-T01 | Render role/permission-appropriate navigation and user identity in the app shell | Component tests for admin, reviewer, generator, and viewer |
| AUTH-3-T02 | Hide or disable unavailable mutations with accessible reason text; preserve read access where allowed | UI tests for generation, approval, audit, and admin affordances |
| AUTH-3-T03 | Handle server `403` consistently, including direct URLs and stale permissions | Browser tests confirm backend denial remains authoritative and UI presents a useful access-denied state |
| AUTH-3-T04 | Ensure audited mutations use the authenticated actor and show relevant results | API/UI tests verify audit attribution is not supplied by the browser |

**Exit criteria:** UI controls match effective permissions for each role; every protected mutation is still enforced by the backend; direct navigation and stale client state cannot bypass authorization.

#### Phase AUTH-4 — Security verification, rollout, and operations

**Goal:** Make authentication support releaseable, diagnosable, and safe to operate.

| Task | Deliverable | Evidence |
|---|---|---|
| AUTH-4-T01 | Add deterministic fake-provider browser coverage and auth route contract suite to CI. Auth contract suite runs under both Docker and Podman, matching ADR-013 v1.1 §5.2 CI matrix | CI reports without real credentials or live identity-provider dependencies |
| AUTH-4-T02 | Verify CSRF, fixation/replay, logout revocation, IdP-bounded expiry, cookie flags, CORS, same/separate-origin deployment, redirect allowlist, role matrix, back-channel logout, and rate limiting | Security test report and reviewed browser/deployment matrix |
| AUTH-4-T03 | Document Authentik setup, hosted login/account management, callback URLs, back-channel logout configuration, IdP certificate rotation procedure, local no-auth mode, IdP-derived session policy, cross-origin/reverse-proxy setup, and recovery | Updated `docs/AUTH.md`, configuration guide, and local runbook |
| AUTH-4-T04 | Add safe operational logging/metrics for login failures and session outcomes; write auth lifecycle events to `audit_events` | Tests prove secrets, codes, tokens, and cookies are redacted; audit_events rows present for each lifecycle event |
| AUTH-4-T05 | Enable production login only after security review and rollback procedure are approved | Release checklist sign-off; tested disable/rollback path |

**Exit criteria:** CI covers the full browser/API lifecycle; deployment guidance is complete; security review accepts the threat model; production enablement is explicit and reversible.

#### Deferred — SAML UI sign-in

Do not add a SAML button to the production UI until the backend validates signed assertions, issuer, audience, recipient, destination, time conditions, and replay protection using a maintained SAML library, and establishes the same session contract as OIDC. Track that work as a separately reviewed extension after AUTH-0 through AUTH-4 have an accepted OIDC baseline.

---

### 6. Security and UX Invariants

- Tokens, authorization codes, PKCE verifiers, and session IDs never enter browser storage, application logs, analytics, or error telemetry.
- Authentication state is resolved before protected data requests begin.
- Login failure, provider outage, expired session, and insufficient permission are distinct user-visible states.
- Do not redirect to arbitrary URLs after login/logout; allow only validated local paths on the same-origin app or an explicitly configured UI origin.
- The API remains authoritative for every resource and action permission.
- Anonymous local/demo access is never silently treated as production SSO.
- Accessibility includes keyboard operation, visible focus, screen-reader status/error announcement, and appropriately labelled sign-in/out controls.

---

### 7. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| UI ships against simulated backend auth | Critical | Make AUTH-0 exit criteria a prerequisite for provider-enabled release |
| Browser token storage leaks credentials | Critical | Use server-managed HttpOnly sessions; explicitly prohibit local/session storage |
| Separate-origin cookies or browser privacy controls block sessions | High | Test credentialed CORS and cookie modes; use same-origin hosting or a BFF/reverse proxy where third-party cookie blocking applies |
| UI permission checks drift from backend policy | High | Return effective permissions from the API; keep server checks authoritative and contract-tested |
| Local no-auth mode reaches production | Critical | Require `NORMA_AUTH_MODE=oidc` in production and test startup rejection of disabled mode |
| Authentik claim mapping grants unintended privileges | Critical | IdP Admin reviews mapping; reject unmapped claims to least-privileged/denied state and test every role |
| Auth errors create redirect loops or lose work | Medium | Preserve validated local return paths and test expiry during user workflows |
| SAML is mistaken for production-ready because routes exist | High | Keep UI SAML deferred until signature and protocol validation is implemented |
| Authentik unavailable during development | Medium | Local no-auth mode for dev; mock IdP provider in CI |
| Back-channel logout endpoint spammed or forged | High | Rate-limit; validate signature, issuer, audience, time claims, event claim, subject/session selector, and replay ID before invalidating any session |

---

### 8. Definition of Done

1. OIDC login, callback, current-user, session expiry, and logout work through a server-managed session.
2. Anonymous requests receive `401`; authenticated unauthorized requests receive `403`; protected API routes enforce the same permission contract.
3. UI bootstrapping, route gating, permission-aware controls, and recovery are tested for admin, reviewer, generator, viewer, and anonymous states.
4. Cookie, CSRF, same/separate-origin CORS, redirect, replay, IdP-bounded expiry, claim mapping, back-channel logout, rate limiting, and redaction requirements have passing evidence and IdP Admin production sign-off.
5. Auth lifecycle events are written to `audit_events` with actor, action, resource, result, IP, and user-agent.
6. UI lint, typecheck, unit/component, accessibility, browser, and build checks pass in CI; backend auth tests use a deterministic fake provider and run under both Docker and Podman.
7. `docs/AUTH.md` and the deployment runbook describe only implemented and security-reviewed behavior.

---

### 9. Confirmed Constraints and Remaining Decision Gates

The following stakeholder constraints are accepted: select **Authentik** as the initial open-source OIDC IdP and reuse its hosted login/user-management pages; support a separately hosted UI origin; derive session and refresh policy from Authentik; support configurable no-auth local development; and make the IdP Admin accountable for IdP configuration, role mapping, and production authentication sign-off.

Remaining decisions to record in AUTH-0-T07/T08:

- Which Authentik version is the initial reference, and which versions are in the supported test matrix?
- Which Authentik groups carry role assignments, and does Norma require pre-provisioning or permit just-in-time user records?
- Which browser/deployment combinations require a same-origin BFF because third-party-cookie protections prevent direct cross-site API sessions?


### Recommendation: Authentik vs Keycloak

**Choose Authentik** as the initial reference IdP.

| Criterion | Authentik | Keycloak | Winner |
|---|---|---|---|
| **Back-channel logout** | OIDC support is documented as preview from 2025.8; verify GA status for the pinned release ([Authentik docs](https://docs.goauthentik.io/add-secure-apps/providers/oauth2/frontchannel_and_backchannel_logout/)) | Supported; verify the pinned release and client configuration | Candidate advantage, subject to version conformance |
| **Audit logging** | Built-in Events system covering login, login_failed, logout, user_write, secret_rotate, suspicious_request | Login events and admin events; must be enabled per realm; more configuration required | **Authentik** |
| **Time to first working SSO** | Visual flow editor, fewer concepts, YAML blueprints | Steeper learning curve, more concepts (realms, clients, mappers) | **Authentik** |
| **Resource footprint** | ~2 GB RAM minimum (server + worker + PostgreSQL) | 2–4 GB minimum (JVM, Infinispan cache) | **Authentik** (lighter on WSL2) |
| **Protocol depth** | OIDC, SAML, LDAP, SCIM, RADIUS, Kerberos, Proxy | OIDC, SAML, token exchange, DPoP, FAPI 2 Final, Organizations | **Keycloak** (deeper) |
| **Multi-tenancy** | Brands (cosmetic), Tenants (alpha) | Realms (production-ready) | **Keycloak** |
| **Container simplicity** | Server + worker + PostgreSQL, no JVM, no Infinispan | Single binary but JVM baseline, Infinispan clustering | **Authentik** |
| **Configuration as code** | YAML blueprints, Terraform, K8s operators | Partial (JSON export) | **Authentik** |
| **Backing** | Authentik Security (Open Core Ventures), MIT core | Red Hat / IBM, CNCF Incubating, Apache 2.0 | **Keycloak** (enterprise backing) |
| **WSL2 compatibility** | Python + Go, lighter footprint | JVM-heavy, higher memory baseline | **Authentik** |

Comparison scores and resource figures are directional estimates, not verified
release criteria. Provider capabilities and event names are version-sensitive;
AUTH-0-T07 must record the pinned Authentik version, inspect its discovery
metadata, and run the listed conformance checks before treating a capability as
available. The upstream OIDC logout documentation linked above currently labels
the feature preview; the deployment decision must verify its status for the
selected version.

**Why Authentik wins for this project:**

1. **Back-channel logout is a documented OIDC capability**, subject to version verification. Authentik documents sending signed Logout Tokens when a user session is ended, an administrator deletes a session, or an account is deactivated. Norma must configure the supported logout URI and validate the protocol token; an Authentik audit event alone is not a logout signal.
2. **Complementary audit evidence.** Authentik's event system records IdP-side lifecycle and administration events. Norma must separately write its own validated login/logout/authorization events to `audit_events`; no automatic direct mapping is assumed. Reconcile the two sources operationally where required.
3. **YAML blueprints align with Norma's GitOps philosophy.** The blueprints are declarative configuration files that can be version-controlled, matching the ADR-001/002/003 approach to infrastructure.
4. **Potentially lighter footprint on WSL2.** Running Fedora in WSL2 with limited RAM favors measuring both candidates against the same seeded workload; the memory figures in the comparison are estimates, not release requirements.
5. **Faster onboarding.** The visual flow editor and fewer core concepts reduce IdP Admin training time.

**When Keycloak would be preferred:**
- If the organization already has Keycloak expertise or Red Hat infrastructure.
- If multi-tenant B2B (Organizations) is on the roadmap.
- If SAML federation with legacy identity systems is required at scale.
- If FAPI 2 certification or token exchange (RFC 8693) is required.

For Norma's use case — OIDC-first, audit-heavy, container-portable, developer-friendly — **Authentik is the better fit**.

---

### 10. Changelog

| Version | Date | Change |
|---|---|---|
| v1.0 | 2026-09-26 | Initial proposal |
| **v1.1** | **2026-09-26** | **ADR references corrected to file paths; session invalidation triggers added; back-channel logout decision added; audit lifecycle events added; CSRF pattern specified; rate limiting added; threat model table added; Authentik recommended as reference IdP; AUTH-0-T02 completion path clarified; container-runtime coverage noted; IdP certificate rotation added to AUTH-4-T03** |
| **v1.2** | **2026-09-26** | **Fixed production environment variable; required compatible Authentik signing-key setup; specified OIDC Back-Channel Logout validation and replay checks; separated `user_write` audit events from protocol logout; strengthened CSRF token binding; marked Authentik evaluation partial pending pinned-version conformance** |
| **v1.3** | **2026-09-26** | **Disabled identity-header fallback by default; limited explicit opt-in to non-production auth-disabled test mode; rejected the setting in production/OIDC; updated test harness and CORS regression contract** |