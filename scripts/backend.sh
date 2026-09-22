#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="$REPO_ROOT/.runtime"
PID_FILE="$RUNTIME_DIR/backend.pid"
LOG_FILE="$RUNTIME_DIR/backend.log"

mkdir -p "$RUNTIME_DIR"

usage() {
  echo "Usage: $0 {start|stop|status}"
  exit 2
}

is_running() {
  [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null
}

descendant_pids() {
  local parent="$1"
  ps -l | awk -v parent="$parent" 'NR > 1 && $2 == parent { print $1 }'
}

stop_tree() {
  local parent="$1"
  local child
  while read -r child; do
    [[ -n "$child" ]] && stop_tree "$child"
  done < <(descendant_pids "$parent")
  kill "$parent" 2>/dev/null || true
}

start() {
  if is_running; then
    echo "Backend is already running (PID $(cat "$PID_FILE"))."
    return 0
  fi
  rm -f "$PID_FILE"

  local python_cmd="$REPO_ROOT/.venv/Scripts/python.exe"
  if [[ ! -x "$python_cmd" ]]; then
    python_cmd="python"
  fi

  (
    cd "$REPO_ROOT"
    nohup "$python_cmd" -m uvicorn antinode_norma.server.api:app \
      --host 0.0.0.0 --port 8000 >>"$LOG_FILE" 2>&1 &
    echo $! >"$PID_FILE"
  )
  echo "Backend started: http://localhost:8000"
}

stop() {
  if ! is_running; then
    rm -f "$PID_FILE"
    echo "Backend is not running."
    return 0
  fi
  local pid
  pid="$(cat "$PID_FILE")"
  stop_tree "$pid"
  rm -f "$PID_FILE"
  echo "Backend stopped (PID $pid)."
}

status() {
  if is_running; then
    echo "Backend is running (PID $(cat "$PID_FILE")): http://localhost:8000"
  else
    rm -f "$PID_FILE"
    echo "Backend is not running."
  fi
}

case "${1:-}" in
  start) start ;;
  stop) stop ;;
  status) status ;;
  *) usage ;;
esac
