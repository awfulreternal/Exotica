from __future__ import annotations
import logging
import os
import re

_SECRET_ASSIGNMENT = re.compile(r"(?i)(api_hash|api_key|token|session_string|password|auth_code)(\s*[=:]\s*)(\S+)")
_BOT_TOKEN = re.compile(r"(?i)\b\d{5,}:[A-Za-z0-9_-]{20,}\b")

class SecretRedactionFilter(logging.Filter):
    """Best-effort redaction; callers must still avoid logging secrets."""
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        message = _SECRET_ASSIGNMENT.sub(r"\1\2[REDACTED]", message)
        message = _BOT_TOKEN.sub("[REDACTED_TOKEN]", message)
        record.msg, record.args = message, ()
        return True

def configure_logging() -> None:
    level = getattr(logging, os.environ.get("EXOTICA_LOG_LEVEL", "INFO").upper(), logging.INFO)
    handler = logging.StreamHandler()
    handler.addFilter(SecretRedactionFilter())
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
