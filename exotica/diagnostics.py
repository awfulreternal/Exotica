from __future__ import annotations
import platform
import sys
from pathlib import Path
from .config import ensure_private_dir
from .heroku_runtime import HEROKU_ROOT

def collect_diagnostics(path: Path) -> list[tuple[str, str]]:
    ensure_private_dir(path)
    return [
        ("Python", platform.python_version()),
        ("Platform", f"{platform.system()} / {platform.machine()}"),
        ("Data directory", str(path)),
        ("Directory exists", str(path.is_dir())),
        ("Permissions", oct(path.stat().st_mode & 0o777) if sys.platform != "win32" else "platform-managed"),
        (
            "Telegram runtime",
            "Heroku / Hikka-derived runtime available"
            if (HEROKU_ROOT / "heroku" / "__main__.py").is_file()
            else "vendored runtime missing",
        ),
        ("Result", "checks complete"),
    ]
