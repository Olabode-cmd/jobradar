#!/usr/bin/env bash
# One-time setup: Python venv + dependencies, backend init, dashboard build.
# Run this once after cloning. It is safe to re-run.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── colour helpers ─────────────────────────────────────────────────────────────
if [[ -t 1 ]]; then
  GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; RESET='\033[0m'
else
  GREEN=''; YELLOW=''; RED=''; RESET=''
fi
ok()   { echo -e "${GREEN}✓${RESET}  $*"; }
warn() { echo -e "${YELLOW}!${RESET}  $*"; }
fail() { echo -e "${RED}✗  $*${RESET}" >&2; exit 1; }
step() { echo; echo -e "${YELLOW}▶${RESET}  $*"; }

# ── check prerequisites ────────────────────────────────────────────────────────
step "Checking prerequisites"

PYTHON=""
for cmd in python3 python; do
  if command -v "$cmd" >/dev/null 2>&1; then
    version="$("$cmd" -c 'import sys; print(sys.version_info[:2])')"
    major=$("$cmd" -c 'import sys; print(sys.version_info[0])')
    minor=$("$cmd" -c 'import sys; print(sys.version_info[1])')
    if [[ "$major" -eq 3 && "$minor" -ge 11 ]]; then
      PYTHON="$cmd"
      ok "Python $("$cmd" --version)"
      break
    fi
  fi
done
[[ -n "$PYTHON" ]] || fail "Python 3.11 or newer is required. Get it from https://www.python.org/downloads/"

if command -v bun >/dev/null 2>&1; then
  ok "Bun $(bun --version)"
else
  fail "Bun is required. Install it in one command: curl -fsSL https://bun.sh/install | bash
       (or see https://bun.sh for other install options)"
fi

# ── Python virtual environment ─────────────────────────────────────────────────
step "Setting up Python environment"

VENV="$ROOT/backend/.venv"
if [[ ! -d "$VENV" ]]; then
  "$PYTHON" -m venv "$VENV"
  ok "Created virtual environment"
else
  ok "Virtual environment already exists"
fi

# Resolve the python binary inside the venv (Windows vs Unix)
if [[ -f "$VENV/Scripts/python.exe" ]]; then
  PY="$VENV/Scripts/python.exe"
  PIP="$VENV/Scripts/pip.exe"
else
  PY="$VENV/bin/python"
  PIP="$VENV/bin/pip"
fi

step "Installing Python packages (this may take a minute)"
"$PIP" install --quiet --upgrade pip
"$PIP" install --quiet -r "$ROOT/backend/requirements.txt"
ok "Python packages installed"

# ── backend initialisation ─────────────────────────────────────────────────────
step "Initialising the backend"
(cd "$ROOT/backend" && "$PY" -m app.cli setup)
ok "Backend ready (.env, database)"

# ── web dashboard ──────────────────────────────────────────────────────────────
step "Installing dashboard dependencies"
(cd "$ROOT/web" && bun install --frozen-lockfile 2>/dev/null || bun install)
ok "Node packages installed"

step "Building the dashboard"
(cd "$ROOT/web" && bun run build)
ok "Dashboard built"

# ── optional: browser for Tier C sources (Indeed, Wellfound) ──────────────────
echo
echo -e "${YELLOW}Optional:${RESET} Indeed and Wellfound need a real browser to load."
echo "  If you plan to enable them (Tier C, off by default),"
echo "  run this once:"
echo
echo "    backend/.venv/Scripts/python.exe -m patchright install chromium   # Windows"
echo "    backend/.venv/bin/python -m patchright install chromium            # Mac / Linux"

# ── done ───────────────────────────────────────────────────────────────────────
echo
ok "Setup complete."
echo
echo "  Start the app:"
echo "    ./start.sh"
echo
echo "  Then open http://127.0.0.1:8000"
echo "  The first screen asks what job you're looking for, then fetches your first matches."
echo
