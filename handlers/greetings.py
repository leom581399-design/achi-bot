"""
ACHI BOT - qo'shilish/chiqish oqimi: welcome/goodbye xabarlari, captcha,
tizim xabarlarini tozalash (cleanservice) va join-request'larni avtomatik
qabul qilish.
"""
from __future__ import annotations

import time

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    CallbackQuery,
    ChatJoinRequest,
    ChatPermissions,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

import texts
from database import db
from utils import is_chat_admin, mention_html

router = Router(name="greetings")

_CAPTCHA_TIMEOUT_SEC = 90
_RESTRICTED_PERMISSIONS = ChatPermissions(can_send_messages=False)
_FULL_PERMISSIONS = ChatPermissions(
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


def _captcha_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=texts.CAPTCHA_BUTTON, callback_data=f"captcha:{user_id}"
                )
            ]
        ]
    )


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


# ------------------------------------------------------------------
# Sozlash buyruqlari
# ------------------------------------------------------------------


@router.message(Command("setwelcome"))
async def cmd_setwelcome(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return
    text = (command.args or "").strip()
    if not text:
        await message.reply(
            "Xush kelibsiz xabarini yozing. {mention} o'rniga odamning ismi qo'yiladi.\n"
            "Masalan: /setwelcome Salom {mention}, guruhimizga xush kelibsiz!"
        )
        return
    await db.ensure_chat(message.chat.id, message.chat.title)
    await db.update_chat_setting(message.chat.id, welcome_text=text)
    await message.reply(texts.WELCOME_SET)
    await message.answer(text.format(mention=mention_html(message.from_user.id, message.from_user.full_name)))


@router.message(Command("setgoodbye"))
async def cmd_setgoodbye(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return
    text = (command.args or "").strip()
    if not text:
        await message.reply("Xayrlashuv xabarini yozing. Masalan: /setgoodbye Xayr, {mention}!")
        return
    await db.ensure_chat(message.chat.id, message.chat.title)
    await db.update_chat_setting(message.chat.id, goodbye_text=text)
    await message.reply(texts.GOODBYE_SET)


@router.message(Command("cleanservice"))
async def cmd_cleanservice(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return
    arg = (command.args or "").strip().lower()
    if arg not in ("on", "off"):
        await message.reply("Shunday yozing: /cleanservice on yoki /cleanservice off")
        return
    await db.ensure_chat(message.chat.id, message.chat.title)
    await db.update_chat_setting(message.chat.id, clean_service=1 if arg == "on" else 0)
    await message.reply(texts.CLEAN_SERVICE_ON if arg == "on" else texts.CLEAN_SERVICE_OFF)


@router.message(Command("captcha"))
async def cmd_captcha(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return
    arg = (command.args or "").strip().lower()
    if arg not in ("on", "off"):
        await message.reply("Shunday yozing: /captcha on yoki /captcha off")
        return
    await db.ensure_chat(message.chat.id, message.chat.title)
    await db.update_chat_setting(message.chat.id, captcha_enabled=1 if arg == "on" else 0)
    await message.reply(texts.CAPTCHA_ON if arg == "on" else texts.CAPTCHA_OFF)


# ------------------------------------------------------------------
# Yangi a'zo qo'shilishi / chiqishi
# ------------------------------------------------------------------


@router.message(F.new_chat_members)
async def on_new_members(message: Message, bot: Bot) -> None:
    await db.ensure_chat(message.chat.id, message.chat.title)
    settings_row = await db.get_chat_settings(message.chat.id)
    clean_service = bool(settings_row["clean_service"]) if settings_row else False
    captcha_enabled = bool(settings_row["captcha_enabled"]) if settings_row else False
    welcome_text = (
        settings_row["welcome_text"] if settings_row and settings_row["welcome_text"] else None
    )

    join_message_id = message.message_id
    fed_id = await db.get_chat_federation(message.chat.id)

    for member in message.new_chat_members:
        if member.is_bot:
            continue

        # Federatsiya (premium funksiya): agar bu odam federatsiyaning
        # boshqa guruhida banlangan bo'lsa, shu yerga qo'shilishi bilanoq
        # avtomatik chiqarib yuboramiz.
        if fed_id:
            fed_ban_row = await db.is_fed_banned(fed_id, member.id)
            if fed_ban_row:
                try:
                    await bot.ban_chat_member(message.chat.id, member.id)
                except Exception:
                    pass
                continue

        mention = mention_html(member.id, member.full_name)

        if captcha_enabled:
            try:
                await bot.restrict_chat_member(
                    message.chat.id, member.id, permissions=_RESTRICTED_PERMISSIONS
                )
            except Exception:
                pass
            prompt = await message.answer(
                texts.CAPTCHA_PROMPT.format(mention=mention, seconds=_CAPTCHA_TIMEOUT_SEC),
                reply_markup=_captcha_keyboard(member.id),
            )
            await db.add_pending_captcha(
                chat_id=message.chat.id,
                user_id=member.id,
                join_message_id=join_message_id,
                prompt_message_id=prompt.message_id,
                expires_at=time.time() + _CAPTCHA_TIMEOUT_SEC,
            )
        else:
            text = welcome_text.format(mention=mention) if welcome_text else texts.DEFAULT_WELCOME.format(mention=mention)
            await message.answer(text)

    if clean_service:
        try:
            await message.delete()
        except Exception:
            pass


@router.message(F.left_chat_member)
async def on_left_member(message: Message, bot: Bot) -> None:
    await db.ensure_chat(message.chat.id, message.chat.title)
    settings_row = await db.get_chat_settings(message.chat.id)
    clean_service = bool(settings_row["clean_service"]) if settings_row else False
    goodbye_text = (
        settings_row["goodbye_text"] if settings_row and settings_row["goodbye_text"] else None
    )

    member = message.left_chat_member
    if member and not member.is_bot:
        mention = mention_html(member.id, member.full_name)
        text = goodbye_text.format(mention=mention) if goodbye_text else texts.DEFAULT_GOODBYE.format(mention=mention)
        await message.answer(text)

    if clean_service:
        try:
            await message.delete()
        except Exception:
            pass


# ------------------------------------------------------------------
# Captcha tugmasi
# ------------------------------------------------------------------


@router.callback_query(F.data.startswith("captcha:"))
async def on_captcha_button(callback: CallbackQuery, bot: Bot) -> None:
    _, raw_user_id = callback.data.split(":", maxsplit=1)
    expected_user_id = int(raw_user_id)

    if not callback.from_user or callback.from_user.id != expected_user_id:
        await callback.answer(texts.CAPTCHA_WRONG_USER, show_alert=True)
        return

    chat_id = callback.message.chat.id if callback.message else None
    if chat_id is None:
        await callback.answer()
        return

    pending = await db.pop_pending_captcha(chat_id, expected_user_id)
    try:
        await bot.restrict_chat_member(
            chat_id, expected_user_id, permissions=_FULL_PERMISSIONS
        )
    except Exception:
        pass

    mention = mention_html(expected_user_id, callback.from_user.full_name)
    if callback.message:
        try:
            await callback.message.edit_text(texts.CAPTCHA_PASSED.format(mention=mention))
        except Exception:
            pass

    settings_row = await db.get_chat_settings(chat_id)
    welcome_text = (
        settings_row["welcome_text"] if settings_row and settings_row["welcome_text"] else None
    )
    text = (
        welcome_text.format(mention=mention)
        if welcome_text
        else texts.DEFAULT_WELCOME.format(mention=mention)
    )
    await bot.send_message(chat_id, text)
    await callback.answer()


async def sweep_expired_captchas(bot: Bot) -> None:
    """
    APScheduler orqali muntazam chaqiriladi: vaqti o'tgan captcha'larni
    topib, o'sha odamlarni guruhdan chiqarib yuboradi.
    """
    now = time.time()
    expired = await db.get_expired_captchas(now)
    for row in expired:
        chat_id = row["chat_id"]
        user_id = row["user_id"]
        await db.pop_pending_captcha(chat_id, user_id)
        try:
            await bot.ban_chat_member(chat_id, user_id)
            await bot.unban_chat_member(chat_id, user_id, only_if_banned=True)
        except Exception:
            pass
        if row["prompt_message_id"]:
            try:
                await bot.delete_message(chat_id, row["prompt_message_id"])
            except Exception:
                pass
        try:
            mention = mention_html(user_id, "foydalanuvchi")
            await bot.send_message(chat_id, texts.CAPTCHA_FAILED_KICK.format(mention=mention))
        except Exception:
            pass


# ------------------------------------------------------------------
# Join request - avtomatik qabul qilish
# ------------------------------------------------------------------


@router.chat_join_request()
async def on_join_request(request: ChatJoinRequest, bot: Bot) -> None:
    try:
        await bot.approve_chat_join_request(request.chat.id, request.from_user.id)
    except Exception:
        return
    mention = mention_html(request.from_user.id, request.from_user.full_name)
    try:
        await bot.send_message(
            request.chat.id, texts.JOIN_REQUEST_ACCEPTED_LOG.format(mention=mention)
        )
    except Exception:
        pass
