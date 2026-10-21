# EXOTICA

Monochrome Telegram userbot framework for Linux VPS, local Linux, Termux and Docker.

**Version 0.3.0.** This release adds Telegram user authorization, a Telethon runtime, built-in outgoing commands, callback-based inline panels/forms, a navigable text gallery, an opt-in Python module loader and a small Hikka/Heroku-style compatibility facade.

## Features
- Monochrome CLI, diagnostics, private data paths and secret-aware logging.
- Telegram account login using API credentials from `my.telegram.org`; optional two-step verification.
- Telethon client runtime and built-in `.help`, `.ping`, `.exotica`, `.gallery`, `.form` commands.
- Inline callback panel, confirmation form and navigable text gallery demo.
- Explicitly opt-in local module engine and minimal `Module`, `@command`, `@tds` API.
- Small Hikka/Heroku-style facade for adapted modules; not a drop-in legacy loader.
- Backup/restore with archive path checks; Telegram session files are excluded from backups.
- Linux and Termux install scripts; non-root Docker image; tests.

## Install on Linux
Requires Python 3.11+.
```sh
git clone <YOUR-EXOTICA-REPOSITORY-URL> Exotica
cd Exotica
./scripts/install.sh
. .venv/bin/activate
exotica doctor
```

## Termux
Run inside Termux, not a root shell:
```sh
pkg install python git
git clone <YOUR-EXOTICA-REPOSITORY-URL> Exotica
cd Exotica
sh scripts/install-termux.sh
. .venv/bin/activate
```

## Telegram setup
1. Create API credentials at `https://my.telegram.org`.
2. Set credentials as environment variables (recommended):
   ```sh
   export EXOTICA_API_ID="your_numeric_api_id"
   export EXOTICA_API_HASH="your_api_hash"
   ```
   If omitted, Exotica prompts for them; the API hash prompt is hidden.
3. Authorize your own Telegram account:
   ```sh
   exotica login
   ```
   Enter the phone number, login code, and (if enabled) two-step verification password when prompted.
4. Start the runtime:
   ```sh
   exotica run
   ```
5. In a chat, send these commands as outgoing messages:
   - `.help` — commands
   - `.ping` — Telegram round-trip timing
   - `.exotica` — inline control panel
   - `.gallery` — navigable text gallery demo
   - `.form` — inline confirmation form

The session is stored in `$EXOTICA_HOME/sessions/main.session` (default `~/.local/share/exotica/sessions/main.session`). Treat it like a password. Never share it or upload it to issue trackers. Do not commit API credentials or session files.

## Local modules — read before enabling
Modules are **disabled by default**. Python modules execute with the same OS permissions as Exotica; this loader is not a sandbox and a manifest is not a security boundary. Only enable code you have personally reviewed:
```sh
mkdir -p "${EXOTICA_HOME:-$HOME/.local/share/exotica}/modules"
exotica run --allow-modules
```
A basic module can look like this:
```python
from exotica.modules.api import Module, command

class Example(Module):
    @command(name="hello", description="Example command")
    async def hello(self, event):
        await event.edit("EXOTICA / HELLO")
```
Save it as `example.py` in the modules directory, then restart with `--allow-modules`. Modules can access the authenticated client and therefore act as your account; review every line before enabling.

## Hikka / Heroku compatibility
Run `exotica compat` to see the implemented surface. A basic `Module` base class and `command` / `tds` decorators are available through `exotica.adapters.hikka_compat`. This is a compatibility starting point, **not full backwards compatibility**. Legacy modules using private loader imports, module configuration, databases, inline managers, galleries, or fork-specific APIs require individual porting. Do not blindly execute downloaded modules.

## Other commands
`exotica --version`, `exotica doctor`, `exotica paths`, `exotica modules`, `exotica compat`, `exotica backup`, `exotica restore <archive>`.

## Environment
- `EXOTICA_HOME`: data directory (default `~/.local/share/exotica`)
- `EXOTICA_API_ID`, `EXOTICA_API_HASH`: Telegram API credentials
- `EXOTICA_LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR, CRITICAL
- `NO_COLOR`: disable ANSI color

## Docker
Docker can run diagnostics and inspect files, but interactive Telegram login needs an interactive terminal and persistent `/data` volume. Never publish that volume.

## Licensing
Intended for GNU AGPL v3.0 or later. The current `LICENSE` file is a notice linking to the official full text, not the complete license text. Include the full applicable license before public distribution and preserve notices for copied/adapted code. Review dependency licenses.
