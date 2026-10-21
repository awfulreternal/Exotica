"""Minimal compatibility facade for writing/adapting Hikka/Heroku-like modules.

This does not make arbitrary legacy modules drop-in compatible. Imports such as
`from .. import loader, utils`, private database APIs and inline manager APIs need
individual adaptation. Only the small decorator/base-class surface below exists.
"""
from ..modules.api import Module, command, tds

class _LoaderFacade:
    Module = Module
    command = staticmethod(command)
    tds = staticmethod(tds)

loader = _LoaderFacade()

SUPPORTED_COMPATIBILITY = {
    "loader.Module": "basic facade available",
    "loader.command": "basic command decorator available",
    "loader.tds": "metadata decorator available",
    "module_config": "not implemented",
    "inline_forms": "basic Telegram callback panel only; legacy inline API not compatible",
    "galleries": "navigation demo; media gallery API not implemented",
    "database_api": "not implemented",
    "client_api": "Telethon client available on Exotica Module instances",
}

def compatibility_report() -> dict[str, str]:
    return dict(SUPPORTED_COMPATIBILITY)
