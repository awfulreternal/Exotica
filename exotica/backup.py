from __future__ import annotations
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import tarfile
from .config import ensure_private_dir

_SENSITIVE_KEYS = {"api_hash", "api_token", "auth_key", "authkey", "bot_token", "password", "session", "token"}


def _redact_secrets(value):
    if isinstance(value, dict):
        return {
            key: _redact_secrets(item)
            for key, item in value.items()
            if str(key).lower().replace("-", "_") not in _SENSITIVE_KEYS
        }
    if isinstance(value, list):
        return [_redact_secrets(item) for item in value]
    return value

class BackupError(ValueError):
    pass

def create_backup(source: Path, destination_dir: Path) -> Path:
    source = source.resolve()
    if not source.is_dir():
        raise BackupError("Data directory does not exist.")
    ensure_private_dir(destination_dir)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = destination_dir / f"exotica-backup-{stamp}.tar.gz"
    def excluded(path: Path) -> bool:
        name = path.name.lower()
        return (
            name.endswith((".session", ".session-journal", ".env"))
            or name == ".env"
            or name == "api_token.txt"
            or name.startswith("exotica-backup-")
            or "__pycache__" == name
        )

    def add_item(item: Path, arcname: str) -> None:
        if item.suffix.lower() == ".json" and item.is_file():
            try:
                contents = json.loads(item.read_text(encoding="utf-8"))
                payload = json.dumps(
                    _redact_secrets(contents), ensure_ascii=False, indent=2
                ).encode("utf-8")
            except (OSError, ValueError):
                return
            info = tarfile.TarInfo(arcname)
            info.size = len(payload)
            info.mode = 0o600
            info.mtime = item.stat().st_mtime
            archive.addfile(info, io.BytesIO(payload))
            return
        archive.add(item, arcname=arcname, recursive=False)

    with tarfile.open(target, "w:gz") as archive:
        for item in source.iterdir():
            if item.resolve() == destination_dir.resolve() or excluded(item):
                continue
            if item.is_dir():
                for child in sorted(item.rglob("*")):
                    if excluded(child):
                        continue
                    # Do not recurse into excluded directories.
                    if any(excluded(parent) for parent in child.parents if parent != source.parent and parent != source):
                        continue
                    add_item(child, str(child.relative_to(source)))
                add_item(item, item.name)
            else:
                add_item(item, item.name)
    try:
        target.chmod(0o600)
    except OSError:
        pass
    return target

def restore_backup(archive_path: Path, destination: Path) -> int:
    destination = ensure_private_dir(destination)
    base = destination.resolve()
    with tarfile.open(archive_path, "r:gz") as archive:
        members = archive.getmembers()
        for member in members:
            p = Path(member.name)
            if p.is_absolute() or ".." in p.parts or not p.parts:
                raise BackupError(f"Unsafe archive path: {member.name}")
            if member.issym() or member.islnk() or member.isdev():
                raise BackupError(f"Unsupported archive member: {member.name}")
            if not (member.isfile() or member.isdir()):
                raise BackupError(f"Unsupported archive member: {member.name}")
        # Extract each validated regular file/directory manually. Avoid tarfile's
        # version-dependent extraction filters and never extract links/devices.
        count = 0
        for member in members:
            target = (base / member.name).resolve()
            if target != base and base not in target.parents:
                raise BackupError(f"Unsafe resolved path: {member.name}")
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True, mode=0o700)
            else:
                target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                source = archive.extractfile(member)
                if source is None:
                    raise BackupError(f"Cannot read archive member: {member.name}")
                with source, target.open("wb") as output:
                    output.write(source.read())
                try:
                    target.chmod(0o600)
                except OSError:
                    pass
            count += 1
    return count
