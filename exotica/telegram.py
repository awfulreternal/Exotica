from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

from .config import data_dir, ensure_private_dir

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

    async def run(self) -> None:
        from .modules.engine import ModuleEngine
        await self.client.connect()
        if not await self.client.is_user_authorized():
            await self.client.disconnect()
            raise TelegramSetupError("No authorized session. Run `exotica login` first.")
        me = await self.client.get_me()
        print(f"Connected as {getattr(me, 'username', None) or me.id}. Exotica is running.")
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
        @self.client.on(events.NewMessage(outgoing=True, pattern=r"^\.help(?:\s|$)"))
        async def help_handler(event):
            await event.edit("EXOTICA / COMMANDS\n───────────────\n.help — command list\n.ping — connection latency\n.exotica — inline control panel\n.gallery — text gallery with callback navigation\n.form — inline confirmation form\n\nOnly commands sent by you are processed.")

        @self.client.on(events.NewMessage(outgoing=True, pattern=r"^\.ping(?:\s|$)"))
        async def ping_handler(event):
            import time
            start = time.perf_counter()
            msg = await event.edit("EXOTICA / PING…")
            elapsed = (time.perf_counter() - start) * 1000
            await msg.edit(f"EXOTICA / PONG\nTelegram round-trip: {elapsed:.0f} ms")

        @self.client.on(events.NewMessage(outgoing=True, pattern=r"^\.exotica(?:\s|$)"))
        async def panel_handler(event):
            buttons = [[Button.inline("Status", b"exo:status"), Button.inline("Commands", b"exo:help")], [Button.inline("Close", b"exo:close")]]
            await event.edit("EXOTICA\n───────────────\nMonochrome userbot control panel", buttons=buttons)

        @self.client.on(events.NewMessage(outgoing=True, pattern=r"^\.gallery(?:\s|$)"))
        async def gallery_handler(event):
            buttons = [[Button.inline("‹", b"exo:gallery:1"), Button.inline("1 / 3", b"exo:gallery:1"), Button.inline("›", b"exo:gallery:2")]]
            await event.edit("EXOTICA / GALLERY\n\n01 — Overview\nInline navigation is active. Add reviewed modules to display actual media.", buttons=buttons)

        @self.client.on(events.NewMessage(outgoing=True, pattern=r"^\.form(?:\s|$)"))
        async def form_handler(event):
            buttons = [[Button.inline("Confirm", b"exo:form:confirm"), Button.inline("Cancel", b"exo:form:cancel")]]
            await event.edit("EXOTICA / CONFIRMATION FORM\n\nChoose an action below. This is a callback-based inline form.", buttons=buttons)

        @self.client.on(events.CallbackQuery())
        async def callback_handler(event):
            if not event.data or not event.data.startswith(b"exo:"):
                return
            parts = event.data.decode("utf-8", "replace").split(":")
            action = parts[1] if len(parts) > 1 else ""
            if action == "status":
                await event.answer("Connected", alert=True)
            elif action == "help":
                await event.answer(".help  .ping  .exotica  .gallery", alert=True)
            elif action == "close":
                await event.edit("EXOTICA / PANEL CLOSED", buttons=None)
            elif action == "gallery":
                page = parts[2] if len(parts) > 2 else "1"
                captions = {"1": "01 — Overview", "2": "02 — Inline navigation", "3": "03 — Module extension"}
                page = page if page in captions else "1"
                buttons = [[Button.inline("‹", f"exo:gallery:{max(1, int(page)-1)}".encode()), Button.inline(f"{page} / 3", b"exo:gallery:1"), Button.inline("›", f"exo:gallery:{min(3, int(page)+1)}".encode())]]
                await event.edit(f"EXOTICA / GALLERY\n\n{captions[page]}\n\nText gallery is active. A media carousel can be supplied by a module.", buttons=buttons)
            elif action == "prev":
                await event.answer("Use the gallery navigation buttons.")
            elif action == "next":
                await event.answer("Use the gallery navigation buttons.")
            elif action == "form":
                result = parts[2] if len(parts) > 2 else "cancel"
                await event.edit("EXOTICA / FORM\n\n" + ("Confirmed." if result == "confirm" else "Cancelled."), buttons=None)
            else:
                await event.answer("Unknown action")
        if self.allow_modules and self.module_engine:
            self.module_engine.register_handlers(self.client, events)
