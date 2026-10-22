"""Exotica-branded inline dashboard and low-overhead diagnostics."""

from __future__ import annotations

import html

from herokutl.tl.custom import Message

from exotica.host_info import get_host_profile
from exotica.latency import measure_telegram_rtt
from exotica.telegram_ui import telegram_emoji

from .. import loader, utils
from ..inline.types import InlineCall

_EMOJI_IDS = {
    "brand": (5393588431026674882, "🪐"),
    "info": (5870609858520158157, "ℹ️"),
    "users": (5870772616305839506, "👥"),
    "lavhost": (5469986291380657759, "✌️"),
}


@loader.tds
class ExoticaMod(loader.Module):
    """Exotica control room, host information, and Telegram latency."""

    strings = {"name": "Exotica"}
    strings_ru = {
        "name": "Exotica",
        "home": "<b>EXOTICA</b>  /  <code>control room</code>\n\n{icon} <b>Статус</b>  ·  {status}\n{info} <b>Узел</b>  ·  {host}\n{users} <b>Модули</b>  ·  {modules}\n\nВыбери раздел.",
        "status": "<b>EXOTICA</b>  /  <b>СТАТУС</b>\n\n{icon} Аккаунт  ·  <code>{account}</code>\n{info} Uptime  ·  <code>{uptime}</code>\n{users} Модули  ·  <code>{modules}</code>",
        "host": "<b>EXOTICA</b>  /  <b>ИНФОРМАЦИЯ О ХОСТЕ</b>\n\n{icon} Провайдер  ·  <code>{provider}</code>\n{info} CPU  ·  <code>{cpu}</code>\nRAM  ·  <code>{memory}</code>\nTier  ·  <code>{tier}</code>\nlavHost  ·  <code>{lavhost}</code>{note}",
        "oracle_note": "\n\n<blockquote>На официальной странице OCI Always Free A1 указан эквивалент 2 OCPU / 12 GB при постоянном использовании. 24 GB отображаются как обнаруженная конфигурация; бесплатный tier не подтверждён.</blockquote>",
        "ping": "<b>EXOTICA</b>  /  <b>TELEGRAM RTT</b>\n\n{icon} Один лёгкий Telegram state-запрос  ·  <code>{latency} ms</code>",
        "module_list": "<b>EXOTICA</b>  /  <b>МОДУЛИ</b>\n\n{users} Загружено  ·  <code>{count}</code>\n\n{items}",
        "empty_modules": "Встроенные модули активны; дополнительных модулей нет.",
        "ping_error": "Не удалось измерить Telegram RTT. Проверь соединение и локальные логи.",
        "home_button": "⌂ Обзор",
        "status_button": "◉ Статус",
        "host_button": "▣ Хост",
        "ping_button": "⌁ Ping",
        "modules_button": "▤ Модули",
        "back_button": "‹ Назад",
        "close_button": "Закрыть",
        "connected": "в сети",
        "disconnected": "нет соединения",
        "lavhost_yes": "обнаружен",
        "lavhost_no": "не обнаружен",
        "ram_unknown": "не определена",
        "tier_unknown": "не подтверждён",
    }
    strings_en = {
        "name": "Exotica",
        "home": "<b>EXOTICA</b>  /  <code>control room</code>\n\n{icon} <b>Status</b>  ·  {status}\n{info} <b>Node</b>  ·  {host}\n{users} <b>Modules</b>  ·  {modules}\n\nChoose a section.",
        "status": "<b>EXOTICA</b>  /  <b>STATUS</b>\n\n{icon} Account  ·  <code>{account}</code>\n{info} Uptime  ·  <code>{uptime}</code>\n{users} Modules  ·  <code>{modules}</code>",
        "host": "<b>EXOTICA</b>  /  <b>HOST INFORMATION</b>\n\n{icon} Provider  ·  <code>{provider}</code>\n{info} CPU  ·  <code>{cpu}</code>\nRAM  ·  <code>{memory}</code>\nTier  ·  <code>{tier}</code>\nLavHost  ·  <code>{lavhost}</code>{note}",
        "oracle_note": "\n\n<blockquote>OCI's official Always Free A1 allocation is equivalent to 2 OCPU / 12 GB when used continuously. 24 GB is shown as detected capacity; Free Tier status is not verified.</blockquote>",
        "ping": "<b>EXOTICA</b>  /  <b>TELEGRAM RTT</b>\n\n{icon} One lightweight Telegram state request  ·  <code>{latency} ms</code>",
        "module_list": "<b>EXOTICA</b>  /  <b>MODULES</b>\n\n{users} Loaded  ·  <code>{count}</code>\n\n{items}",
        "empty_modules": "Built-in modules are active; no additional modules are loaded.",
        "ping_error": "Telegram RTT could not be measured. Check connectivity and local logs.",
        "home_button": "⌂ Overview",
        "status_button": "◉ Status",
        "host_button": "▣ Host",
        "ping_button": "⌁ Ping",
        "modules_button": "▤ Modules",
        "back_button": "‹ Back",
        "close_button": "Close",
        "connected": "online",
        "disconnected": "offline",
        "lavhost_yes": "detected",
        "lavhost_no": "not detected",
        "ram_unknown": "unknown",
        "tier_unknown": "not verified",
    }

    def _labels(self):
        return self.strings_ru if self._db.get("heroku.translations", "lang") == "ru" else self.strings_en

    def _emoji(self, name):
        emoji_id, fallback = _EMOJI_IDS[name]
        return telegram_emoji(
            emoji_id,
            fallback,
            premium=bool(getattr(self._client.heroku_me, "premium", False)),
        )

    def _buttons(self, labels, *, home=False):
        if home:
            return [
                [
                    {"text": labels["status_button"], "callback": self._show_status},
                    {"text": labels["host_button"], "callback": self._show_host},
                ],
                [
                    {"text": labels["ping_button"], "callback": self._show_ping},
                    {"text": labels["modules_button"], "callback": self._show_modules},
                ],
                [{"text": labels["close_button"], "action": "close"}],
            ]
        return [[{"text": labels["back_button"], "callback": self._show_home}]]

    def _home_text(self, labels):
        connected = self._client.is_connected()
        host = get_host_profile()
        return labels["home"].format(
            icon=self._emoji("brand"),
            info=self._emoji("info"),
            users=self._emoji("users"),
            status=labels["connected"] if connected else labels["disconnected"],
            host=html.escape(host.provider),
            modules=len(self.allmodules.modules),
        )

    @loader.command()
    async def exotica(self, message: Message):
        """Open the Exotica inline control room."""
        labels = self._labels()
        await self.inline.form(
            self._home_text(labels),
            message=message,
            reply_markup=self._buttons(labels, home=True),
            force_me=True,
            silent=True,
        )

    @loader.command()
    async def ping(self, message: Message):
        """Measure Telegram RTT with one lightweight RPC."""
        labels = self._labels()
        try:
            latency = await measure_telegram_rtt(self._client)
        except Exception:
            await utils.answer(message, labels["ping_error"])
            return
        await utils.answer(
            message,
            labels["ping"].format(icon=self._emoji("brand"), latency=f"{latency:.1f}"),
        )

    async def _show_home(self, call: InlineCall):
        labels = self._labels()
        await call.edit(self._home_text(labels), reply_markup=self._buttons(labels, home=True))

    async def _show_status(self, call: InlineCall):
        labels = self._labels()
        account = getattr(self._client.heroku_me, "username", None) or self._client.tg_id
        await call.edit(
            labels["status"].format(
                icon=self._emoji("brand"),
                info=self._emoji("info"),
                users=self._emoji("users"),
                account=html.escape(str(account)),
                uptime=html.escape(utils.formatted_uptime()),
                modules=len(self.allmodules.modules),
            ),
            reply_markup=self._buttons(labels),
        )

    async def _show_host(self, call: InlineCall):
        labels = self._labels()
        profile = get_host_profile()
        tier = profile.tier if profile.tier != "Not verified" else labels["tier_unknown"]
        memory = f"{profile.memory_gb:g} GB" if profile.memory_gb is not None else labels["ram_unknown"]
        cpu = f"{profile.cpu_cores:g} cores" if profile.cpu_cores is not None else labels["ram_unknown"]
        note = ""
        if profile.provider == "Oracle Cloud" and profile.memory_gb and profile.memory_gb >= 24 and profile.tier == "Not verified":
            note = labels["oracle_note"]
        await call.edit(
            labels["host"].format(
                icon=self._emoji("lavhost" if profile.lavhost else "brand"),
                info=self._emoji("info"),
                provider=html.escape(profile.provider),
                cpu=html.escape(cpu),
                memory=html.escape(memory),
                tier=html.escape(tier),
                lavhost=labels["lavhost_yes"] if profile.lavhost else labels["lavhost_no"],
                note=note,
            ),
            reply_markup=self._buttons(labels),
        )

    async def _show_ping(self, call: InlineCall):
        labels = self._labels()
        try:
            latency = await measure_telegram_rtt(self._client)
            text = labels["ping"].format(icon=self._emoji("brand"), latency=f"{latency:.1f}")
        except Exception:
            text = labels["ping_error"]
        await call.edit(text, reply_markup=self._buttons(labels))

    async def _show_modules(self, call: InlineCall):
        labels = self._labels()
        extra = [
            html.escape(getattr(module, "name", module.__class__.__name__))
            for module in self.allmodules.modules
            if module.__class__.__module__ != "heroku.modules.exotica"
        ][:12]
        items = "\n".join(f"• {name}" for name in extra) or labels["empty_modules"]
        await call.edit(
            labels["module_list"].format(icon=self._emoji("brand"), users=self._emoji("users"), count=len(self.allmodules.modules), items=items),
            reply_markup=self._buttons(labels),
        )
