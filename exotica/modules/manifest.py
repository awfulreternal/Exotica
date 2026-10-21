from __future__ import annotations
import json
import re
from dataclasses import dataclass
from pathlib import Path

_NAME = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]{0,63}$")
_ALLOWED_PERMISSIONS = {"messages.read", "messages.write", "profile.read", "storage.read", "storage.write"}

@dataclass(frozen=True)
class ModuleManifest:
    name: str
    version: str
    description: str
    entrypoint: str
    permissions: tuple[str, ...]

def parse_manifest(path: Path) -> ModuleManifest:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read manifest: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError("Manifest must be a JSON object.")
    name, version = raw.get("name"), raw.get("version")
    description, entrypoint = raw.get("description", ""), raw.get("entrypoint")
    permissions = raw.get("permissions", [])
    if not isinstance(name, str) or not _NAME.fullmatch(name):
        raise ValueError("Invalid module name.")
    if not isinstance(version, str) or not version.strip():
        raise ValueError("Module version must be a non-empty string.")
    if not isinstance(description, str) or len(description) > 500:
        raise ValueError("Description must be text of at most 500 characters.")
    if not isinstance(entrypoint, str) or Path(entrypoint).is_absolute() or ".." in Path(entrypoint).parts:
        raise ValueError("Entrypoint must be relative and cannot traverse directories.")
    if not isinstance(permissions, list) or any(not isinstance(p, str) for p in permissions):
        raise ValueError("Permissions must be a list of strings.")
    unknown = set(permissions) - _ALLOWED_PERMISSIONS
    if unknown:
        raise ValueError(f"Unknown permissions: {', '.join(sorted(unknown))}")
    return ModuleManifest(name, version, description, entrypoint, tuple(permissions))

def inspect_manifests(directory: Path) -> list[ModuleManifest]:
    if not directory.exists():
        return []
    return [parse_manifest(path) for path in sorted(directory.glob("*.json"))]
