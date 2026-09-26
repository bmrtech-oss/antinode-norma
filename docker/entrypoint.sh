#!/bin/sh
set -eu

mode="${NORMA_RUNTIME_MODE:-http}"

case "$mode" in
  http)
    exec uvicorn antinode_norma.server.api:app --host "${NORMA_HTTP_HOST:-0.0.0.0}" --port "${NORMA_HTTP_PORT:-8000}"
    ;;
  mcp)
    exec python -m antinode_norma.server.mcp_server
    ;;
  all)
    echo "NORMA_RUNTIME_MODE=all is not supported in one container; use the app-http and app-mcp Compose services." >&2
    exit 2
    ;;
  *)
    echo "Unsupported NORMA_RUNTIME_MODE: $mode. Use http or mcp." >&2
    exit 2
    ;;
esac
