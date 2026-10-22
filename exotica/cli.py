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
from .ui import print_banner, print_status

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="exotica", description="Exotica — Hikka-derived Telegram userbot")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("doctor", help="check runtime and private data directory")
    sub.add_parser("paths", help="show application data path")
    sub.add_parser("modules", help="list downloaded runtime modules without executing code")
    sub.add_parser("backup", help="create a private archive of managed data")
    restore = sub.add_parser("restore", help="restore a validated archive")
    restore.add_argument("archive", type=Path)
    sub.add_parser("login", help="start the interactive first-run login and userbot")
    sub.add_parser("run", help="start the Heroku/Hikka userbot runtime")
    sub.add_parser("legacy-login", help="authorize using the retired Telethon runtime")
    legacy_run = sub.add_parser("legacy-run", help="start the retired Telethon runtime")
    legacy_run.add_argument("--allow-modules", action="store_true", help="execute reviewed local Python modules (full OS permissions)")
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
    raw_args = list(sys.argv[1:] if argv is None else argv)
    if raw_args and raw_args[0] in {"run", "login"}:
        from .heroku_runtime import run_heroku
        try:
            heroku_args = raw_args[1:] if raw_args[0] == "run" else ["--no-web", *raw_args[1:]]
            return run_heroku(heroku_args)
        except (RuntimeError, OSError, ValueError) as exc:
            print(f"Exotica runtime failed: {exc}", file=sys.stderr)
            return 2
    args = parser.parse_args(raw_args)

    if args.command is None:
        print_banner()
        print("\n  COMMANDS\n  --------")
        print("  doctor   Runtime and permissions diagnostics")
        print("  modules  List downloaded runtime modules (read-only)")
        print("  backup   Create a private data backup")
        print("  restore  Restore a validated backup")
        print("  paths    Show data directory")
        print("  login    First-run authorization and startup")
        print("  run      Start Heroku/Hikka runtime")
        print("  legacy-run  Start retired Telethon runtime")
        print("  compat   Show legacy compatibility status")
        return 0
    if args.command == "legacy-login":
        try:
            from .telegram import authenticate
            import asyncio
            asyncio.run(authenticate())
        except (RuntimeError, OSError, ValueError) as exc:
            print(f"Telegram login failed: {exc}", file=sys.stderr)
            return 2
        return 0
    if args.command == "legacy-run":
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
        directory = ensure_private_dir(data_dir()) / "loaded_modules"
        files = sorted(path for path in directory.glob("*.py") if not path.name.startswith("_"))
        if not files:
            print("No downloaded runtime modules found.")
            print(f"Directory: {directory}")
            print("Source inspection only; module code is never executed.")
            return 0
        for path in files:
            print(f"{path.name}  {path.stat().st_size} bytes")
        print("Source listing only; module code is never executed by this command.")
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
