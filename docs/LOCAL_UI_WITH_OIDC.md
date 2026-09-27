# Local UI Development with OIDC

Use this guide when developers need to exercise the live UI with real browser authentication. You need an OIDC provider/client configured for local development; the placeholder values in `.env.example` are not valid credentials.

## Configure the OIDC Client

Create or use an OIDC client in your identity provider with authorization-code login and PKCE enabled. Register this exact callback URL with the provider:

```text
http://localhost:8000/api/auth/oidc/callback
```

The callback belongs to the API. The allowed origin below belongs to the browser UI; they are different settings. For the Vite development server, the UI origin is `http://localhost:3000`.

Copy `.env.example` to `.env`, then set the auth values below. Use either `NORMA_OIDC_ISSUER` or `NORMA_OIDC_DISCOVERY_URL`; the configured issuer must match the issuer published in discovery metadata. The provider must be reachable from both the browser and the app container where applicable.

```dotenv
NORMA_ENVIRONMENT=development
NORMA_AUTH_MODE=oidc
NORMA_AUTH_ALLOW_IDENTITY_HEADERS=false
NORMA_AUTH_ALLOWED_ORIGINS=http://localhost:3000
NORMA_OIDC_ISSUER=https://idp.example.test/replace-with-your-issuer
NORMA_OIDC_DISCOVERY_URL=
NORMA_OIDC_CLIENT_ID=replace-with-your-client-id
NORMA_OIDC_CLIENT_SECRET=replace-with-your-client-secret
NORMA_OIDC_REDIRECT_URI=http://localhost:8000/api/auth/oidc/callback
LLM_PROVIDER=mock
DATABASE_URL=postgresql://norma:norma-local-only@db:5432/norma
```

Replace the example issuer, client ID, and secret with values from your provider. Do not commit `.env`. `NORMA_AUTH_ALLOWED_ORIGINS` must contain the exact UI origin, including scheme, host, and port, with no path or trailing slash. Add another origin only if developers actually browse from it; `localhost` and `127.0.0.1` are distinct origins.

## Configure the UI and Start

For Vite development, create `ui/.env.local`:

```dotenv
VITE_API_BASE_URL=http://localhost:8000
```

The UI calls the API cross-origin from port 3000 to port 8000 and includes session credentials. OIDC mode configures CORS with the explicit allowed UI origin and credentials enabled. Keep the hostname consistent: browse at `http://localhost:3000` and use `http://localhost:8000` as the API URL. The UI also stores an API URL override in browser local storage; if it is stale, clear `norma-ui-api-base-url` and reload.

From the repository root in Fedora WSL:

```bash
podman-compose --profile local config >/dev/null
podman-compose --profile local up --build -d
podman-compose --profile local ps
curl --fail http://localhost:8000/health
```

Then install and run the UI:

```bash
npm --prefix ui ci
npm --prefix ui run dev -- --host 0.0.0.0
```

Open <http://localhost:3000/> and select the sign-in action. Before sign-in, `GET /api/auth/me` returning `401` is expected. After the provider redirects back to the UI, the session cookie should make that endpoint return `200`.

If you change `.env`, restart the app service so FastAPI rebuilds its CORS middleware from the new settings:

```bash
podman-compose --profile local down
podman-compose --profile local up --build -d
```

This stops the services but preserves the PostgreSQL volume. `podman-compose` may print a missing-container error for `antinode-norma-mcp` if that service was never created; verify the remaining containers with `podman ps -a --filter name=antinode-norma`. Do not add `-v` unless you intend to delete local database data.

## Verify Credentialed CORS

A preflight from the Vite UI origin should return the explicit origin and allow credentials. It must not return `Access-Control-Allow-Origin: *`:

```bash
curl -i -X OPTIONS http://localhost:8000/api/auth/me \
  -H 'Origin: http://localhost:3000' \
  -H 'Access-Control-Request-Method: GET' \
  -H 'Access-Control-Request-Headers: content-type'
```

Expect `Access-Control-Allow-Origin: http://localhost:3000` and `Access-Control-Allow-Credentials: true`. The server also allows the configured methods and the `Accept`, `Authorization`, `Content-Type`, and `X-CSRF-Token` headers.

## Troubleshooting

- **`/api/auth/oidc/login` returns `503`:** the running API is not in OIDC mode. Check `NORMA_AUTH_MODE=oidc` inside `app-http`, then recreate the service.
- **Provider initialization returns `502`:** verify the issuer/discovery URL and that the app container can reach the provider. Confirm the discovery document's issuer exactly matches `NORMA_OIDC_ISSUER` when set.
- **Callback reports invalid return origin:** add the browser UI origin to `NORMA_AUTH_ALLOWED_ORIGINS`, not just the API callback URL.
- **CORS still reports `*`:** the API is likely running with disabled auth or an old environment. Confirm the active container has `NORMA_AUTH_MODE=oidc`, the exact UI origin is configured, and `app-http` was restarted after editing `.env`.
- **Login succeeds but API calls return `401` or `403`:** keep the browser/API hostname consistent and inspect the session cookie in browser developer tools. A `403` can also mean the signed-in user's mapped OIDC roles do not grant the requested permission.

For the auth route and role details, see [AUTH.md](AUTH.md). For the shared Fedora WSL2 Podman setup, see [LOCAL_DEV_COMMANDS.md](LOCAL_DEV_COMMANDS.md).
