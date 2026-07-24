"""
ACHI BOT - qo'shimcha admin vositalari:

1. @admin / @admins - guruhdagi barcha adminlarni "ping" qilib chaqirish
   (boshqa mashhur botlardagi kabi).
2. /adminber - kimnidir ACHI BOT orqali admin qilish (faqat guruh EGASI).
3. /adminol - ACHI BOT orqali berilgan adminlikni olib tashlash (faqat
   guruh EGASI).
4. /tag - guruhda ko'rilgan barcha a'zolarni chaqirish (admin buyrug'i).
"""
from __future__ import annotations

import asyncio
import time

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandObject
from aiogram.types import ChatMemberAdministrator, ChatMemberOwner, Message, User

import texts
from config import settings
from database import db
from utils import is_chat_admin, is_chat_owner, mention_html, resolve_target_user

router = Router(name="admin_tools")


# ------------------------------------------------------------------
# @admin / @admins ping
# ------------------------------------------------------------------

# Har (chat, chaqiruvchi) juftligi uchun oxirgi chaqirilgan vaqt - spamni
# oldini olish uchun (config.admin_ping_cooldown_sec).
_last_ping: dict[tuple[int, int], float] = {}


@router.message(
    F.chat.type.in_({"group", "supergroup"}),
    F.text.regexp(r"(?i)(^|\s)@admins?\b"),
)
async def on_admin_ping(message: Message, bot: Bot) -> None:
    if not message.from_user:
        return

    key = (message.chat.id, message.from_user.id)
    now = time.time()
    last = _last_ping.get(key)
    if last and now - last < settings.admin_ping_cooldown_sec:
        remaining = int(settings.admin_ping_cooldown_sec - (now - last))
        await message.reply(texts.ADMIN_PING_COOLDOWN.format(seconds=remaining))
        return

    try:
        admins = await bot.get_chat_administrators(message.chat.id)
    except TelegramAPIError:
        return

    mentions = [
        mention_html(a.user.id, a.user.full_name)
        for a in admins
        if not a.user.is_bot
    ]
    if not mentions:
        await message.reply(texts.ADMIN_PING_NO_ADMINS)
        return

    _last_ping[key] = now

    caller = mention_html(message.from_user.id, message.from_user.full_name)
    header = texts.ADMIN_PING_HEADER.format(caller=caller)
    await message.reply(f"{header}\n{' '.join(mentions)}")


# ------------------------------------------------------------------
# Nishonni aniqlash (reply / text_mention / @username orqali
# known_members jadvalidan qidirish)
# ------------------------------------------------------------------


async def _resolve_target(message: Message, bot: Bot, args: str | None) -> User | None:
    target = await resolve_target_user(message, bot)
    if target:
        return target

    if not args:
        return None

    username = args.strip().lstrip("@").split()[0].lower()
    if not username:
        return None

    rows = await db.list_known_members(message.chat.id)
    for row in rows:
        if row["username"] and row["username"].lower() == username:
            return User(
                id=row["user_id"],
                is_bot=False,
                first_name=row["full_name"] or username,
                username=row["username"],
            )
    return None


# ------------------------------------------------------------------
# /adminber - admin qilish
# ------------------------------------------------------------------


@router.message(Command("adminber"))
async def cmd_adminber(message: Message, command: CommandObject, bot: Bot) -> None:
    if message.chat.type not in ("group", "supergroup"):
        await message.reply(texts.ONLY_IN_GROUP)
        return
    if not message.from_user or not await is_chat_owner(
        bot, message.chat.id, message.from_user.id
    ):
        await message.reply(texts.ADMINBER_ONLY_OWNER)
        return

    target = await _resolve_target(message, bot, command.args)
    if not target:
        await message.reply(texts.ADMINBER_USAGE)
        return

    try:
        member = await bot.get_chat_member(message.chat.id, target.id)
    except TelegramAPIError:
        member = None
    if isinstance(member, (ChatMemberAdministrator, ChatMemberOwner)):
        await message.reply(texts.ADMINBER_CANT_PROMOTE_ADMIN)
        return

    try:
        await bot.promote_chat_member(
            message.chat.id,
            target.id,
            can_change_info=False,
            can_delete_messages=True,
            can_invite_users=True,
            can_restrict_members=True,
            can_pin_messages=True,
            can_promote_members=False,
            can_manage_video_chats=False,
            is_anonymous=False,
        )
    except TelegramAPIError:
        await message.reply(texts.BOT_NOT_ADMIN)
        return

    await db.add_bot_promoted_admin(message.chat.id, target.id, message.from_user.id)
    await db.log_action(
        chat_id=message.chat.id,
        chat_title=message.chat.title,
        action="promote",
        target_id=target.id,
        target_name=target.full_name,
        target_username=target.username,
        admin_id=message.from_user.id,
        admin_name=message.from_user.full_name,
        reason="ACHI BOT orqali admin qilindi",
    )

    mention = mention_html(target.id, target.full_name)
    admin_mention = mention_html(message.from_user.id, message.from_user.full_name)
    await message.reply(texts.ADMINBER_DONE.format(target=mention, admin=admin_mention))


# ------------------------------------------------------------------
# /adminol - adminlikni olib tashlash
# ------------------------------------------------------------------


@router.message(Command("adminol"))
async def cmd_adminol(message: Message, command: CommandObject, bot: Bot) -> None:
    if message.chat.type not in ("group", "supergroup"):
        await message.reply(texts.ONLY_IN_GROUP)
        return
    if not message.from_user or not await is_chat_owner(
        bot, message.chat.id, message.from_user.id
    ):
        await message.reply(texts.ADMINOL_ONLY_OWNER)
        return

    target = await _resolve_target(message, bot, command.args)
    if not target:
        await message.reply(texts.ADMINOL_USAGE)
        return

    try:
        member = await bot.get_chat_member(message.chat.id, target.id)
    except TelegramAPIError:
        member = None
    if isinstance(member, ChatMemberOwner):
        await message.reply(texts.ADMINOL_CANT_TARGET_OWNER)
        return

    # Faqat ACHI BOT orqali berilgan adminlikni olib tashlashga ruxsat
    # beramiz - Telegram orqali to'g'ridan-to'g'ri tayinlangan adminlarga
    # tegmaymiz (bu bot vakolatidan tashqari, chalkashlikni oldini olish
    # uchun ataylab shunday cheklangan).
    was_bot_promoted = await db.is_bot_promoted_admin(message.chat.id, target.id)
    if not was_bot_promoted:
        await message.reply(texts.ADMINOL_NOT_BOT_PROMOTED)
        return

    try:
        await bot.promote_chat_member(
            message.chat.id,
            target.id,
            can_change_info=False,
            can_delete_messages=False,
            can_invite_users=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_promote_members=False,
            can_manage_video_chats=False,
            is_anonymous=False,
        )
    except TelegramAPIError:
        await message.reply(texts.BOT_NOT_ADMIN)
        return

    await db.remove_bot_promoted_admin(message.chat.id, target.id)
    await db.log_action(
        chat_id=message.chat.id,
        chat_title=message.chat.title,
        action="demote",
        target_id=target.id,
        target_name=target.full_name,
        target_username=target.username,
        admin_id=message.from_user.id,
        admin_name=message.from_user.full_name,
        reason="ACHI BOT orqali adminlikdan olindi",
    )

    mention = mention_html(target.id, target.full_name)
    admin_mention = mention_html(message.from_user.id, message.from_user.full_name)
    await message.reply(texts.ADMINOL_DONE.format(target=mention, admin=admin_mention))


# ------------------------------------------------------------------
# /tag - ko'rilgan a'zolarni chaqirish
# ------------------------------------------------------------------


@router.message(Command("tag"))
async def cmd_tag(message: Message, command: CommandObject, bot: Bot) -> None:
    if message.chat.type not in ("group", "supergroup"):
        await message.reply(texts.ONLY_IN_GROUP)
        return
    if not message.from_user or not await is_chat_admin(
        bot, message.chat.id, message.from_user.id
    ):
        await message.reply(texts.TAG_ONLY_ADMIN)
        return

    rows = await db.list_known_members(
        message.chat.id, exclude_user_id=message.from_user.id
    )
    if not rows:
        await message.reply(texts.TAG_NO_MEMBERS)
        return

    extra_text = (command.args or "").strip()
    await message.reply(texts.TAG_STARTED.format(count=len(rows)))

    batch_size = settings.tag_batch_size
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        mentions = [
            mention_html(r["user_id"], r["full_name"] or "a'zo") for r in batch
        ]
        text = " ".join(mentions)
        if extra_text:
            text = f"{extra_text}\n{text}"
        try:
            await message.answer(text)
        except TelegramAPIError:
            pass
        if i + batch_size < len(rows):
            await asyncio.sleep(settings.tag_batch_delay_sec)



# ------------------------------------------------------------------
# /staff - guruh adminlari ro'yxati
# ------------------------------------------------------------------


@router.message(Command("staff"))
async def cmd_staff(message: Message, bot: Bot) -> None:
    if message.chat.type not in ("group", "supergroup"):
        await message.reply(texts.ONLY_IN_GROUP)
        return

    try:
        admins = await bot.get_chat_administrators(message.chat.id)
    except TelegramAPIError:
        await message.reply(texts.STAFF_EMPTY)
        return

    real_admins = [a for a in admins if not a.user.is_bot]
    if not real_admins:
        await message.reply(texts.STAFF_EMPTY)
        return

    lines = [texts.STAFF_HEADER.format(chat_title=message.chat.title or "")]
    owners = [a for a in real_admins if isinstance(a, ChatMemberOwner)]
    others = [a for a in real_admins if not isinstance(a, ChatMemberOwner)]

    for a in owners:
        mention = mention_html(a.user.id, a.user.full_name)
        lines.append(texts.STAFF_OWNER_LINE.format(mention=mention))
    for a in others:
        mention = mention_html(a.user.id, a.user.full_name)
        lines.append(texts.STAFF_ADMIN_LINE.format(mention=mention))

    await message.reply("\n".join(lines))


# ------------------------------------------------------------------
# /achi - bot haqida
# ------------------------------------------------------------------


@router.message(Command("achi"))
async def cmd_achi(message: Message) -> None:
    await message.reply(texts.ACHI_ABOUT)
