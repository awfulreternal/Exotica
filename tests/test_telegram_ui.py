from exotica.telegram_ui import telegram_emoji


def test_premium_emoji_uses_document_id_for_premium_accounts():
    assert telegram_emoji(123456789, "🪐", premium=True) == (
        '<tg-emoji emoji-id="123456789">🪐</tg-emoji>'
    )


def test_premium_emoji_falls_back_to_unicode_for_standard_accounts():
    assert telegram_emoji(123456789, "🪐", premium=False) == "🪐"
