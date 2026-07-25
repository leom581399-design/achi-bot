"""
ACHI BOT - Federatsiya (premium funksiya).

Federatsiya orqali bir nechta guruhni bog'lab, umumiy ban ro'yxatini
ishlatish mumkin: bitta guruhda /fban qilingan odam federatsiyaga a'zo
BARCHA guruhlarda avtomatik banlanadi.

Cheklov: federatsiya yaratish/guruhni federatsiyaga ulash faqat premium
guruhlar uchun ochiq (yoki bot egasi/super-admin bo'lsa - unga har doim
tekin). /fban/funban esa federatsiyaga allaqachon ulangan har qanday
guruh admini uchun ishlaydi (chunki ulanish bosqichida premium talab
qilingan edi).
"""
from __future__ import annotations

import secrets

from aiogram import Bot, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

import texts
from database import db
from handlers.premium import is_premium_or_free
from utils import is_chat_admin, mention_html, resolve_target, user_display_name

router = Router(name="federation")


async def _guard_admin(message: Message, bot: Bot) -> bool:
    if message.chat.type not in ("group", "supergroup"):
        await message.reply(texts.ONLY_IN_GROUP)
        return False
    if not message.from_user or not await is_chat_admin(
        bot, message.chat.id, message.from_user.id
    ):
        await message.reply(texts.NOT_ADMIN)
        return False
    return True


def _generate_fed_id() -> str:
    return secrets.token_hex(4)


@router.message(Command("fnew"))
async def cmd_fnew(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return

    if not await is_premium_or_free(message.chat.id, message.from_user.id):
        await message.reply(texts.FED_REQUIRES_PREMIUM)
        return

    existing = await db.get_federation_by_owner(message.from_user.id)
    if existing:
        await message.reply(
            texts.FED_ALREADY_OWN.format(name=existing["name"], fed_id=existing["fed_id"])
        )
        return

    name = (command.args or "").strip() or f"{message.chat.title or 'Fed'}"
    fed_id = _generate_fed_id()
    await db.create_federation(fed_id, name, message.from_user.id)
    await db.link_chat_to_federation(fed_id, message.chat.id)
    await message.reply(texts.FED_CREATED.format(name=name, fed_id=fed_id))


@router.message(Command("fjoin"))
async def cmd_fjoin(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return

    if not await is_premium_or_free(message.chat.id, message.from_user.id):
        await message.reply(texts.FED_REQUIRES_PREMIUM)
        return

    fed_id = (command.args or "").strip()
    if not fed_id:
        await message.reply(texts.FED_USAGE)
        return

    fed = await db.get_federation(fed_id)
    if not fed:
        await message.reply(texts.FED_NOT_FOUND)
        return

    if not await db.is_fed_admin(fed_id, message.from_user.id):
        await message.reply(texts.FED_JOIN_NOT_OWNER)
        return

    await db.link_chat_to_federation(fed_id, message.chat.id)
    await message.reply(texts.FED_JOINED.format(name=fed["name"]))


@router.message(Command("fleave"))
async def cmd_fleave(message: Message, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return

    fed_id = await db.get_chat_federation(message.chat.id)
    if not fed_id:
        await message.reply(texts.FED_NOT_IN_ANY)
        return

    await db.unlink_chat_from_federation(message.chat.id)
    await message.reply(texts.FED_LEFT)


@router.message(Command("finfo"))
async def cmd_finfo(message: Message) -> None:
    if message.chat.type not in ("group", "supergroup"):
        await message.reply(texts.ONLY_IN_GROUP)
        return

    fed_id = await db.get_chat_federation(message.chat.id)
    if not fed_id:
        await message.reply(texts.FED_NOT_IN_ANY)
        return

    fed = await db.get_federation(fed_id)
    if not fed:
        await message.reply(texts.FED_NOT_FOUND)
        return

    chats = await db.get_federation_chats(fed_id)
    bans_count = await db.count_fed_bans(fed_id)
    await message.reply(
        texts.FED_INFO.format(
            name=fed["name"],
            fed_id=fed_id,
            chats_count=len(chats),
            bans_count=bans_count,
        )
    )


@router.message(Command("fban"))
async def cmd_fban(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return

    fed_id = await db.get_chat_federation(message.chat.id)
    if not fed_id:
        await message.reply(texts.FED_NOT_IN_ANY)
        return

    target, remaining_text = await resolve_target(message, bot, command.args)
    if not target:
        await message.reply(texts.REPLY_NEEDED)
        return

    reason = remaining_text or texts.REASON_NOT_SPECIFIED
    await db.fed_ban(fed_id, target.id, reason, message.from_user.id)

    chats = await db.get_federation_chats(fed_id)
    for chat_id in chats:
        try:
            await bot.ban_chat_member(chat_id, target.id)
        except Exception:
            # Bot o'sha guruhda admin bo'lmasligi yoki boshqa sabab bilan
            # ban qilib bo'lmasligi mumkin - bitta guruh muvaffaqiyatsiz
            # bo'lsa ham, qolganlarida davom etamiz.
            pass
        await db.log_action(
            chat_id=chat_id,
            chat_title=None,
            action="ban",
            target_id=target.id,
            target_name=target.full_name,
            target_username=target.username,
            admin_id=message.from_user.id,
            admin_name=user_display_name(message.from_user),
            reason=f"[Federatsiya] {reason}",
        )

    mention = mention_html(target.id, target.full_name)
    await message.reply(texts.FED_BAN_DONE.format(target=mention, reason=reason))


@router.message(Command("funban"))
async def cmd_funban(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return

    fed_id = await db.get_chat_federation(message.chat.id)
    if not fed_id:
        await message.reply(texts.FED_NOT_IN_ANY)
        return

    target, _ = await resolve_target(message, bot, command.args)
    if not target:
        await message.reply(texts.REPLY_NEEDED)
        return

    removed = await db.fed_unban(fed_id, target.id)
    mention = mention_html(target.id, target.full_name)
    if not removed:
        await message.reply(texts.FED_NOT_BANNED)
        return

    chats = await db.get_federation_chats(fed_id)
    for chat_id in chats:
        try:
            await bot.unban_chat_member(chat_id, target.id, only_if_banned=True)
        except Exception:
            pass

    await message.reply(texts.FED_UNBAN_DONE.format(target=mention))


@router.message(Command("fed", "federation"))
async def cmd_fed_help(message: Message) -> None:
    await message.reply(texts.FED_USAGE)
