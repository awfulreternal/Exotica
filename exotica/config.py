from __future__ import annotations
import os
from pathlib import Path

def data_dir() -> Path:
    override = os.environ.get("EXOTICA_HOME")
    return Path(override).expanduser() if override else Path.home() / ".local" / "share" / "exotica"

def ensure_private_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        path.chmod(0o700)
    except OSError:
        pass
    return path

def validate_log_level(value: str | None) -> str:
    level = (value or "INFO").upper()
    if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ValueError(f"Invalid log level: {level}")
    return level
