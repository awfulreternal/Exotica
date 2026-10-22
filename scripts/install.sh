#!/usr/bin/env sh
set -eu
if [ "$(id -u)" -eq 0 ]; then
  echo "Run installer as a regular user, not root." >&2
  exit 1
fi
PYTHON_BIN="${PYTHON_BIN:-python3}"
command -v "$PYTHON_BIN" >/dev/null 2>&1 || { echo "Python 3.11+ required." >&2; exit 1; }
"$PYTHON_BIN" - <<'PY'
import sys
if sys.version_info < (3, 11): raise SystemExit("Exotica requires Python 3.11+.")
PY
"$PYTHON_BIN" -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
echo "Installed. Activate: . .venv/bin/activate"
echo "Run: exotica doctor"
