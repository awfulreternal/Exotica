from __future__ import annotations

import re


_CUSTOM_EMOJI = re.compile(r'<tg-emoji emoji-id=["\']?\d+["\']?>(.*?)</tg-emoji>')


def telegram_emoji(document_id: int, fallback: str, *, premium: bool) -> str:
    if not premium:
        return fallback
    return f'<tg-emoji emoji-id="{document_id}">{fallback}</tg-emoji>'


def resolve_custom_emoji(text: str, *, premium: bool) -> str:
    """Keep Telegram custom emoji for Premium accounts, use readable fallback otherwise."""
    return text if premium else _CUSTOM_EMOJI.sub(r"\1", text)
