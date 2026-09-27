# Podman Command Reference

Run these commands from the repository root inside Fedora WSL2, using the same Linux user that owns the rootless Podman containers. This project uses `podman-compose`; if your installation provides the Compose v2 plugin instead, replace `podman-compose` with `podman compose`.

## Check Podman

```bash
podman --version
podman-compose --version
podman info --debug
```

On Fedora, install the documented host prerequisites once if needed:

```bash
sudo dnf install -y podman podman-compose python3-pip python3-devel gcc-c++ make
```

Do not add `sudo` to normal Podman commands. Rootless Podman has a separate container/image store for each user.

## Configure and Start

Create `.env` from the example if you have not already configured it. For local development, the example uses the mock LLM provider and disabled auth. Then check and start the complete stack:

```bash
cp .env.example .env
podman-compose --profile local config
podman-compose --profile local up --build -d
```

`--build` is needed for the first build or after Dockerfile, dependency-manifest, or other image-layer changes. The `local` profile starts PostgreSQL, migration and seed jobs, FastAPI/UI (`app-http`), and MCP (`app-mcp`). The API is published at `http://localhost:8000`.

Useful startup variants:

```bash
# Start or update using the already-built image; no image build.
podman-compose --profile local up -d

# Start the HTTP profile only.
podman-compose --profile http up --build -d

# Build the shared image before a first MCP-only run.
podman-compose --profile http build app-http
podman-compose --profile mcp run --rm app-mcp

# Start optional Prometheus, Grafana, Loki, and Tempo services.
podman-compose --profile observability up -d
```

## Check Status and Health

```bash
podman-compose --profile local ps
podman ps
podman ps -a
curl --fail http://localhost:8000/health
```

Inspect a specific local auth setting without printing the container's full environment:

```bash
podman exec antinode-norma-http printenv NORMA_AUTH_MODE
podman exec antinode-norma-http printenv NORMA_AUTH_LOCAL_ROLE
```

For disabled auth, `NORMA_AUTH_LOCAL_ROLE` accepts `viewer`, `generator`, `reviewer`, or `admin`; omitted values default to `viewer`. The no-auth service grants that role to any caller, so use elevated roles only on an isolated local instance.

## Logs and Shell Access

```bash
# Follow API startup and request logs.
podman-compose --profile local logs -f app-http

# Show the latest API logs without following.
podman-compose --profile local logs --tail=200 app-http

# Inspect startup jobs or the database.
podman-compose --profile local logs local-migrate local-seed
podman-compose --profile local logs db

# Open a shell in a running API container.
podman exec -it antinode-norma-http sh
```

If `down` or `logs` reports that `antinode-norma-mcp` does not exist, that service may not have been created for the current profile; check `podman ps -a --filter name=antinode-norma`. A missing optional container can produce a warning while other services are still processed.

## Apply Changes Without Rebuilding

The app services bind-mount the checkout at `/app`.

- **Python source edits:** The files appear immediately in the container, but Uvicorn is not started with `--reload`. Restart the API to load changed code:

  ```bash
  podman-compose --profile local restart app-http
  ```

- **`.env` edits:** Environment values are captured when a container is created. Recreate the stack without `--build` so the existing image is reused and Compose reloads `.env`:

  ```bash
  podman-compose --profile local down
  podman-compose --profile local up -d
  ```

- **Dockerfile or dependency changes:** Rebuild the image:

  ```bash
  podman-compose --profile local up --build -d
  ```

- **UI source while running Vite:** Vite HMR updates source files; this is separate from the container-served production UI. To refresh the compiled SPA served by FastAPI, build it in the mounted checkout:

  ```bash
  npm --prefix ui run build
  ```

After recreating the API, verify startup with `podman-compose --profile local ps`, `podman-compose --profile local logs --tail=100 app-http`, and `curl --fail http://localhost:8000/health`.

## Stop and Remove Data

Stop the project's containers and network while preserving the named PostgreSQL volume:

```bash
podman-compose --profile local down
```

To also delete the local PostgreSQL database volume, use `-v`. **This permanently deletes this Compose project's database data:**

```bash
podman-compose --profile local down -v
```

Local seed files are separate from the PostgreSQL volume. Remove only the known local seed outputs when intentionally resetting them:

```bash
rm -rf .runtime/local-seed .runtime/local-seed-complete.json
```

## WSL2 and SELinux Notes

- Run Podman commands inside Fedora WSL2 from the Fedora checkout. A Windows Vite process and a WSL container can have different meanings of `localhost`; keeping both in Fedora avoids that ambiguity.
- Prefer the distro's Linux filesystem over `/mnt/<drive>` for the checkout to avoid slow bind mounts and relabeling problems.
- The Compose bind mounts use `:Z` for SELinux-enabled Fedora. Keep the label; do not remove it to work around permissions without diagnosing the mount.
- Use `db` as the PostgreSQL hostname from containers. Use `localhost:8000` from the host browser for the published API.
- Do not commit `.env`, generated local state under `.runtime/`, or other local credentials.
