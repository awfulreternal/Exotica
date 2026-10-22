from __future__ import annotations

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Any

from . import __version__
from .backup import create_backup
from .config import data_dir, ensure_private_dir
from .ui import render_panel

log = logging.getLogger(__name__)

class TelegramSetupError(RuntimeError):
    pass

def _telethon():
    try:
        from telethon import TelegramClient, events, Button
        from telethon.errors import SessionPasswordNeededError
    except ImportError as exc:
        raise TelegramSetupError("Telethon is missing. Install with: pip install 'exotica-userbot[telegram]'") from exc
    return TelegramClient, events, Button, SessionPasswordNeededError

def _credentials() -> tuple[int, str]:
    raw_id = os.environ.get("EXOTICA_API_ID", "").strip()
    api_hash = os.environ.get("EXOTICA_API_HASH", "").strip()
    if not raw_id:
        raw_id = input("Telegram API ID (my.telegram.org): ").strip()
    if not api_hash:
        import getpass
        api_hash = getpass.getpass("Telegram API hash: ").strip()
    try:
        api_id = int(raw_id)
    except ValueError as exc:
        raise TelegramSetupError("EXOTICA_API_ID must be an integer.") from exc
    if api_id <= 0 or len(api_hash) < 20:
        raise TelegramSetupError("API ID/hash look invalid; obtain them from my.telegram.org.")
    return api_id, api_hash

def session_path() -> Path:
    folder = ensure_private_dir(data_dir() / "sessions")
    path = folder / "main"
    return path

async def authenticate() -> None:
    TelegramClient, _, _, SessionPasswordNeededError = _telethon()
    api_id, api_hash = _credentials()
    client = TelegramClient(str(session_path()), api_id, api_hash)
    try:
        await client.connect()
        if await client.is_user_authorized():
            me = await client.get_me()
            print(f"Already authorized as {getattr(me, 'username', None) or me.id}.")
            return
        phone = input("Phone number with country code: ").strip()
        if not phone:
            raise TelegramSetupError("Phone number cannot be empty.")
        await client.send_code_request(phone)
        code = input("Telegram login code: ").strip().replace(" ", "")
        try:
            await client.sign_in(phone=phone, code=code)
        except SessionPasswordNeededError:
            import getpass
            password = getpass.getpass("Two-step verification password: ")
            await client.sign_in(password=password)
        me = await client.get_me()
        print(f"Authorized as {getattr(me, 'username', None) or me.id}.")
        print(f"Session stored privately at: {session_path()}")
    finally:
        await client.disconnect()
    try:
        session_path().with_suffix(".session").chmod(0o600)
    except OSError:
        pass

class TelegramRuntime:
    def __init__(self, allow_modules: bool = False):
        TelegramClient, events, Button, _ = _telethon()
        self.events, self.Button = events, Button
        self.allow_modules = allow_modules
        self.api_id, self.api_hash = _credentials()
        self.client = TelegramClient(str(session_path()), self.api_id, self.api_hash)
        self.module_engine: Any = None
        self.started_at = time.monotonic()
        self.account_id: int | None = None
        self.account_label = "Unknown"

    async def run(self) -> None:
        from .modules.engine import ModuleEngine
        await self.client.connect()
        if not await self.client.is_user_authorized():
            await self.client.disconnect()
            raise TelegramSetupError("No authorized session. Run `exotica login` first.")
        me = await self.client.get_me()
        self.account_id = me.id
        self.account_label = getattr(me, "username", None) or getattr(me, "first_name", None) or str(me.id)
        self.started_at = time.monotonic()
        print(f"Connected as {self.account_label}. Exotica is running.")
        self.module_engine = ModuleEngine(self.client)
        if self.allow_modules:
            try:
                loaded = self.module_engine.load_all()
                print(f"Loaded {loaded} local module(s). They run with your account's permissions.")
            except Exception as exc:
                print(f"Module loading warning: {exc}")
        else:
            print("External modules are disabled. Start with --allow-modules only for reviewed code.")
        self._register_handlers()
        try:
            await self.client.run_until_disconnected()
        finally:
            await self.client.disconnect()

    def _register_handlers(self) -> None:
        events, Button = self.events, self.Button

        def module_summary() -> list[tuple[str, int]]:
            if not self.module_engine:
                return []
            counts: dict[int, int] = {}
            for instance, _ in self.module_engine.commands.values():
                identity = id(instance)
                counts[identity] = counts.get(identity, 0) + 1
            return [(type(instance).__name__, counts.get(id(instance), 0)) for instance in self.module_engine.instances]

        def module_commands() -> list[tuple[str, str]]:
            if not self.module_engine:
                return []
            commands = []
            for name, (instance, attr_name) in self.module_engine.commands.items():
                spec = getattr(getattr(instance, attr_name), "__exotica_command__", None)
                commands.append((name, getattr(spec, "description", "")))
            return commands

        def panel_text(page: str) -> str:
            return render_panel(
                page,
                account=self.account_label,
                user_id=self.account_id or 0,
                uptime=time.monotonic() - self.started_at,
                connected=self.client.is_connected(),
                version=__version__,
                modules_enabled=self.allow_modules,
                modules=module_summary(),
                module_commands=module_commands(),
            )

        def panel_buttons(page: str):
            if page == "home":
                return [
                    [Button.inline("Status", b"exo:status"), Button.inline("Modules", b"exo:modules")],
                    [Button.inline("Commands", b"exo:commands"), Button.inline("System", b"exo:system")],
                    [Button.inline("Backup", b"exo:backup"), Button.inline("Close", b"exo:close")],
                ]
            if page == "backup":
                return [[Button.inline("Create backup", b"exo:backup:run"), Button.inline("Cancel", b"exo:home")]]
            return [[Button.inline("‹ Home", b"exo:home")]]

        @self.client.on(events.NewMessage(outgoing=True, pattern=r"^\.help(?:\s|$)"))
        async def help_handler(event):
            await event.edit("EXOTICA  /  COMMANDS\n━━━━━━━━━━━━━━━━━━━━\n.help      Command reference\n.ping      Telegram round-trip\n.exotica   Open control room\n.gallery   Browse the demo gallery\n.form      Open confirmation demo\n\nOnly your outgoing commands are processed.")

        @self.client.on(events.NewMessage(outgoing=True, pattern=r"^\.ping(?:\s|$)"))
        async def ping_handler(event):
            import time
            start = time.perf_counter()
            msg = await event.edit("EXOTICA  /  CHECKING CONNECTION…")
            elapsed = (time.perf_counter() - start) * 1000
            await msg.edit(f"EXOTICA  /  CONNECTION OK\nTelegram round-trip   {elapsed:.0f} ms")

        @self.client.on(events.NewMessage(outgoing=True, pattern=r"^\.exotica(?:\s|$)"))
        async def panel_handler(event):
            await event.edit(panel_text("home"), buttons=panel_buttons("home"))

        @self.client.on(events.NewMessage(outgoing=True, pattern=r"^\.gallery(?:\s|$)"))
        async def gallery_handler(event):
            buttons = [[Button.inline("‹", b"exo:gallery:1"), Button.inline("1 / 3", b"exo:gallery:1"), Button.inline("›", b"exo:gallery:2")]]
            await event.edit("EXOTICA  /  GALLERY\n━━━━━━━━━━━━━━━━━━━━\n01  OVERVIEW\nInline navigation is active. Reviewed modules can provide media.", buttons=buttons)

        @self.client.on(events.NewMessage(outgoing=True, pattern=r"^\.form(?:\s|$)"))
        async def form_handler(event):
            buttons = [[Button.inline("Confirm", b"exo:form:confirm"), Button.inline("Cancel", b"exo:form:cancel")]]
            await event.edit("EXOTICA  /  CONFIRM ACTION\n━━━━━━━━━━━━━━━━━━━━\nChoose whether to continue.", buttons=buttons)

        @self.client.on(events.CallbackQuery())
        async def callback_handler(event):
            if not event.data or not event.data.startswith(b"exo:"):
                return
            if event.sender_id != self.account_id:
                await event.answer("Only the account owner can use this panel.", alert=True)
                return
            parts = event.data.decode("utf-8", "replace").split(":")
            action = parts[1] if len(parts) > 1 else ""
            if action in {"home", "status", "modules", "commands", "system"}:
                await event.edit(panel_text(action), buttons=panel_buttons(action))
            elif action == "backup" and len(parts) > 2 and parts[2] == "run":
                await event.answer("Creating private backup…")
                base = ensure_private_dir(data_dir())
                try:
                    archive = await asyncio.to_thread(create_backup, base, base / "backups")
                except Exception:
                    log.exception("Panel backup failed")
                    await event.edit("EXOTICA  /  BACKUP FAILED\n━━━━━━━━━━━━━━━━━━━━\nCheck the local logs for details.", buttons=panel_buttons("home"))
                else:
                    await event.edit(
                        "EXOTICA  /  BACKUP READY\n━━━━━━━━━━━━━━━━━━━━\n"
                        f"{archive.name}\nStored in the private backups directory.\n"
                        "Telegram sessions and .env files were excluded.",
                        buttons=panel_buttons("home"),
                    )
            elif action == "backup":
                await event.edit(panel_text("backup"), buttons=panel_buttons("backup"))
            elif action == "close":
                await event.edit("EXOTICA  /  PANEL CLOSED\nSend .exotica to reopen.", buttons=None)
            elif action == "gallery":
                page = parts[2] if len(parts) > 2 else "1"
                captions = {"1": "01 — Overview", "2": "02 — Inline navigation", "3": "03 — Module extension"}
                page = page if page in captions else "1"
                buttons = [[Button.inline("‹", f"exo:gallery:{max(1, int(page)-1)}".encode()), Button.inline(f"{page} / 3", b"exo:gallery:1"), Button.inline("›", f"exo:gallery:{min(3, int(page)+1)}".encode())]]
                await event.edit(f"EXOTICA  /  GALLERY\n━━━━━━━━━━━━━━━━━━━━\n{captions[page]}\n\nText gallery is active. A module can supply a media carousel.", buttons=buttons)
            elif action == "prev":
                await event.answer("Use the gallery navigation buttons.")
            elif action == "next":
                await event.answer("Use the gallery navigation buttons.")
            elif action == "form":
                result = parts[2] if len(parts) > 2 else "cancel"
                await event.edit("EXOTICA  /  FORM\n━━━━━━━━━━━━━━━━━━━━\n" + ("Confirmed." if result == "confirm" else "Cancelled."), buttons=None)
            else:
                await event.answer("Unknown action")
        if self.allow_modules and self.module_engine:
            self.module_engine.register_handlers(self.client, events)
