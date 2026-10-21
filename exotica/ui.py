from __future__ import annotations
import os
import sys

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
WHITE = "\033[97m"

def color_enabled() -> bool:
    return sys.stdout.isatty() and "NO_COLOR" not in os.environ and os.environ.get("TERM") != "dumb"

def style(value: str, code: str) -> str:
    return f"{code}{value}{RESET}" if color_enabled() else value

def banner() -> str:
    art = [
        "  ███████╗██╗  ██╗ ██████╗ ████████╗██╗ ██████╗ █████╗ ",
        "  ██╔════╝╚██╗██╔╝██╔═══██╗╚══██╔══╝██║██╔════╝██╔══██╗",
        "  █████╗   ╚███╔╝ ██║   ██║   ██║   ██║██║     ███████║",
        "  ██╔══╝   ██╔██╗ ██║   ██║   ██║   ██║██║     ██╔══██║",
        "  ███████╗██╔╝ ██╗╚██████╔╝   ██║   ██║╚██████╗██║  ██║",
        "  ╚══════╝╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚═╝ ╚═════╝╚═╝  ╚═╝",
    ]
    return style("  EXOTICA", BOLD + WHITE) + "\n" + "\n".join(style(line, BOLD + WHITE) for line in art) + "\n" + style("  MONOCHROME USERBOT FRAMEWORK  /  v0.2.0", DIM)

def print_banner() -> None:
    print(banner())

def print_status(label: str, value: str) -> None:
    print(f"  {style(label, BOLD)}  {value}")
