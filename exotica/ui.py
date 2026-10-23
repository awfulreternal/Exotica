from __future__ import annotations
import os
import platform
import sys

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
WHITE = "\033[97m"
CYAN = "\033[96m"

def color_enabled() -> bool:
    return sys.stdout.isatty() and "NO_COLOR" not in os.environ and os.environ.get("TERM") != "dumb"

def style(value: str, code: str) -> str:
    return f"{code}{value}{RESET}" if color_enabled() else value

def banner() -> str:
    from . import __version__
    host = "lavHost-compatible" if os.environ.get("LAVHOST") else "self-hosted"
    return "\n".join((
        style("  ┌─ EXOTICA ───────────────────────────────────────┐", BOLD + CYAN),
        style("  │  TELEGRAM USERBOT   /   HIKKA-INSPIRED          │", CYAN),
        style(f"  │  Version {__version__:<10}  {host:<25}│", DIM),
        style("  └────────────────────────────────────────────────┘", BOLD + CYAN),
    ))

def print_banner() -> None:
    print(banner())

def print_status(label: str, value: str) -> None:
    marker = style("›", CYAN)
    print(f"  {marker} {style(label, BOLD)}  {value}")


def format_uptime(seconds: float) -> str:
    total = max(0, int(seconds))
    days, remainder = divmod(total, 86_400)
    hours, remainder = divmod(remainder, 3_600)
    minutes, seconds = divmod(remainder, 60)
    if days:
        return f"{days}d {hours:02}:{minutes:02}:{seconds:02}"
    return f"{hours:02}:{minutes:02}:{seconds:02}"


def render_panel(
    page: str,
    *,
    account: str,
    user_id: int,
    uptime: float,
    connected: bool,
    version: str,
    modules_enabled: bool,
    modules: list[tuple[str, int]],
    module_commands: list[tuple[str, str]] | None = None,
) -> str:
    state = "CONNECTED" if connected else "DISCONNECTED"
    module_state = f"{len(modules)} loaded" if modules_enabled else "disabled · opt-in"
    heading = f"EXOTICA  /  {state}  /  v{version}"

    if page == "home":
        return "\n".join((
            heading,
            "━━━━━━━━━━━━━━━━━━━━",
            "CONTROL ROOM",
            f"Account   {account} · {user_id}",
            f"Uptime    {format_uptime(uptime)}",
            f"Modules   {module_state}",
            "",
            "Choose a section.",
        ))
    if page == "status":
        return "\n".join((
            heading,
            "━━━━━━━━━━━━━━━━━━━━",
            "RUNTIME STATUS",
            f"Telegram  {'Online' if connected else 'Offline'}",
            f"Account   {account}",
            f"ID        {user_id}",
            f"Uptime    {format_uptime(uptime)}",
            f"Modules   {module_state}",
        ))
    if page == "modules":
        lines = [heading, "━━━━━━━━━━━━━━━━━━━━", "MODULES", f"Execution  {module_state}"]
        if modules_enabled and modules:
            lines.extend(f"· {name}  /  {count} command(s)" for name, count in modules[:12])
            if len(modules) > 12:
                lines.append(f"· and {len(modules) - 12} more")
        elif modules_enabled:
            lines.append("No local modules loaded.")
        else:
            lines.append("Local Python modules are disabled.")
            lines.append("Enable only code you have reviewed.")
        return "\n".join(lines)
    if page == "commands":
        commands = [
            ".help      Command reference",
            ".ping      Telegram round-trip",
            ".exotica   Open this control room",
            ".gallery   Browse the demo gallery",
            ".form      Open the confirmation demo",
        ]
        commands.extend(
            f".{name}  {description or 'Module command'}"[:72]
            for name, description in (module_commands or [])[:12]
        )
        return "\n".join((heading, "━━━━━━━━━━━━━━━━━━━━", "COMMANDS", *commands))
    if page == "system":
        host = "lavHost-compatible" if os.environ.get("LAVHOST") else "self-hosted"
        return "\n".join((
            heading,
            "━━━━━━━━━━━━━━━━━━━━",
            "SYSTEM",
            f"Platform  {platform.system()} / {platform.machine()}",
            f"Python    {platform.python_version()}",
            f"Hosting   {host}",
            "Storage   private local data directory",
            "Session   private · excluded from backups",
        ))
    if page == "backup":
        return "\n".join((
            heading,
            "━━━━━━━━━━━━━━━━━━━━",
            "PRIVATE BACKUP",
            "Create an archive of managed Exotica data?",
            "Telegram sessions and .env files are excluded.",
        ))
    return heading
