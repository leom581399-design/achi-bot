"""
ACHI BOT - moderatsiya: ban/unban/mute/unmute/kick/warn/unwarn/warns + lock/unlock.

Qoida: sabab MAJBURIY EMAS - admin xohlasa yozadi, xohlamasa yozmaydi
(bunday holda "ko'rsatilmagan" deb yoziladi). Nishonni (kimga nisbatan
amal qilinayotganini) aniqlash uchun uchta yo'l bor:

1. Reply qilib buyruq yozish (masalan xabarga reply qilib "/ban spam")
2. text_mention (odamni "@" bilan belgilab, Telegram avtomatik taklif
   qilgan holatda)
3. Buyruq argumentida to'g'ridan-to'g'ri RAQAMLI Telegram ID yozish
   (masalan "/ban 8387547842 spam qildi") - bu ODAM GURUHDA HOZIR
   BO'LMASA HAM ishlaydi, chunki Telegram Bot API ban/mute kabi
   amallarni foydalanuvchi ID orqali to'g'ridan-to'g'ri bajara oladi
4. Buyruq argumentida @username yozish (bot avval shu odamni ko'rgan
   bo'lishi kerak - Telegram Bot API'da "@username orqali ID topish"
   degan umumiy metod yo'q)
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta

from aiogram import Bot, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandObject
from aiogram.types import ChatPermissions, Message

import texts
from config import settings
from database import db
from utils import (
    is_chat_admin,
    is_target_admin,
    mention_html,
    parse_duration,
    resolve_target,
    user_display_name,
)

router = Router(name="moderation")

_MUTED_PERMISSIONS = ChatPermissions(
    can_send_messages=False,
    can_send_audios=False,
    can_send_documents=False,
    can_send_photos=False,
    can_send_videos=False,
    can_send_video_notes=False,
    can_send_voice_notes=False,
    can_send_polls=False,
    can_send_other_messages=False,
    can_add_web_page_previews=False,
)

_UNMUTED_PERMISSIONS = ChatPermissions(
    can_send_messages=True,
    can_send_audios=True,
    can_send_documents=True,
    can_send_photos=True,
    can_send_videos=True,
    can_send_video_notes=True,
    can_send_voice_notes=True,
    can_send_polls=True,
    can_send_other_messages=True,
    can_add_web_page_previews=True,
)


async def _guard(message: Message, bot: Bot) -> bool:
    """Umumiy tekshiruvlar: guruhda ekanligi, admin ekanligi."""
    if message.chat.type not in ("group", "supergroup"):
        await message.reply(texts.ONLY_IN_GROUP)
        return False
    if not message.from_user or not await is_chat_admin(
        bot, message.chat.id, message.from_user.id
    ):
        await message.reply(texts.NOT_ADMIN)
        return False
    return True


def _duration_label(delta: timedelta) -> str:
    total = int(delta.total_seconds())
    if total % (7 * 86400) == 0:
        return f"{total // (7 * 86400)} hafta"
    if total % 86400 == 0:
        return f"{total // 86400} kun"
    if total % 3600 == 0:
        return f"{total // 3600} soat"
    return f"{total // 60} daqiqa"


async def _execute_action(
    *,
    bot: Bot,
    chat_id: int,
    chat_title: str | None,
    action: str,
    target_id: int,
    target_name: str,
    target_username: str | None,
    admin_id: int,
    admin_name: str,
    reason: str,
    duration_seconds: int | None,
    duration_label: str | None,
    reply_message: Message,
) -> None:
    target_mention = mention_html(target_id, target_name)
    admin_mention_text = admin_name

    if action in ("ban", "tban"):
        until_date = None
        if duration_seconds:
            until_date = int(time.time()) + duration_seconds
        try:
            await bot.ban_chat_member(chat_id, target_id, until_date=until_date)
        except TelegramAPIError:
            await reply_message.answer(texts.BOT_NOT_ADMIN)
            return
        await db.log_action(
            chat_id=chat_id,
            chat_title=chat_title,
            action=action,
            target_id=target_id,
            target_name=target_name,
            target_username=target_username,
            admin_id=admin_id,
            admin_name=admin_name,
            reason=reason,
            duration=duration_label,
        )
        if action == "tban":
            text = texts.TBAN_DONE.format(
                target=target_mention,
                duration=duration_label,
                reason=reason,
                admin=admin_mention_text,
            )
        else:
            text = texts.BAN_DONE.format(
                target=target_mention, reason=reason, admin=admin_mention_text
            )
        await reply_message.answer(text)

    elif action in ("mute", "tmute"):
        until_date = None
        if duration_seconds:
            until_date = int(time.time()) + duration_seconds
        try:
            await bot.restrict_chat_member(
                chat_id, target_id, permissions=_MUTED_PERMISSIONS, until_date=until_date
            )
        except TelegramAPIError:
            await reply_message.answer(texts.BOT_NOT_ADMIN)
            return
        await db.log_action(
            chat_id=chat_id,
            chat_title=chat_title,
            action=action,
            target_id=target_id,
            target_name=target_name,
            target_username=target_username,
            admin_id=admin_id,
            admin_name=admin_name,
            reason=reason,
            duration=duration_label,
        )
        if action == "tmute":
            text = texts.TMUTE_DONE.format(
                target=target_mention,
                duration=duration_label,
                reason=reason,
                admin=admin_mention_text,
            )
        else:
            text = texts.MUTE_DONE.format(
                target=target_mention, reason=reason, admin=admin_mention_text
            )
        await reply_message.answer(text)

    elif action == "kick":
        try:
            await bot.ban_chat_member(chat_id, target_id)
            await bot.unban_chat_member(chat_id, target_id, only_if_banned=True)
        except TelegramAPIError:
            await reply_message.answer(texts.BOT_NOT_ADMIN)
            return
        await db.log_action(
            chat_id=chat_id,
            chat_title=chat_title,
            action=action,
            target_id=target_id,
            target_name=target_name,
            target_username=target_username,
            admin_id=admin_id,
            admin_name=admin_name,
            reason=reason,
        )
        await reply_message.answer(
            texts.KICK_DONE.format(
                target=target_mention, reason=reason, admin=admin_mention_text
            )
        )

    elif action == "warn":
        count = await db.add_warn(chat_id, target_id, reason, admin_id, admin_name)
        await db.log_action(
            chat_id=chat_id,
            chat_title=chat_title,
            action=action,
            target_id=target_id,
            target_name=target_name,
            target_username=target_username,
            admin_id=admin_id,
            admin_name=admin_name,
            reason=reason,
        )
        if count >= settings.max_warns:
            try:
                await bot.ban_chat_member(chat_id, target_id)
            except TelegramAPIError:
                await reply_message.answer(texts.BOT_NOT_ADMIN)
                return
            await db.log_action(
                chat_id=chat_id,
                chat_title=chat_title,
                action="ban",
                target_id=target_id,
                target_name=target_name,
                target_username=target_username,
                admin_id=admin_id,
                admin_name="ACHI BOT (avto)",
                reason=f"{settings.max_warns} marta ogohlantirish to'plandi",
            )
            await db.clear_warns(chat_id, target_id)
            await reply_message.answer(
                texts.WARN_LIMIT_REACHED.format(
                    target=target_mention, max_warns=settings.max_warns
                )
            )
        else:
            await reply_message.answer(
                texts.WARN_DONE.format(
                    target=target_mention,
                    count=count,
                    max_warns=settings.max_warns,
                    reason=reason,
                    admin=admin_mention_text,
                )
            )


async def _dispatch(
    message: Message,
    bot: Bot,
    command: CommandObject,
    *,
    action: str,
    requires_duration: bool,
) -> None:
    if not await _guard(message, bot):
        return

    target, remaining_text = await resolve_target(message, bot, command.args)
    if not target:
        await message.reply(texts.REPLY_NEEDED)
        return

    if target.id == message.from_user.id:
        await message.reply(texts.CANT_ACT_ON_SELF)
        return

    if await is_target_admin(bot, message.chat.id, target.id):
        await message.reply(texts.CANT_ACT_ON_ADMIN)
        return

    duration_seconds: int | None = None
    duration_label: str | None = None

    if requires_duration:
        if not remaining_text:
            await message.reply(texts.DURATION_USAGE)
            return
        parts = remaining_text.split(maxsplit=1)
        delta = parse_duration(parts[0])
        if not delta:
            await message.reply(texts.DURATION_INVALID)
            return
        duration_seconds = int(delta.total_seconds())
        duration_label = _duration_label(delta)
        remaining_text = parts[1].strip() if len(parts) > 1 else None

    # Sabab MAJBURIY EMAS - yozilmasa standart matn ishlatiladi.
    reason = remaining_text if remaining_text else texts.REASON_NOT_SPECIFIED

    await _execute_action(
        bot=bot,
        chat_id=message.chat.id,
        chat_title=message.chat.title,
        action=action,
        target_id=target.id,
        target_name=target.full_name,
        target_username=target.username,
        admin_id=message.from_user.id,
        admin_name=user_display_name(message.from_user),
        reason=reason,
        duration_seconds=duration_seconds,
        duration_label=duration_label,
        reply_message=message,
    )


@router.message(Command("ban"))
async def cmd_ban(message: Message, command: CommandObject, bot: Bot) -> None:
    await _dispatch(message, bot, command, action="ban", requires_duration=False)


@router.message(Command("tban"))
async def cmd_tban(message: Message, command: CommandObject, bot: Bot) -> None:
    await _dispatch(message, bot, command, action="tban", requires_duration=True)


@router.message(Command("mute"))
async def cmd_mute(message: Message, command: CommandObject, bot: Bot) -> None:
    await _dispatch(message, bot, command, action="mute", requires_duration=False)


@router.message(Command("tmute"))
async def cmd_tmute(message: Message, command: CommandObject, bot: Bot) -> None:
    await _dispatch(message, bot, command, action="tmute", requires_duration=True)


@router.message(Command("kick"))
async def cmd_kick(message: Message, command: CommandObject, bot: Bot) -> None:
    await _dispatch(message, bot, command, action="kick", requires_duration=False)


@router.message(Command("warn"))
async def cmd_warn(message: Message, command: CommandObject, bot: Bot) -> None:
    await _dispatch(message, bot, command, action="warn", requires_duration=False)


@router.message(Command("unban"))
async def cmd_unban(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard(message, bot):
        return
    target, _ = await resolve_target(message, bot, command.args)
    if not target:
        await message.reply(texts.REPLY_NEEDED)
        return
    try:
        await bot.unban_chat_member(message.chat.id, target.id, only_if_banned=False)
    except TelegramAPIError:
        await message.reply(texts.BOT_NOT_ADMIN)
        return
    await db.log_action(
        chat_id=message.chat.id,
        chat_title=message.chat.title,
        action="unban",
        target_id=target.id,
        target_name=target.full_name,
        target_username=target.username,
        admin_id=message.from_user.id,
        admin_name=user_display_name(message.from_user),
        reason=None,
    )
    await message.reply(texts.UNBAN_DONE.format(target=mention_html(target.id, target.full_name)))


@router.message(Command("unmute"))
async def cmd_unmute(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard(message, bot):
        return
    target, _ = await resolve_target(message, bot, command.args)
    if not target:
        await message.reply(texts.REPLY_NEEDED)
        return
    try:
        await bot.restrict_chat_member(
            message.chat.id, target.id, permissions=_UNMUTED_PERMISSIONS
        )
    except TelegramAPIError:
        await message.reply(texts.BOT_NOT_ADMIN)
        return
    await db.log_action(
        chat_id=message.chat.id,
        chat_title=message.chat.title,
        action="unmute",
        target_id=target.id,
        target_name=target.full_name,
        target_username=target.username,
        admin_id=message.from_user.id,
        admin_name=user_display_name(message.from_user),
        reason=None,
    )
    await message.reply(texts.UNMUTE_DONE.format(target=mention_html(target.id, target.full_name)))


@router.message(Command("unwarn"))
async def cmd_unwarn(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard(message, bot):
        return
    target, _ = await resolve_target(message, bot, command.args)
    if not target:
        await message.reply(texts.REPLY_NEEDED)
        return
    removed = await db.remove_last_warn(message.chat.id, target.id)
    mention = mention_html(target.id, target.full_name)
    if not removed:
        await message.reply(texts.NO_WARNS.format(target=mention))
        return
    count = await db.count_warns(message.chat.id, target.id)
    await db.log_action(
        chat_id=message.chat.id,
        chat_title=message.chat.title,
        action="unwarn",
        target_id=target.id,
        target_name=target.full_name,
        target_username=target.username,
        admin_id=message.from_user.id,
        admin_name=user_display_name(message.from_user),
        reason=None,
    )
    await message.reply(texts.UNWARN_DONE.format(target=mention, count=count))


@router.message(Command("warns"))
async def cmd_warns(message: Message, command: CommandObject, bot: Bot) -> None:
    if message.chat.type not in ("group", "supergroup"):
        await message.reply(texts.ONLY_IN_GROUP)
        return
    target, _ = await resolve_target(message, bot, command.args)
    if not target:
        await message.reply(texts.REPLY_NEEDED)
        return
    mention = mention_html(target.id, target.full_name)
    rows = await db.list_warns(message.chat.id, target.id)
    if not rows:
        await message.reply(texts.WARNS_LIST_EMPTY.format(target=mention))
        return
    lines = [texts.WARNS_LIST_HEADER.format(target=mention, count=len(rows), max_warns=settings.max_warns)]
    for i, row in enumerate(rows, start=1):
        date = datetime.fromtimestamp(row["created_at"]).strftime("%d.%m.%Y %H:%M")
        lines.append(
            texts.WARNS_LIST_ITEM.format(
                num=i,
                reason=row["reason"] or texts.REASON_NOT_SPECIFIED,
                admin=row["admin_name"] or "?",
                date=date,
            )
        )
    await message.reply("\n".join(lines))


# ------------------------------------------------------------------
# Lock / Unlock
# ------------------------------------------------------------------

_VALID_LOCKS = {"link", "photo", "video", "sticker", "forward", "gif", "all"}


@router.message(Command("lock"))
async def cmd_lock(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard(message, bot):
        return
    lock_type = (command.args or "").strip().lower()
    if lock_type not in _VALID_LOCKS:
        await message.reply(texts.LOCK_TYPE_UNKNOWN)
        return
    await db.set_lock(message.chat.id, lock_type)
    await message.reply(texts.LOCK_DONE.format(lock_name=texts.LOCK_NAMES[lock_type]))


@router.message(Command("unlock"))
async def cmd_unlock(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard(message, bot):
        return
    lock_type = (command.args or "").strip().lower()
    if lock_type not in _VALID_LOCKS:
        await message.reply(texts.LOCK_TYPE_UNKNOWN)
        return
    await db.unset_lock(message.chat.id, lock_type)
    await message.reply(texts.UNLOCK_DONE.format(lock_name=texts.LOCK_NAMES[lock_type]))


@router.message(Command("locks"))
async def cmd_locks(message: Message, bot: Bot) -> None:
    if message.chat.type not in ("group", "supergroup"):
        await message.reply(texts.ONLY_IN_GROUP)
        return
    locks = await db.list_locks(message.chat.id)
    if not locks:
        await message.reply(f"{texts.LOCKS_HEADER}\n{texts.LOCKS_EMPTY}")
        return
    names = ", ".join(texts.LOCK_NAMES.get(l, l) for l in locks)
    await message.reply(f"{texts.LOCKS_HEADER} {names}")


def _content_lock_type(message: Message) -> str | None:
    if message.photo:
        return "photo"
    if message.video or message.video_note:
        return "video"
    if message.sticker:
        return "sticker"
    if message.animation:
        return "gif"
    if message.forward_date or message.forward_from or message.forward_from_chat:
        return "forward"
    if message.entities:
        for entity in message.entities:
            if entity.type in ("url", "text_link"):
                return "link"
    if message.text and ("http://" in message.text or "https://" in message.text or "t.me/" in message.text):
        return "link"
    return None


async def _check_lock(message: Message, bot: Bot):
    """
    Filtr sifatida ishlatiladi: faqat haqiqatan ham qulflangan (o'chirilishi
    kerak bo'lgan) xabarlar uchun True/dict qaytaradi. Bu MUHIM - agar bu
    yerda oddiy "return" bilan handler ichida chiqib ketilsa (filtr True
    qaytarib, handler keyin hech narsa qilmasa), aiogram baribir shu
    xabarni "band qilindi" deb hisoblab, boshqa routerlarga (masalan admin
    buyruqlariga) yuborilishini to'xtatib qo'yardi. Shu sabab tekshiruvning
    hammasi filtr darajasida bo'lishi kerak.
    """
    if not message.from_user or message.from_user.is_bot:
        return False
    if message.chat.type not in ("group", "supergroup"):
        return False
    if await is_chat_admin(bot, message.chat.id, message.from_user.id):
        return False

    content_type = _content_lock_type(message)
    if not content_type:
        return False

    locked_all = await db.is_locked(message.chat.id, "all")
    locked_specific = await db.is_locked(message.chat.id, content_type)
    if not (locked_all or locked_specific):
        return False

    return {"lock_content_type": content_type}


@router.message(_check_lock)
async def enforce_locks(message: Message, lock_content_type: str) -> None:
    try:
        await message.delete()
    except Exception:
        pass
    mention = mention_html(message.from_user.id, message.from_user.full_name)
    try:
        await message.answer(texts.LOCKED_CONTENT_REMOVED.format(mention=mention))
    except Exception:
        pass
