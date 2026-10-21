from __future__ import annotations
import argparse
import os
import sys
import tarfile
from pathlib import Path

from . import __version__
from .backup import BackupError, create_backup, restore_backup
from .config import data_dir, ensure_private_dir, validate_log_level
from .diagnostics import collect_diagnostics
from .logging_setup import configure_logging
from .modules.manifest import inspect_manifests
from .ui import print_banner, print_status

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="exotica", description="Exotica — monochrome Telegram userbot framework")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("doctor", help="check runtime and private data directory")
    sub.add_parser("paths", help="show application data path")
    sub.add_parser("modules", help="inspect module manifests without executing code")
    sub.add_parser("backup", help="create a private archive of managed data")
    restore = sub.add_parser("restore", help="restore a validated archive")
    restore.add_argument("archive", type=Path)
    sub.add_parser("login", help="authorize a Telegram account and create a local session")
    run = sub.add_parser("run", help="connect to Telegram and start Exotica")
    run.add_argument("--allow-modules", action="store_true", help="execute reviewed local Python modules (full OS permissions)")
    sub.add_parser("compat", help="show Hikka/Heroku compatibility surface")
    return parser

def main(argv: list[str] | None = None) -> int:
    try:
        validate_log_level(os.environ.get("EXOTICA_LOG_LEVEL"))
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2
    configure_logging()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        print_banner()
        print("\n  COMMANDS\n  --------")
        print("  doctor   Runtime and permissions diagnostics")
        print("  modules  Inspect local module manifests")
        print("  backup   Create a private data backup")
        print("  restore  Restore a validated backup")
        print("  paths    Show data directory")
        print("  login    Authorize Telegram")
        print("  run      Start Telegram runtime")
        print("  compat   Show legacy compatibility status")
        return 0
    if args.command == "login":
        try:
            from .telegram import authenticate
            import asyncio
            asyncio.run(authenticate())
        except (RuntimeError, OSError, ValueError) as exc:
            print(f"Telegram login failed: {exc}", file=sys.stderr)
            return 2
        return 0
    if args.command == "run":
        try:
            from .telegram import TelegramRuntime
            import asyncio
            asyncio.run(TelegramRuntime(allow_modules=args.allow_modules).run())
        except (RuntimeError, OSError, ValueError) as exc:
            print(f"Exotica runtime failed: {exc}", file=sys.stderr)
            return 2
        except KeyboardInterrupt:
            print("\nExotica stopped.")
            return 130
        return 0
    if args.command == "compat":
        from .adapters.hikka_compat import compatibility_report
        for name, status in compatibility_report().items():
            print(f"{name}: {status}")
        return 0
    if args.command == "doctor":
        for label, value in collect_diagnostics(data_dir()):
            print_status(label, value)
        return 0
    if args.command == "paths":
        print(data_dir())
        return 0
    if args.command == "modules":
        directory = ensure_private_dir(data_dir()) / "modules"
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            manifests = inspect_manifests(directory)
        except ValueError as exc:
            print(f"Module manifest error: {exc}", file=sys.stderr)
            return 2
        if not manifests:
            print("No module manifests found.")
            print(f"Directory: {directory}")
            print("Metadata inspection only; module code is never executed.")
            return 0
        for item in manifests:
            print(f"{item.name}  v{item.version}")
            print(f"  {item.description}")
            print(f"  Permissions: {', '.join(item.permissions) or 'none'}")
            print(f"  Entrypoint (not executed): {item.entrypoint}")
        return 0
    if args.command == "backup":
        base = ensure_private_dir(data_dir())
        try:
            target = create_backup(base, base / "backups")
        except (BackupError, OSError, tarfile.TarError) as exc:
            print(f"Backup failed: {exc}", file=sys.stderr)
            return 2
        print(f"Backup created: {target}")
        return 0
    if args.command == "restore":
        try:
            count = restore_backup(args.archive, data_dir())
        except (BackupError, OSError, tarfile.TarError) as exc:
            print(f"Restore failed: {exc}", file=sys.stderr)
            return 2
        print(f"Restore complete. Archive entries processed: {count}")
        return 0
    parser.print_help()
    return 0
