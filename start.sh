#!/usr/bin/env bash
# Runs the API (http://127.0.0.1:8000, auto-reload) and the dashboard dev server
# (http://127.0.0.1:5173, proxies /api to the API) together. Ctrl+C stops both.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -x "$ROOT/backend/.venv/Scripts/python.exe" ]]; then
  PYTHON="$ROOT/backend/.venv/Scripts/python.exe"
elif [[ -x "$ROOT/backend/.venv/bin/python" ]]; then
  PYTHON="$ROOT/backend/.venv/bin/python"
else
  echo "No backend virtualenv found. Run: cd backend && python -m venv .venv && pip install -r requirements.txt" >&2
  exit 1
fi

if ! command -v bun >/dev/null 2>&1; then
  echo "Bun is not installed. Get it from https://bun.sh" >&2
  exit 1
fi

if [[ ! -d "$ROOT/web/node_modules" ]]; then
  echo "Dashboard dependencies are missing. Run: cd web && bun install" >&2
  exit 1
fi

# Kills a process and everything it started. On Windows (Git Bash) a plain `kill` leaves the
# children of native processes running, so go through taskkill with the Windows pid.
stop_tree() {
  local pid="$1" winpid
  if command -v taskkill >/dev/null 2>&1; then
    winpid="$(ps -p "$pid" 2>/dev/null | awk 'NR==2 {print $4}')"
    taskkill //PID "${winpid:-$pid}" //T //F >/dev/null 2>&1 || true
  else
    pkill -TERM -P "$pid" 2>/dev/null || true
    kill "$pid" 2>/dev/null || true
  fi
}

pids=()
cleanup() {
  trap - EXIT INT TERM
  for pid in "${pids[@]}"; do
    stop_tree "$pid"
  done
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

(cd "$ROOT/backend" && exec "$PYTHON" -m uvicorn app.main:app --reload --port 8000) &
pids+=($!)
(cd "$ROOT/web" && exec bun run dev) &
pids+=($!)

echo "API        http://127.0.0.1:8000"
echo "Dashboard  http://127.0.0.1:5173"
echo "Press Ctrl+C to stop both."

# Exit as soon as either process dies, so a crashed API doesn't leave a dashboard talking to nothing.
while kill -0 "${pids[0]}" 2>/dev/null && kill -0 "${pids[1]}" 2>/dev/null; do
  sleep 1
done
