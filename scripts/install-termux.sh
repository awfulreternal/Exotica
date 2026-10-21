#!/data/data/com.termux/files/usr/bin/sh
set -eu
if [ -z "${PREFIX:-}" ] || [ ! -d "$PREFIX" ]; then
  echo "Run this script inside Termux." >&2
  exit 1
fi
pkg install -y python git
python - <<'PY'
import sys
if sys.version_info < (3, 11): raise SystemExit("Exotica requires Python 3.11+.")
PY
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
echo "Installed. Activate: . .venv/bin/activate"
echo "Run: exotica doctor"
