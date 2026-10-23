# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

# ©️ Codrago, 2024-2030
# This file is a part of Heroku Userbot
# 🌐 https://github.com/Heroku-userbot/Heroku
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import logging

from .. import loader, translations, utils
from ..inline.types import BotInlineCall
from exotica.telegram_ui import resolve_custom_emoji

logger = logging.getLogger(__name__)


@loader.tds
class Quickstart(loader.Module):
    """Notifies user about userbot installation"""

    strings = {
        "name": "ExoticaWelcome",
        "exotica_welcome": (
            "{}<tg-emoji emoji-id=5393588431026674882>🪐</tg-emoji> "
            "<b>EXOTICA</b>  ·  <b>Hikka is ready.</b>\n\n"
            "<tg-emoji emoji-id=5870609858520158157>ℹ️</tg-emoji> "
            "<b>.exotica</b>  ·  control room\n"
            "<tg-emoji emoji-id=5870772616305839506>👥</tg-emoji> "
            "<b>.help</b>  ·  commands and modules\n"
            "<tg-emoji emoji-id=5931472654660800739>📡</tg-emoji> "
            "<b>.ping</b>  ·  Telegram round-trip time"
        ),
    }

    async def client_ready(self):
        def welcome_text():
            text = self.strings["exotica_welcome"].format(
                utils.get_platform_emoji() if self.client.heroku_me.premium else ""
            )
            return resolve_custom_emoji(
                text, premium=bool(self.client.heroku_me.premium)
            )

        self.text = welcome_text

        try:
            content_channel = None
            existing_channel_id = self.db.get("heroku.forums", "channel_id", None)

            if existing_channel_id:
                try:
                    content_channel = await self.client.get_entity(existing_channel_id)
                    logger.debug(
                        f"Found existing content channel with ID {existing_channel_id}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Saved channel ID {existing_channel_id} not found or inaccessible: {e}"
                    )
                    content_channel = None
                    self.db.set("heroku.forums", "forums_cache", {"heroku-userbot": {}})

            if not content_channel:
                async for dialog in self.client.iter_dialogs():
                    if dialog.title and dialog.title.lower() in {"exotica-userbot", "heroku-userbot"}:
                        content_channel = dialog.entity
                        logger.debug(
                            f"Found existing channel '{dialog.title}' with ID {dialog.entity.id}"
                        )
                        self.db.set(
                            "heroku.forums", "channel_id", int(dialog.entity.id)
                        )
                        break

            if not content_channel:
                content_channel = await self.db.ensure_content_channel()

            if not content_channel:
                raise RuntimeError("Failed to get or create content channel!")

            forum_entity = None
            existing_forum_id = self.db.get("heroku.forums", "forum_id", None)

            if existing_forum_id:
                try:
                    forum_entity = await self.client.get_entity(existing_forum_id)
                except Exception:
                    forum_entity = None

            if not forum_entity:
                try:
                    if not (
                        hasattr(content_channel, "forum") or not content_channel.forum
                    ):
                        from herokutl.tl.functions.channels import ToggleForumRequest

                        try:
                            await self.client(
                                ToggleForumRequest(
                                    channel=content_channel,
                                    enabled=True,
                                )
                            )
                        except Exception as e:
                            logger.debug(
                                f"Channel might already be a forum or conversion failed: {e}"
                            )

                    forum_entity = content_channel
                    self.db.set("heroku.forums", "forum_id", int(content_channel.id))
                except Exception:
                    forum_entity = content_channel

            required_topics = [
                (
                    "Assets",
                    "🌆 Your Exotica assets will be stored here",
                    5877307202888273539,
                ),
                (
                    "Backups",
                    "💾 Your Exotica backups will be stored here",
                    5877307202888273539,
                ),
            ]

            for topic_title, topic_desc, emoji_id in required_topics:
                try:
                    await utils.asset_forum_topic(
                        client=self.client,
                        db=self.db,
                        peer=forum_entity.id if forum_entity else content_channel.id,
                        title=topic_title,
                        description=topic_desc,
                        icon_emoji_id=emoji_id,
                    )
                    logger.debug(f"Created or verified topic '{topic_title}'")
                except Exception:
                    logger.exception(f"Failed to create/verify topic '{topic_title}'")

            await utils.invite_inline_bot(self.client, content_channel)

        except Exception:
            logger.exception(
                "Can't find and/or create content channel\n"
                "This may cause several consequences, such as:\n"
                "- Non working inline-logs, backups, assets features\n"
                "- This error will occur every restart\n\n"
                "You can try solving this by leaving some channels/groups"
            )

        self.mark = lambda: utils.chunks(
            [
                {
                    "text": self.strings.get("language", lang),
                    "data": f"heroku/lang/{lang}",
                }
                for lang in translations.SUPPORTED_LANGUAGES
            ],
            3,
        )

    async def inline_ready(self):
        if self.get("no_msg"):
            return

        await self.inline.bot.send_message(
            self._client.tg_id,
            self.text(),
            reply_markup=self.inline.generate_markup(self.mark()),
            disable_web_page_preview=True,
        )

        self.set("no_msg", True)

    @loader.callback_handler()
    async def lang(self, call: BotInlineCall):
        if not call.data.startswith("heroku/lang/"):
            return

        lang = call.data.split("/")[2]

        self._db.set(translations.__name__, "lang", lang)
        await self.allmodules.reload_translations()

        await self.inline.bot(call.answer(self.strings["language_saved"]))
        await call.edit(text=self.text(), reply_markup=self.mark())
