"""
ACHI BOT - middleware'lar.

`EnsureChatMiddleware` har bir guruh xabari kelganda shu guruhni
`chat_settings` jadvalida "bor" deb belgilaydi (yo'q bo'lsa yaratadi,
bor bo'lsa nomini yangilaydi). Shu orqali admin hech qanday sozlash
buyrug'ini yozmagan bo'lsa ham, guruh avtomatik ravishda har soatlik
hisobot ro'yxatiga (report_enabled standart holatda yoqilgan) tushadi.

`FloodMiddleware` esa har bir foydalanuvchining xabar yozish tezligini
kuzatib boradi: agar sozlangan vaqt oralig'ida (config.flood_time_window_sec)
sozlangan sondan (config.flood_message_limit) ko'p xabar yozsa, avtomatik
10 daqiqaga mute qiladi. Bu middleware xabarni handlerlarga yuborishni
to'xtatmaydi (faqat kuzatuv va jazo, keyin oqim davom etadi) - shu bilan
admin buyruqlari va boshqa handlerlar bilan ziddiyat bo'lmaydi.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import ChatPermissions, Message, TelegramObject, Update

import texts
from config import settings
from database import db
from utils import is_chat_admin, mention_html

_known_chats: set[int] = set()

# Telegram Bot API'da "guruhdagi barcha a'zolarni olish" degan tayyor
# metod yo'q, shu sabab @admin/@admins ping va /tag funksiyalari uchun
# har bir xabar yozgan odamni "known_members" jadvaliga yozib boramiz.
# Har xabarda DB'ga yozmaslik uchun (keraksiz yuklama bo'lmasin), bitta
# odamni har 5 daqiqada faqat bir marta yangilaymiz.
_MEMBER_TRACK_INTERVAL_SEC = 5 * 60
_member_last_tracked: dict[tuple[int, int], float] = {}


class EnsureChatMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        chat = None
        if isinstance(event, Update):
            inner = event.event
            chat = getattr(inner, "chat", None)
        else:
            chat = getattr(event, "chat", None)

        if chat is not None and chat.type in ("group", "supergroup") and chat.id not in _known_chats:
            try:
                await db.ensure_chat(chat.id, chat.title)
            except Exception:
                pass
            _known_chats.add(chat.id)

        await self._track_member(event, chat)
        await self._track_message_count(event, chat)

        return await handler(event, data)

    async def _track_member(self, event: TelegramObject, chat) -> None:
        if chat is None or chat.type not in ("group", "supergroup"):
            return

        inner = event.event if isinstance(event, Update) else event
        user = getattr(inner, "from_user", None)
        if user is None or user.is_bot:
            return

        key = (chat.id, user.id)
        now = time.time()
        last = _member_last_tracked.get(key)
        if last and now - last < _MEMBER_TRACK_INTERVAL_SEC:
            return

        try:
            await db.upsert_known_member(chat.id, user.id, user.full_name, user.username)
        except Exception:
            pass
        _member_last_tracked[key] = now

    async def _track_message_count(self, event: TelegramObject, chat) -> None:
        """
        /top buyrug'i (eng faol a'zolar reytingi) uchun - HAR bir
        xabarda +1 qilamiz (yuqoridagi `_track_member`dan farqli, u
        5 daqiqada bir marta ism/username yangilaydi, xabar sonini
        emas). Foydalanuvchi avval `known_members`da bo'lishi kerak
        (upsert_known_member orqali) - shu sabab bu funksiya
        `_track_member`dan KEYIN chaqiriladi.
        """
        if chat is None or chat.type not in ("group", "supergroup"):
            return
        inner = event.event if isinstance(event, Update) else event
        if not isinstance(inner, Message) or not inner.text:
            return
        user = getattr(inner, "from_user", None)
        if user is None or user.is_bot:
            return
        try:
            await db.increment_message_count(chat.id, user.id)
        except Exception:
            pass


_FLOOD_MUTE_SECONDS = 10 * 60
_recent_messages: dict[tuple[int, int], deque[float]] = defaultdict(deque)
_flood_muted_until: dict[tuple[int, int], float] = {}


class FloodMiddleware(BaseMiddleware):
    """Faqat guruh xabarlari (Message update) uchun ishlaydi."""

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        bot = data.get("bot")
        user = event.from_user
        if (
            bot is None
            or user is None
            or user.is_bot
            or event.chat.type not in ("group", "supergroup")
        ):
            return await handler(event, data)

        key = (event.chat.id, user.id)
        now = time.time()

        # Agar hozirgina flood uchun mute qilingan bo'lsa, qayta-qayta
        # ogohlantirish yubormaslik uchun shu oynani tekshiramiz.
        muted_until = _flood_muted_until.get(key)
        if muted_until and now < muted_until:
            return await handler(event, data)

        if await is_chat_admin(bot, event.chat.id, user.id):
            return await handler(event, data)

        # VIP a'zolar (premium funksiya - /vip orqali qo'shiladi) flood
        # cheklovidan ozod - masalan guruh homiylari/hurmatli mehmonlar.
        try:
            if await db.is_vip(event.chat.id, user.id):
                return await handler(event, data)
        except Exception:
            pass

        # Premium: /floodlimit orqali guruhga xos chegara o'rnatilgan
        # bo'lsa, global standart o'rniga o'shani ishlatamiz.
        flood_limit = settings.flood_message_limit
        flood_window = settings.flood_time_window_sec
        try:
            chat_row = await db.get_chat_settings(event.chat.id)
            if chat_row and chat_row["flood_limit_override"] and chat_row["flood_window_override"]:
                flood_limit = chat_row["flood_limit_override"]
                flood_window = chat_row["flood_window_override"]
        except Exception:
            pass

        window = _recent_messages[key]
        window.append(now)
        while window and now - window[0] > flood_window:
            window.popleft()

        if len(window) > flood_limit:
            window.clear()

            # /setfloodmode orqali o'rnatilgan amal (standart: "mute") -
            # GroupHelpBot'dagi FloodService::getAction() mantig'iga mos:
            # warn/mute/tmute/kick/ban/tban.
            flood_action = "mute"
            try:
                if chat_row and chat_row["flood_action"]:
                    flood_action = chat_row["flood_action"]
            except Exception:
                pass

            mention = mention_html(user.id, user.full_name)
            # "warn" bundan mustasno - u odamni cheklamaydi, shu sabab
            # keyingi flood tekshiruvi darrov yana ishlayversin (mute
            # cooldown'ini o'rnatmaymiz).
            if flood_action != "warn":
                _flood_muted_until[key] = now + _FLOOD_MUTE_SECONDS

            try:
                if flood_action == "warn":
                    await event.answer(texts.FLOOD_WARNING.format(mention=mention))

                elif flood_action == "tmute":
                    await bot.restrict_chat_member(
                        event.chat.id,
                        user.id,
                        permissions=ChatPermissions(can_send_messages=False),
                        until_date=int(now) + _FLOOD_MUTE_SECONDS,
                    )
                    await db.log_action(
                        chat_id=event.chat.id,
                        chat_title=event.chat.title,
                        action="tmute",
                        target_id=user.id,
                        target_name=user.full_name,
                        target_username=user.username,
                        admin_id=0,
                        admin_name="ACHI BOT (anti-flood)",
                        reason="Flood - juda tez-tez xabar yozdi",
                        duration="10 daqiqa",
                    )
                    await event.answer(texts.FLOOD_MUTED.format(mention=mention))

                elif flood_action == "mute":
                    await bot.restrict_chat_member(
                        event.chat.id,
                        user.id,
                        permissions=ChatPermissions(can_send_messages=False),
                    )
                    await db.log_action(
                        chat_id=event.chat.id,
                        chat_title=event.chat.title,
                        action="mute",
                        target_id=user.id,
                        target_name=user.full_name,
                        target_username=user.username,
                        admin_id=0,
                        admin_name="ACHI BOT (anti-flood)",
                        reason="Flood - juda tez-tez xabar yozdi",
                        duration=None,
                    )
                    await event.answer(texts.FLOOD_MUTED_PERMANENT.format(mention=mention))

                elif flood_action == "kick":
                    await bot.ban_chat_member(event.chat.id, user.id)
                    await bot.unban_chat_member(event.chat.id, user.id, only_if_banned=True)
                    await db.log_action(
                        chat_id=event.chat.id,
                        chat_title=event.chat.title,
                        action="kick",
                        target_id=user.id,
                        target_name=user.full_name,
                        target_username=user.username,
                        admin_id=0,
                        admin_name="ACHI BOT (anti-flood)",
                        reason="Flood - juda tez-tez xabar yozdi",
                    )
                    await event.answer(texts.FLOOD_KICKED.format(mention=mention))

                elif flood_action == "tban":
                    await bot.ban_chat_member(
                        event.chat.id, user.id, until_date=int(now) + _FLOOD_MUTE_SECONDS
                    )
                    await db.log_action(
                        chat_id=event.chat.id,
                        chat_title=event.chat.title,
                        action="tban",
                        target_id=user.id,
                        target_name=user.full_name,
                        target_username=user.username,
                        admin_id=0,
                        admin_name="ACHI BOT (anti-flood)",
                        reason="Flood - juda tez-tez xabar yozdi",
                        duration="10 daqiqa",
                    )
                    await event.answer(
                        texts.FLOOD_TBANNED.format(mention=mention, duration="10 daqiqa")
                    )

                elif flood_action == "ban":
                    await bot.ban_chat_member(event.chat.id, user.id)
                    await db.log_action(
                        chat_id=event.chat.id,
                        chat_title=event.chat.title,
                        action="ban",
                        target_id=user.id,
                        target_name=user.full_name,
                        target_username=user.username,
                        admin_id=0,
                        admin_name="ACHI BOT (anti-flood)",
                        reason="Flood - juda tez-tez xabar yozdi",
                    )
                    await event.answer(texts.FLOOD_BANNED.format(mention=mention))

                else:
                    # Noma'lum qiymat bo'lib qolsa (masalan eski ma'lumot)
                    # - xavfsiz standart: mute.
                    await bot.restrict_chat_member(
                        event.chat.id,
                        user.id,
                        permissions=ChatPermissions(can_send_messages=False),
                        until_date=int(now) + _FLOOD_MUTE_SECONDS,
                    )
                    await event.answer(texts.FLOOD_MUTED.format(mention=mention))
            except Exception:
                pass
            return  # flood qilingan xabarni boshqa handlerlarga yubormaymiz

        return await handler(event, data)
