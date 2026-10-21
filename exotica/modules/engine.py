from __future__ import annotations
import importlib.util
import inspect
import logging
import re
from pathlib import Path
from types import ModuleType
from typing import Any
from ..config import data_dir, ensure_private_dir
from .api import Module, CommandSpec

log = logging.getLogger(__name__)
_NAME = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]{0,63}$")

class ModuleEngine:
    """Opt-in local Python module loader; modules execute with the user's full OS permissions."""
    def __init__(self, client):
        self.client = client
        self.directory = ensure_private_dir(data_dir() / "modules")
        self.instances: list[Module] = []
        self.commands: dict[str, tuple[Module, str]] = {}

    def load_all(self) -> int:
        for path in sorted(self.directory.glob("*.py")):
            if path.name.startswith("_"):
                continue
            if not _NAME.fullmatch(path.stem):
                log.warning("Skipping module with invalid filename: %s", path.name)
                continue
            self._load(path)
        return len(self.instances)

    def _load(self, path: Path) -> None:
        spec = importlib.util.spec_from_file_location(f"exotica_user_module_{path.stem}", path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot create import spec for {path.name}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # Explicit opt-in; arbitrary module code is not sandboxed.
        found = False
        for obj in vars(module).values():
            if inspect.isclass(obj) and issubclass(obj, Module) and obj is not Module and obj.__module__ == module.__name__:
                instance = obj()
                instance.client = self.client
                self.instances.append(instance)
                found = True
                for attr_name in dir(instance):
                    method = getattr(instance, attr_name)
                    spec_data = getattr(method, "__exotica_command__", None)
                    if spec_data is None and attr_name.endswith("_cmd") and inspect.iscoroutinefunction(method):
                        spec_data = CommandSpec(attr_name[:-4])
                    if spec_data:
                        self.commands[spec_data.name.lower()] = (instance, attr_name)
        if not found:
            log.warning("No Exotica Module subclass found in %s", path.name)

    def register_handlers(self, client, events) -> None:
        @client.on(events.NewMessage(outgoing=True, pattern=r"^\.([A-Za-z0-9_-]+)(?:\s|$)"))
        async def module_command_handler(event):
            name = event.pattern_match.group(1).lower()
            entry = self.commands.get(name)
            if not entry:
                return
            instance, attr_name = entry
            method: Any = getattr(instance, attr_name)
            try:
                if not instance.client:
                    instance.client = client
                await method(event)
            except Exception:
                log.exception("Module command failed: %s", name)
                await event.edit(f"EXOTICA / MODULE ERROR\nCommand: {name}\nSee local logs for details.")
