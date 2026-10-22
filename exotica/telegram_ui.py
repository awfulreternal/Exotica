from __future__ import annotations


def telegram_emoji(document_id: int, fallback: str, *, premium: bool) -> str:
    if not premium:
        return fallback
    return f'<tg-emoji emoji-id="{document_id}">{fallback}</tg-emoji>'
