# Local UI Development without OIDC

Use this guide to start the local Podman stack with auth mode disabled and run the UI against it. This mode needs no identity-provider credentials. It is for local development only.

> In development with `NORMA_AUTH_MODE=disabled` and `NORMA_AUTH_ALLOW_IDENTITY_HEADERS=false`, the API supplies a synthetic least-privileged viewer identity to the UI. This is local-only behavior; production rejects disabled auth. The viewer can browse read-only UI sections, while write/admin controls remain permission-gated.

## Configure and Start the Containers

Run these commands from the repository root inside Fedora WSL. Copy the example if you have not already created your local `.env`:

```bash
cp .env.example .env
```

Keep these local values in `.env`:

```dotenv
LLM_PROVIDER=mock
NORMA_ENVIRONMENT=development
NORMA_AUTH_MODE=disabled
NORMA_AUTH_ALLOW_IDENTITY_HEADERS=false
NORMA_AUTH_ALLOWED_ORIGINS=
DATABASE_URL=postgresql://norma:norma-local-only@db:5432/norma
```

Start the complete local profile. On the first run, build the image:

```bash
podman-compose --profile local config >/dev/null
podman-compose --profile local up --build -d
podman-compose --profile local ps
curl --fail http://localhost:8000/health
```

The `.env` file is loaded into `app-http` and `app-mcp`. `db` is the Compose hostname used by containers; do not replace it with `localhost` in the container database URL.

## Run the UI

The container serves the built SPA from `ui/dist`. Since Compose bind-mounts the working tree over the image, build the UI in the checkout before opening the container-served page:

```bash
npm --prefix ui ci
npm --prefix ui run build
```

Open <http://localhost:8000/>. The API and UI share an origin in this mode, so the browser does not make a cross-origin credentialed request.

For Vite development, point the browser at the Vite server and use its existing `/api` proxy. Create `ui/.env.local` with:

```dotenv
VITE_API_BASE_URL=http://localhost:3000
```

Then run:

```bash
npm --prefix ui ci
npm --prefix ui run dev -- --host 0.0.0.0
```

Open <http://localhost:3000/>. Use `localhost` consistently; opening the page at `127.0.0.1` makes it a different origin. The default development API URL is `http://localhost:8000`, which is cross-origin from Vite. In disabled-auth mode the API returns wildcard CORS without credential support, while the UI sends credentials to its configured API origin. The Vite proxy setup above keeps the browser request same-origin and avoids that CORS failure.

The UI's saved API URL in browser local storage overrides `VITE_API_BASE_URL`. If requests still go directly to port 8000, clear the `norma-ui-api-base-url` local-storage entry and reload.

## Test UI Work without an Identity Provider

The repository's Playwright UI tests mock `/api/auth/me` and application API responses; they do not require a live login or IdP:

```bash
npm --prefix ui run test:e2e:quality
```

The mock user in `ui/e2e/app.spec.ts` is an admin fixture, so these tests can exercise permission-gated controls. This is separate from a live container-backed, no-login UI session, which is not currently implemented.

## WSL2 and Podman Notes

Run Podman commands inside the Fedora WSL distribution. Prefer keeping the checkout in the distro's Linux filesystem rather than under `/mnt/<drive>`; Windows-mounted paths can be slower and may not support SELinux relabeling as expected. The Compose bind mounts already use `:Z` for rootless Podman on SELinux-enabled Fedora. Do not remove that label to work around a Windows-mounted-path issue without checking the resulting mount permissions.

To stop the stack without deleting PostgreSQL data:

```bash
podman-compose --profile local down
```

`podman-compose` may print a missing-container error for `antinode-norma-mcp` if that service was never created; it can still remove the other containers and network. Verify with `podman ps -a --filter name=antinode-norma`.
