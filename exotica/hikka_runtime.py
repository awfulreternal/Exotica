from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from .config import data_dir, ensure_private_dir

HIKKA_ROOT = Path(__file__).resolve().parent.parent / "vendor" / "hikka"


def run_hikka(arguments: list[str] | None = None) -> int:
    if not (HIKKA_ROOT / "hikka" / "__main__.py").is_file():
        raise RuntimeError(f"Vendored Hikka runtime is missing: {HIKKA_ROOT}")

    home = ensure_private_dir(data_dir()).resolve()
    environment = os.environ.copy()
    pythonpath = environment.get("PYTHONPATH", "")
    environment["PYTHONPATH"] = os.pathsep.join(
        part for part in (str(HIKKA_ROOT), pythonpath) if part
    )
    environment["EXOTICA_HOME"] = str(home)

    if api_id := environment.get("EXOTICA_API_ID"):
        environment["api_id"] = api_id
    if api_hash := environment.get("EXOTICA_API_HASH"):
        environment["api_hash"] = api_hash

    command = [sys.executable, "-m", "hikka", *(arguments or [])]
    command.extend(("--data-root", str(home)))
    result = subprocess.run(
        command,
        cwd=HIKKA_ROOT,
        env=environment,
        check=False,
        start_new_session=True,
    )
    return result.returncode