"""Small, intentionally limited module API for Exotica and adapted legacy modules."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable

@dataclass(frozen=True)
class CommandSpec:
    name: str
    description: str = ""

def command(func: Callable | None = None, *, name: str | None = None, description: str = ""):
    def decorate(fn):
        fn.__exotica_command__ = CommandSpec(name or fn.__name__.removesuffix("_cmd"), description)
        return fn
    return decorate(func) if func else decorate

def tds(cls=None, **metadata):
    def decorate(target):
        target.__exotica_metadata__ = dict(metadata)
        return target
    return decorate(cls) if cls else decorate

class Module:
    """Base class for explicitly enabled local modules. No sandbox is provided."""
    strings: dict[str, str] = {}
    def __init__(self):
        self.client: Any = None
        self.db: dict[str, Any] = {}
    async def client_ready(self, client, db=None):
        self.client = client
        self.db = db if isinstance(db, dict) else {}
