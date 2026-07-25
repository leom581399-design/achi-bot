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
import re
import time

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandObject
from aiogram.types import ChatMemberAdministrator, ChatMemberOwner, Message

import texts
from config import is_super_admin, settings
from database import db
from utils import format_timestamp, is_chat_admin, is_chat_owner, mention_html, resolve_target

router = Router(name="admin_tools")


# ------------------------------------------------------------------
# @admin / @admins ping
# ------------------------------------------------------------------

# Har (chat, chaqiruvchi) juftligi uchun oxirgi chaqirilgan vaqt - spamni
# oldini olish uchun (config.admin_ping_cooldown_sec).
_last_ping: dict[tuple[int, int], float] = {}


_ADMIN_PING_RE = re.compile(r"(?i)(^|\s)@admins?\b")


def _is_admin_ping_text(message: Message) -> bool:
    """
    Oddiy Python funksiyasi orqali tekshiruv - MagicFilter'ning
    `F.text.regexp(...)` chaqiruvidan farqli o'laroq, `message.text is None`
    bo'lgan xabarlarda (rasm, stiker, video va h.k.) TypeError tashlamaydi.
    (F.text.regexp(...) None ustida regexp.search() chaqirib, xato berardi -
    bu real xato edi, shu sabab bu funksiyaga o'zgartirildi.)
    """
    return bool(message.text) and bool(_ADMIN_PING_RE.search(message.text))


@router.message(
    F.chat.type.in_({"group", "supergroup"}),
    _is_admin_ping_text,
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

    target, _ = await resolve_target(message, bot, command.args)
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

    target, _ = await resolve_target(message, bot, command.args)
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
# /achi - bot haqida (super-admin uchun - qaysi guruhlarda ishlaydi)
# ------------------------------------------------------------------


@router.message(Command("achi"))
async def cmd_achi(message: Message) -> None:
    is_group = message.chat.type in ("group", "supergroup")

    # Guruhda /achi buyrug'i berilganda FAQAT reklama kanallar ro'yxati
    # chiqishi kerak - boshqa hech narsa (bot haqida matn ham, super-admin
    # uchun guruhlar ro'yxati ham) qo'shilmasin, aynan foydalanuvchi
    # so'ragan ushbu yakka ro'yxat chiqishi shart.
    if is_group:
        await message.reply(texts.ACHI_GROUP_LINKS_ONLY)
        return

    # Shaxsiy chatda (DM) - odatdagidek bot haqida ma'lumot, super-admin
    # uchun esa qo'shimcha guruhlar ro'yxati.
    if not message.from_user or not is_super_admin(message.from_user.id):
        await message.reply(texts.ACHI_ABOUT)
        return

    # Bot egasi uchun - qo'shimcha qilib qaysi guruhlarda ishlab
    # turganini ham ko'rsatamiz.
    chats = await db.list_all_chats()
    if not chats:
        await message.answer(f"{texts.ACHI_ABOUT}\n\n{texts.ACHI_NO_GROUPS}")
        return

    lines = [texts.ACHI_ABOUT, "", texts.ACHI_GROUPS_HEADER.format(count=len(chats))]
    now = time.time()
    for row in chats:
        title = row["chat_title"] or f"ID: {row['chat_id']}"
        if row["premium_lifetime"]:
            premium_mark = " ⭐(umrbod)"
        elif row["premium_until"] and row["premium_until"] > now:
            premium_mark = " ⭐"
        else:
            premium_mark = ""
        lines.append(texts.ACHI_GROUPS_ITEM.format(title=title, premium=premium_mark))

    text = "\n".join(lines)
    # Telegram xabar uzunligi cheklangan (4096 belgi) - juda ko'p guruh
    # bo'lsa bo'lib yuboramiz.
    if len(text) <= 4000:
        await message.answer(text)
        return

    await message.answer(lines[0] + "\n\n" + lines[2])
    chunk: list[str] = []
    chunk_len = 0
    for line in lines[3:]:
        chunk.append(line)
        chunk_len += len(line) + 1
        if chunk_len > 3500:
            await message.answer("\n".join(chunk))
            chunk = []
            chunk_len = 0
    if chunk:
        await message.answer("\n".join(chunk))



# ------------------------------------------------------------------
# /info - foydalanuvchi profili (reply qilib yoki @username bilan)
# ------------------------------------------------------------------


@router.message(Command("info"))
async def cmd_info(message: Message, command: CommandObject, bot: Bot) -> None:
    if message.chat.type not in ("group", "supergroup"):
        await message.reply(texts.ONLY_IN_GROUP)
        return

    target, _ = await resolve_target(message, bot, command.args)
    if not target:
        # Hech kim ko'rsatilmagan bo'lsa, o'zining profilini ko'rsatamiz.
        target = message.from_user

    if not target:
        await message.reply(texts.INFO_USAGE)
        return

    mention = mention_html(target.id, target.full_name)

    try:
        member = await bot.get_chat_member(message.chat.id, target.id)
        status = member.status
    except TelegramAPIError:
        status = "noma'lum"

    status_label = {
        "creator": "Guruh egasi 👑",
        "administrator": "Admin 🛡",
        "member": "Oddiy a'zo",
        "restricted": "Cheklangan (mute) 🔇",
        "left": "Guruhda yo'q",
        "kicked": "Banlangan 🚫",
    }.get(status, "Noma'lum")

    warn_count = await db.count_warns(message.chat.id, target.id)

    known_row = await db.get_known_member(message.chat.id, target.id)
    if known_row and known_row["first_seen"]:
        first_seen_str = format_timestamp(known_row["first_seen"])
    else:
        first_seen_str = texts.INFO_UNKNOWN_DATE

    username_str = f"@{target.username}" if target.username else texts.INFO_NO_USERNAME

    text = texts.INFO_RESULT.format(
        mention=mention,
        username=username_str,
        user_id=target.id,
        status=status_label,
        first_seen=first_seen_str,
        warn_count=warn_count,
        max_warns=settings.max_warns,
    )
    await message.reply(text)
