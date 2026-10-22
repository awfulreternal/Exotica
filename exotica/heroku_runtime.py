from __future__ import annotations

import os
import subprocess
import sys
from importlib.util import find_spec
from pathlib import Path

from .config import data_dir, ensure_private_dir

_SOURCE_ROOT = Path(__file__).resolve().parent.parent / "vendor" / "heroku"
_INSTALLED_SPEC = find_spec("heroku")
HEROKU_ROOT = (
    _SOURCE_ROOT
    if (_SOURCE_ROOT / "heroku" / "__main__.py").is_file()
    else Path(_INSTALLED_SPEC.origin).resolve().parent.parent
    if _INSTALLED_SPEC and _INSTALLED_SPEC.origin
    else _SOURCE_ROOT
)


def run_heroku(arguments: list[str] | None = None) -> int:
    if not (HEROKU_ROOT / "heroku" / "__main__.py").is_file():
        raise RuntimeError(f"Vendored Heroku runtime is missing: {HEROKU_ROOT}")

    home = ensure_private_dir(data_dir()).resolve()
    environment = os.environ.copy()
    pythonpath = environment.get("PYTHONPATH", "")
    environment["PYTHONPATH"] = os.pathsep.join(
        part for part in (str(HEROKU_ROOT), pythonpath) if part
    )
    environment["EXOTICA_HOME"] = str(home)
    environment["EXOTICA_RUNTIME_ROOT"] = str(HEROKU_ROOT)
    environment["HEROKU_NO_GIT"] = "1"
    environment["EXOTICA_MANAGED_INSTALL"] = "1"

    if api_id := environment.get("EXOTICA_API_ID"):
        environment["api_id"] = api_id
    if api_hash := environment.get("EXOTICA_API_HASH"):
        environment["api_hash"] = api_hash

    command = [sys.executable, "-m", "heroku", "--no-git", *(arguments or [])]
    command.extend(("--data-root", str(home)))
    result = subprocess.run(
        command,
        cwd=home,
        env=environment,
        check=False,
        start_new_session=True,
    )
    return result.returncode