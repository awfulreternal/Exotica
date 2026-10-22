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
import herokutl

from herokutl.errors import WebpageMediaEmptyError
from herokutl.types import InputMediaWebPage
from herokutl.tl.types import Message
from herokutl.utils import get_display_name
from .. import loader, utils, version
import platform as lib_platform
import getpass
import re
from exotica.host_info import get_host_profile
from exotica.latency import measure_telegram_rtt

logger = logging.getLogger(__name__)


@loader.tds
class HerokuInfoMod(loader.Module):
    """Show userbot info"""

    strings = {
        "name": "ExoticaInfo",
        "exotica_info_message": (
            "<tg-emoji emoji-id=5393588431026674882>🪐</tg-emoji> "
            "<b>EXOTICA · SYSTEM INFO</b>\n"
            "<blockquote>👤 <b>Owner</b> · {me}\n🤖 <b>Version</b> · {version}\n"
            "⌨️ <b>Prefix</b> · {prefix}\n🔄 <b>Uptime</b> · {uptime}</blockquote>\n"
            "<blockquote>⚡ <b>Host CPU</b> · {host_cpu}\n🛡 <b>Host RAM</b> · {host_memory}\n"
            "📡 <b>Telegram RTT</b> · {ping} ms</blockquote>\n"
            "<blockquote>☁️ <b>Provider</b> · {platform}\n🧾 <b>Cloud tier</b> · {cloud_tier}\n"
            "🖥 <b>OS</b> · {os}\n🐍 <b>Python</b> · {python_ver}</blockquote>"
        ),
        "exotica_rich_info_message": (
            "<h1><tg-emoji emoji-id=5393588431026674882>🪐</tg-emoji> EXOTICA</h1>"
            "<details><summary>Overview</summary><table>"
            "<tr><th>System</th><th>Measured value</th></tr>"
            "<tr><td>Owner</td><td>{me}</td></tr><tr><td>Version</td><td>{version}</td></tr>"
            "<tr><td>Uptime</td><td>{uptime}</td></tr><tr><td>Telegram RTT</td><td>{ping} ms</td></tr>"
            "</table></details><details><summary>Host</summary><table>"
            "<tr><th>Resource</th><th>Detected</th></tr><tr><td>Provider</td><td>{platform}</td></tr>"
            "<tr><td>CPU quota</td><td>{host_cpu}</td></tr><tr><td>RAM</td><td>{host_memory}</td></tr>"
            "<tr><td>Cloud tier</td><td>{cloud_tier}</td></tr><tr><td>OS</td><td>{os}</td></tr>"
            "<tr><td>Python</td><td>{python_ver}</td></tr></table></details>"
        ),
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "custom_message",
                doc=lambda: (
                    self.strings["_cfg_cst_msg"]
                    + "\n"
                    + (
                        "\n"
                        + self.strings["_cfg_cst_ph"].format(
                            "\n" + utils.config_placeholders()
                        )
                        if utils.config_placeholders()
                        else ""
                    )
                ),
            ),
            loader.ConfigValue(
                "banner_url",
                None,
                lambda: self.strings["_cfg_banner"],
                validator=loader.validators.RandomLink(),
            ),
            loader.ConfigValue(
                "ping_emoji",
                "🪐",
                lambda: self.strings["ping_emoji"],
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "quote_media",
                False,
                lambda: self.strings["_cfg_quote_media"],
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "invert_media",
                False,
                lambda: self.strings["_cfg_invert_media"],
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "rich_mode",
                False,
                lambda: self.strings["_cfg_rich_mode"],
                validator=loader.validators.Boolean(),
            ),
        )

    def _get_cpu_info(self) -> str | None:
        try:
            import psutil

            return f"{psutil.cpu_count(logical=False)} ({psutil.cpu_count()}) core(-s); {psutil.cpu_percent()}% total"
        except PermissionError:
            return None
        except Exception:
            logger.exception("Unsupported placeholder")
            return None

    def _get_cpu_usage(self) -> str:
        try:
            import psutil

            return f"{psutil.cpu_percent(interval=None):.2f}"
        except PermissionError:
            return ""
        except Exception:
            logger.exception("Unsupported placeholder")
            return ""

    def _get_os_name(self):
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME"):
                        return line.split("=")[1].strip().strip('"')
        except FileNotFoundError:
            return self.strings["non_detectable"]

    def _get_ram_usage(self):
        import psutil

        process = psutil.Process()
        memory = process.memory_info().rss
        for child in process.children(recursive=True):
            try:
                memory += child.memory_info().rss
            except psutil.NoSuchProcess:
                continue
        return f"{round(memory / 2**20, 1)} MB"

    def _get_update_status(self):
        try:
            up_to_date = utils.is_up_to_date()
            if up_to_date:
                upd = self.strings["up-to-date"]
            else:
                upd = self.strings["update_required"].format(prefix=self.get_prefix())
        except Exception:
            upd = ""

        return upd

    def _get_platform_emoji(self):
        platform_emoji = utils.get_named_platform_emoji()

        for emoji, icon in [
            ("🍊", '<tg-emoji emoji-id="5449599833973203438">🧡</tg-emoji>'),
            ("🍇", '<tg-emoji emoji-id="5449468596952507859">💜</tg-emoji>'),
            ("😶‍🌫️", '<tg-emoji emoji-id="5370547013815376328">😶‍🌫️</tg-emoji>'),
            ("❓", '<tg-emoji emoji-id="5407025283456835913">📱</tg-emoji>'),
            ("🍀", '<tg-emoji emoji-id="5395325195542078574">🍀</tg-emoji>'),
            ("🦾", '<tg-emoji emoji-id="5386766919154016047">🦾</tg-emoji>'),
            ("🚂", '<tg-emoji emoji-id="5359595190807962128">🚂</tg-emoji>'),
            ("🐳", '<tg-emoji emoji-id="5431815452437257407">🐳</tg-emoji>'),
            ("🕶", '<tg-emoji emoji-id="5407025283456835913">📱</tg-emoji>'),
            ("🐈‍⬛", '<tg-emoji emoji-id="6334750507294262724">🐈‍⬛</tg-emoji>'),
            ("✌️", '<tg-emoji emoji-id="5469986291380657759">✌️</tg-emoji>'),
            ("💎", '<tg-emoji emoji-id="5471952986970267163">💎</tg-emoji>'),
            ("🛡", '<tg-emoji emoji-id="5282731554135615450">🌩</tg-emoji>'),
            ("🌼", '<tg-emoji emoji-id="5224219153077914783">❤️</tg-emoji>'),
            ("🎡", '<tg-emoji emoji-id="5226711870492126219">🎡</tg-emoji>'),
            ("🐧", '<tg-emoji emoji-id="5361541227604878624">🐧</tg-emoji>'),
            ("🧃", '<tg-emoji emoji-id="5422884965593397853">🧃</tg-emoji>'),
            ("🦅", '<tg-emoji emoji-id="5427286516797831670">🦅</tg-emoji>'),
            ("💻", '<tg-emoji emoji-id="5469825590884310445">💻</tg-emoji>'),
            ("🍏", '<tg-emoji emoji-id="5372908412604525258">🍏</tg-emoji>'),
        ]:
            platform_emoji = platform_emoji.replace(emoji, icon)
        return platform_emoji

    def _get_placeholder_providers(self, template_key):
        host_profile = None

        def get_profile():
            nonlocal host_profile
            if host_profile is None:
                host_profile = get_host_profile()
            return host_profile

        def host_summary():
            profile = get_profile()
            parts = []
            if profile.lavhost:
                parts.append("lavHost")
            parts.append(profile.provider)
            if profile.memory_gb is not None:
                parts.append(f"{profile.memory_gb:g} GB RAM")
            return utils.escape_html(" · ".join(parts))

        return {
            "banner_url": lambda: self.config["banner_url"],
            "me": lambda: (
                '<b><a href="tg://user?id={}">{}</a></b>'.format(
                    self._client.heroku_me.id,
                    utils.escape_html(get_display_name(self._client.heroku_me)),
                ).replace("{", "").replace("}", "")
            ),
            "version": lambda: f'<i>{".".join(map(str, version.__version__))}</i>',
            "build": utils.get_commit_url,
            "prefix": lambda: f"«<code>{utils.escape_html(self.get_prefix())}</code>»",
            "platform": host_summary,
            "host_cpu": lambda: (
                f"{get_profile().cpu_cores:g} cores"
                if get_profile().cpu_cores is not None
                else self.strings["non_detectable"]
            ),
            "host_memory": lambda: (
                f"{get_profile().memory_gb:g} GB"
                if get_profile().memory_gb is not None
                else self.strings["non_detectable"]
            ),
            "cloud_tier": lambda: utils.escape_html(get_profile().tier),
            "platform_emoji": self._get_platform_emoji,
            "upd": self._get_update_status,
            "python_ver": lib_platform.python_version,
            "uptime": utils.formatted_uptime,
            "cpu_usage": self._get_cpu_usage,
            "ram_usage": self._get_ram_usage,
            "branch": lambda: version.branch,
            "hostname": lib_platform.node,
            "user": getpass.getuser,
            "os": self._get_os_name,
            "kernel": lib_platform.release,
            "htl_ver": lambda: herokutl.__version__,
            "git_status": utils.get_git_status,
            "cpu": self._get_cpu_info,
            "img": lambda: (
                f'<img src="{utils.escape_html(str(self.config["banner_url"]))}"/>'
                if template_key == "rich_info_message" and self.config["banner_url"]
                else ""
            ),
        }

    def _format_custom_message(self, template, data):
        def replace(match):
            name = match.group(1)
            if name in data:
                return str(data[name])
            return self.strings["missing_placeholder"].format(
                placeholder=utils.escape_html(match.group(0))
            )

        return re.sub(r"{(\w+)}", replace, template)

    async def _render_info(
        self,
        start: float,
        template_key: str = "info_message",
    ) -> str:
        custom_message = self.config["custom_message"]
        exotica_template = {
            "info_message": "exotica_info_message",
            "rich_info_message": "exotica_rich_info_message",
        }.get(template_key, template_key)
        template = custom_message or self.strings.get(
            exotica_template,
            self.strings[template_key],
        )
        required = set(re.findall(r"{(\w+)}", template))
        providers = self._get_placeholder_providers(template_key)
        data = utils.LazyPlaceholderData(providers)
        for name in required & providers.keys():
            data[name]

        if "ping" in required:
            data["ping"] = await measure_telegram_rtt(self._client)
        if custom_message:
            data = await utils.get_placeholders(data, custom_message)
            return self._format_custom_message(custom_message, data)
        return template.format(
            (
                utils.get_platform_emoji()
                if "{}" in template
                and self._client.heroku_me.premium
                and self.config.get("show_heroku", False)
                else ""
            ),
            **data,
        )

    @loader.command()
    async def infocmd(self, message: Message):
        if self.config["rich_mode"]:
            await utils.answer_with_media_fallback(
                message,
                rich_message=await self._render_info(template_key="rich_info_message"),
                reply_to=getattr(message, "reply_to_msg_id", None),
            )
            return

        media = str(self.config["banner_url"])

        if self.config["banner_url"] and self.config["quote_media"] is True:
            media = InputMediaWebPage(str(self.config["banner_url"]), optional=True)

        elif not self.config["banner_url"]:
            media = None

        try:
            await utils.answer_with_media_fallback(
                message,
                await self._render_info(),
                file=media,
                reply_to=getattr(message, "reply_to_msg_id", None),
                invert_media=self.config["invert_media"],
            )
        except WebpageMediaEmptyError:
            await utils.answer(
                message,
                self.strings["no_banner"].format(
                    link=self.config["banner_url"],
                ),
                reply_to=getattr(message, "reply_to_msg_id", None),
            )

    @loader.command()
    async def ubinfo(self, message: Message):
        await utils.answer(message, self.strings["desc"])
