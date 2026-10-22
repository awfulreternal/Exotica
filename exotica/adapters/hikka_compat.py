"""Compatibility status for the vendored Hikka-derived Heroku runtime."""
from ..modules.api import Module, command, tds

class _LoaderFacade:
    Module = Module
    command = staticmethod(command)
    tds = staticmethod(tds)

loader = _LoaderFacade()

SUPPORTED_COMPATIBILITY = {
    "runtime": "Heroku Userbot with Hikka-derived module loader and Heroku-TL client",
    "hikka_imports": "Hikka imports are remapped by upstream loader; fork-specific APIs may differ",
    "module_config": "upstream ModuleConfig, ConfigValue and validators included",
    "inline_forms": "upstream inline form API included",
    "inline_lists": "upstream inline list API included",
    "galleries": "upstream inline media galleries included",
    "database_api": "upstream persistent module database included",
    "security": "upstream owner/group permissions and API flood protection included",
    "client_api": "Heroku-TL client; one Telegram client stack is installed",
}

def compatibility_report() -> dict[str, str]:
    return dict(SUPPORTED_COMPATIBILITY)
