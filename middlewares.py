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

        return await handler(event, data)


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

        window = _recent_messages[key]
        window.append(now)
        while window and now - window[0] > settings.flood_time_window_sec:
            window.popleft()

        if len(window) > settings.flood_message_limit:
            window.clear()
            _flood_muted_until[key] = now + _FLOOD_MUTE_SECONDS
            mention = mention_html(user.id, user.full_name)
            try:
                await bot.restrict_chat_member(
                    event.chat.id,
                    user.id,
                    permissions=ChatPermissions(can_send_messages=False),
                    until_date=int(now) + _FLOOD_MUTE_SECONDS,
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
                    duration="10 daqiqa",
                )
                await event.answer(texts.FLOOD_MUTED.format(mention=mention))
            except Exception:
                pass
            return  # flood qilingan xabarni boshqa handlerlarga yubormaymiz

        return await handler(event, data)
