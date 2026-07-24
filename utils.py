"""
ACHI BOT - umumiy yordamchi funksiyalar: admin tekshiruvi, target aniqlash,
vaqt oralig'ini parse qilish, mention yasash va h.k.
"""
from __future__ import annotations

import re
from datetime import timedelta

from aiogram import Bot
from aiogram.types import Chat, ChatMemberAdministrator, ChatMemberOwner, Message, User

from config import is_super_admin

_DURATION_RE = re.compile(r"^(\d+)\s*([mhdw])$", re.IGNORECASE)
_UNIT_SECONDS = {
    "m": 60,
    "h": 60 * 60,
    "d": 60 * 60 * 24,
    "w": 60 * 60 * 24 * 7,
}


def parse_duration(text: str) -> timedelta | None:
    """"1d", "2h", "30m", "1w" kabi yozuvlarni timedelta'ga aylantiradi."""
    match = _DURATION_RE.match(text.strip())
    if not match:
        return None
    amount, unit = match.groups()
    seconds = int(amount) * _UNIT_SECONDS[unit.lower()]
    return timedelta(seconds=seconds)


def mention_html(user_id: int, name: str) -> str:
    safe_name = name.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f'<a href="tg://user?id={user_id}">{safe_name}</a>'


def user_display_name(user: User) -> str:
    if user.username:
        return f"@{user.username}"
    return user.full_name


async def is_chat_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    if is_super_admin(user_id):
        return True
    try:
        member = await bot.get_chat_member(chat_id, user_id)
    except Exception:
        return False
    return isinstance(member, (ChatMemberAdministrator, ChatMemberOwner))


async def is_target_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
    except Exception:
        return False
    return isinstance(member, (ChatMemberAdministrator, ChatMemberOwner))


async def resolve_target_user(message: Message, bot: Bot) -> User | None:
    """
    Nishonni aniqlaydi: avval reply qilingan xabar egasi, keyin
    entity (text_mention) orqali. @username orqali user obyektini
    olish uchun Bot API imkoni cheklangan, shu uchun reply/entity
    ustuvor qilingan.
    """
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user

    if message.entities:
        for entity in message.entities:
            if entity.type == "text_mention" and entity.user:
                return entity.user
    return None

