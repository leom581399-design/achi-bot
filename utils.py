"""
ACHI BOT - umumiy yordamchi funksiyalar: admin tekshiruvi, target aniqlash,
vaqt oralig'ini parse qilish, mention yasash va h.k.
"""
from __future__ import annotations

import re
import time
from datetime import datetime, timedelta, timezone

from aiogram import Bot
from aiogram.types import Chat, ChatMemberAdministrator, ChatMemberOwner, Message, User

from config import is_super_admin

# O'zbekiston vaqt zonasi - UTC+5, yil davomida o'zgarmaydi (DST yo'q).
# Railway/serverlar odatda UTC vaqtida ishlaydi, shu sabab barcha
# foydalanuvchiga ko'rsatiladigan sana/vaqtlarni shu zona bilan
# hisoblash MUHIM - aks holda "soat hato" bo'lib chiqadi.
TASHKENT_TZ = timezone(timedelta(hours=5))


def now_tashkent() -> datetime:
    """Hozirgi vaqtni Toshkent vaqt zonasida qaytaradi."""
    return datetime.now(TASHKENT_TZ)


def format_timestamp(ts: float, fmt: str = "%d.%m.%Y %H:%M") -> str:
    """
    Unix timestamp'ni (masalan `time.time()` natijasi yoki DB'dagi
    `created_at`) Toshkent vaqt zonasida, berilgan formatda matnga
    aylantiradi. Bu funksiya butun loyihada sana/vaqt ko'rsatish uchun
    YAGONA to'g'ri yo'l - to'g'ridan-to'g'ri `datetime.fromtimestamp()`
    yoki `time.strftime()` ishlatilmasligi kerak (ular server vaqt
    zonasini, ya'ni UTC'ni ishlatib, noto'g'ri soat ko'rsatardi).
    """
    return datetime.fromtimestamp(ts, tz=TASHKENT_TZ).strftime(fmt)

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


async def bot_can_delete_messages(bot: Bot, chat_id: int) -> bool:
    """
    Botning shu guruhda xabar o'chirish huquqi ("can_delete_messages")
    haqiqatan bor-yo'qligini tekshiradi.

    MUHIM: bu tekshiruv qilinmasa, `/lock` buyrug'i faqat bazaga yozib
    qo'yib "taqiqlandi" deb aytadi-yu, lekin botda haqiqiy o'chirish
    huquqi bo'lmasa, keyinchalik kelgan taqiqlangan xabarlar (rasm/gif/
    sticker/video) o'chmay qoladi - admin esa "ishladi deb yozadi, lekin
    ishlamaydi" degan holatga tushadi. Guruh EGASI (owner) har doim
    o'chira oladi (Telegram cheklovi yo'q), oddiy admin bo'lsa faqat
    `can_delete_messages=True` bo'lsa o'chira oladi.
    """
    try:
        member = await bot.get_chat_member(chat_id, bot.id)
    except Exception:
        return False
    if isinstance(member, ChatMemberOwner):
        return True
    if isinstance(member, ChatMemberAdministrator):
        return bool(member.can_delete_messages)
    return False


async def is_chat_owner(bot: Bot, chat_id: int, user_id: int) -> bool:
    """
    Faqat guruhning HAQIQIY egasi (Telegram'dagi "creator" statusi) yoki
    bot super-adminlari uchun True qaytaradi. Oddiy admin (owner emas)
    uchun False.

    Bu qasddan qattiqroq tekshiruv: /adminber va /adminol kabi "yangi
    admin yaratish/olib tashlash" imkoniyati faqat guruh egasiga tegishli
    bo'lishi kerak - aks holda "buzilgan" oddiy admin cheksiz yangi admin
    yaratib, guruhni butunlay egallab olishi mumkin edi.
    """
    if is_super_admin(user_id):
        return True
    try:
        member = await bot.get_chat_member(chat_id, user_id)
    except Exception:
        return False
    return isinstance(member, ChatMemberOwner)


async def resolve_target_user(message: Message, bot: Bot) -> User | None:
    """
    Nishonni aniqlaydi: avval reply qilingan xabar egasi, keyin
    entity (text_mention) orqali. @username orqali user obyektini
    olish uchun Bot API imkoni cheklangan, shu uchun reply/entity
    ustuvor qilingan.

    Eslatma: buyruq argumentidan (raqamli ID/@username) nishon topish
    uchun quyidagi `resolve_target()` funksiyasini ishlatish kerak - u
    ushbu funksiyani ham o'z ichiga oladi.
    """
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user

    if message.entities:
        for entity in message.entities:
            if entity.type == "text_mention" and entity.user:
                return entity.user
    return None


async def resolve_target(
    message: Message, bot: Bot, args: str | None
) -> tuple[User | None, str | None]:
    """
    Nishonni (kimga nisbatan amal qilinayotganini) va qolgan matnni
    (sabab/muddat uchun ishlatiladigan qismi) aniqlaydi. Tekshiruv
    tartibi:

    1. Reply qilingan xabar egasi (bunda `args`ning HAMMASI qolgan
       matn hisoblanadi, chunki birinchi so'z nishon uchun ishlatilmagan)
    2. text_mention entity (xuddi shunday)
    3. `args`ning birinchi so'zi - RAQAMLI Telegram ID (masalan
       "/ban 8387547842 spam qildi" - bu holatda botning o'zi
       shu odamni oldin ko'rgan-ko'rmaganidan qat'i nazar ishlaydi,
       chunki Telegram Bot API ban/mute kabi amallarni ID orqali
       to'g'ridan-to'g'ri bajara oladi)
    4. `args`ning birinchi so'zi - @username (bot shu guruhda oldin
       ko'rgan a'zolar orasidan qidiradi - Telegram Bot API'da
       "@username orqali ID topish" degan umumiy metod yo'q, shu
       sabab faqat botning o'z xotirasi orqali ishlaydi)

    :return: (User yoki None, qolgan matn yoki None)
    """
    reply_target = await resolve_target_user(message, bot)
    if reply_target:
        remaining = (args or "").strip() or None
        return reply_target, remaining

    if not args or not args.strip():
        return None, None

    parts = args.strip().split(maxsplit=1)
    first_token = parts[0]
    remaining = parts[1].strip() if len(parts) > 1 else None
    remaining = remaining or None

    # Raqamli Telegram ID (masalan "/ban 8387547842" yoki "/ban -8387547842")
    stripped_token = first_token.lstrip("-")
    if stripped_token.isdigit() and stripped_token:
        user_id = int(first_token)
        try:
            member = await bot.get_chat_member(message.chat.id, user_id)
            return member.user, remaining
        except Exception:
            # Bot bu odamni hozir guruh a'zosi sifatida topolmadi (masalan
            # u hali guruhga umuman kirmagan, yoki allaqachon chiqib
            # ketgan) - lekin ban/mute kabi amallar Telegram tomonidan
            # baribir foydalanuvchi ID orqali bajarilishi mumkin, shu
            # sabab minimal User obyekti yasab qaytaramiz.
            return (
                User(id=user_id, is_bot=False, first_name=str(user_id)),
                remaining,
            )

    # @username (bot ko'rgan a'zolar ro'yxatidan qidiramiz)
    if first_token.startswith("@") and len(first_token) > 1:
        from database import db  # aylanma import'ni oldini olish uchun shu yerda

        username = first_token.lstrip("@")
        row = await db.get_known_member_by_username(message.chat.id, username)
        if row:
            return (
                User(
                    id=row["user_id"],
                    is_bot=False,
                    first_name=row["full_name"] or username,
                    username=row["username"],
                ),
                remaining,
            )
        return None, None

    return None, None

