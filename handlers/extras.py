"""
ACHI BOT - qo'shimcha BEPUL funksiyalar.

Bu modulda 18 ta BEPUL (barcha guruhlar uchun, premium talab qilinmaydi)
funksiya joylashgan:

1. /language - guruh tilini o'zbek/rus qilib o'zgartirish
2. /pin - xabarni pin qilish (reply qilib)
3. /unpin - pin'ni bekor qilish
4. /purge - reply qilingan xabardan hozirgi xabargacha bo'lgan hammasini o'chirish
5. /id - guruh va foydalanuvchi ID'sini ko'rsatish
6. /mywarns - o'zining ogohlantirishlarini ko'rish (istalgan a'zo uchun)
7. /slowmode - "yumshoq" tezlik cheklovi (soniyada bir marta yozish)
8. /badword, /unbadword, /badwords - taqiqlangan so'zlar ro'yxati
9. /stats - guruh statistikasi (bugun/hafta bo'yicha amallar soni)
10. /topwarns - eng ko'p ogohlantirilgan a'zolar reytingi
11. /invite - guruhning taklif havolasini olish
12. /feedback - bot egasiga fikr-mulohaza yuborish
13. /cancel - DM panelidagi FSM (matn kutish) holatini bekor qilish
"""
from __future__ import annotations

import time

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import texts
from config import is_super_admin, settings
from database import db
from states import PanelFSM
from utils import format_timestamp, is_chat_admin, mention_html, resolve_target, user_display_name

router = Router(name="extras")


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
# 1. /language - til o'zgartirish (guruh ichidan ham mumkin)
# ------------------------------------------------------------------


@router.message(Command("language"))
async def cmd_language(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return
    arg = (command.args or "").strip().lower()
    if arg not in ("uz", "ru"):
        await message.reply(texts.LANGUAGE_USAGE)
        return
    await db.set_chat_language(message.chat.id, arg)
    await message.reply(texts.LANGUAGE_SET_UZ if arg == "uz" else texts.LANGUAGE_SET_RU)


# ------------------------------------------------------------------
# 2-3. /pin, /unpin
# ------------------------------------------------------------------


@router.message(Command("pin"))
async def cmd_pin(message: Message, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return
    if not message.reply_to_message:
        await message.reply(texts.PIN_USAGE)
        return
    try:
        await bot.pin_chat_message(message.chat.id, message.reply_to_message.message_id)
    except TelegramAPIError:
        await message.reply(texts.BOT_NOT_ADMIN)
        return
    await message.reply(texts.PIN_DONE)


@router.message(Command("unpin"))
async def cmd_unpin(message: Message, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return
    try:
        if message.reply_to_message:
            await bot.unpin_chat_message(message.chat.id, message.reply_to_message.message_id)
        else:
            await bot.unpin_all_chat_messages(message.chat.id)
    except TelegramAPIError:
        await message.reply(texts.BOT_NOT_ADMIN)
        return
    await message.reply(texts.UNPIN_DONE)


# ------------------------------------------------------------------
# 4. /purge - reply qilingan xabardan hozirgacha bo'lganini tozalash
# ------------------------------------------------------------------

_PURGE_MAX_MESSAGES = 200


@router.message(Command("purge"))
async def cmd_purge(message: Message, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return
    if not message.reply_to_message:
        await message.reply(texts.PURGE_USAGE)
        return

    start_id = message.reply_to_message.message_id
    end_id = message.message_id
    if end_id <= start_id:
        await message.reply(texts.PURGE_USAGE)
        return

    ids = list(range(start_id, end_id + 1))
    if len(ids) > _PURGE_MAX_MESSAGES:
        await message.reply(texts.PURGE_TOO_MANY.format(limit=_PURGE_MAX_MESSAGES))
        return

    deleted = 0
    try:
        await bot.delete_messages(message.chat.id, ids)
        deleted = len(ids)
    except TelegramAPIError:
        # Ba'zi Bot API versiyalarida delete_messages ishlamasa, birma-bir
        # o'chirishga urinamiz (sekinroq, lekin ishonchli zaxira).
        for mid in ids:
            try:
                await bot.delete_message(message.chat.id, mid)
                deleted += 1
            except TelegramAPIError:
                continue

    if deleted:
        await message.answer(texts.PURGE_DONE.format(count=deleted))
    else:
        await message.answer(texts.BOT_NOT_ADMIN)


# ------------------------------------------------------------------
# 5. /id
# ------------------------------------------------------------------


@router.message(Command("id"))
async def cmd_id(message: Message) -> None:
    target_id = message.from_user.id if message.from_user else "?"
    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id
    await message.reply(
        texts.ID_RESULT.format(chat_id=message.chat.id, user_id=target_id)
    )


# ------------------------------------------------------------------
# 6. /mywarns - istalgan a'zo o'zining ogohlantirishini ko'radi
# ------------------------------------------------------------------


@router.message(Command("mywarns"))
async def cmd_mywarns(message: Message) -> None:
    if message.chat.type not in ("group", "supergroup") or not message.from_user:
        await message.reply(texts.ONLY_IN_GROUP)
        return
    count = await db.count_warns(message.chat.id, message.from_user.id)
    await message.reply(
        texts.MYWARNS_RESULT.format(count=count, max_warns=settings.max_warns)
    )


# ------------------------------------------------------------------
# 7. /slowmode - "yumshoq" tezlik cheklovi
# ------------------------------------------------------------------


@router.message(Command("slowmode"))
async def cmd_slowmode(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return
    arg = (command.args or "").strip().lower()
    if arg in ("off", "0"):
        await db.ensure_chat(message.chat.id, message.chat.title)
        await db.update_chat_setting(message.chat.id, slowmode_seconds=0)
        await message.reply(texts.SLOWMODE_OFF)
        return
    if not arg.isdigit() or int(arg) <= 0:
        await message.reply(texts.SLOWMODE_USAGE)
        return
    seconds = int(arg)
    await db.ensure_chat(message.chat.id, message.chat.title)
    await db.update_chat_setting(message.chat.id, slowmode_seconds=seconds)
    await message.reply(texts.SLOWMODE_ON.format(seconds=seconds))


# ------------------------------------------------------------------
# 8. Bad words (taqiqlangan so'zlar)
# ------------------------------------------------------------------


@router.message(Command("badword"))
async def cmd_badword(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return
    word = (command.args or "").strip().lower()
    if not word:
        await message.reply(texts.BADWORD_USAGE)
        return
    await db.add_bad_word(message.chat.id, word, message.from_user.id)
    await message.reply(texts.BADWORD_ADDED.format(word=word))


@router.message(Command("unbadword"))
async def cmd_unbadword(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return
    word = (command.args or "").strip().lower()
    removed = await db.remove_bad_word(message.chat.id, word)
    await message.reply(
        texts.BADWORD_REMOVED.format(word=word) if removed else texts.BADWORD_NOT_FOUND
    )


@router.message(Command("badwords"))
async def cmd_badwords(message: Message) -> None:
    if message.chat.type not in ("group", "supergroup"):
        await message.reply(texts.ONLY_IN_GROUP)
        return
    words = await db.list_bad_words(message.chat.id)
    if not words:
        await message.reply(texts.BADWORDS_EMPTY)
        return
    await message.reply(f"{texts.BADWORDS_HEADER}\n" + "\n".join(f"- {w}" for w in words))


async def _check_bad_word(message: Message, bot: Bot):
    if not message.text or not message.from_user or message.from_user.is_bot:
        return False
    if message.chat.type not in ("group", "supergroup"):
        return False
    if await is_chat_admin(bot, message.chat.id, message.from_user.id):
        return False
    words = await db.list_bad_words(message.chat.id)
    if not words:
        return False
    lowered = message.text.lower()
    for word in words:
        if word in lowered:
            return {"bad_word": word}
    return False


@router.message(_check_bad_word)
async def enforce_bad_words(message: Message, bad_word: str) -> None:
    try:
        await message.delete()
    except Exception:
        return
    try:
        mention = mention_html(message.from_user.id, message.from_user.full_name)
        await message.answer(texts.BADWORD_REMOVED_NOTICE.format(mention=mention))
    except Exception:
        pass


# ------------------------------------------------------------------
# 9-10. /stats, /topwarns
# ------------------------------------------------------------------


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    if message.chat.type not in ("group", "supergroup"):
        await message.reply(texts.ONLY_IN_GROUP)
        return
    since_week = time.time() - 7 * 86400
    counts = await db.count_actions_by_type_since(message.chat.id, since_week)
    members_count = await db.count_known_members(message.chat.id)
    await message.reply(
        texts.STATS_RESULT.format(
            members=members_count,
            ban=counts.get("ban", 0) + counts.get("tban", 0),
            mute=counts.get("mute", 0) + counts.get("tmute", 0),
            warn=counts.get("warn", 0),
            kick=counts.get("kick", 0),
        )
    )


@router.message(Command("topwarns"))
async def cmd_topwarns(message: Message) -> None:
    if message.chat.type not in ("group", "supergroup"):
        await message.reply(texts.ONLY_IN_GROUP)
        return
    since_month = time.time() - 30 * 86400
    rows = await db.top_warned_users_since(message.chat.id, since_month, limit=5)
    if not rows:
        await message.reply(texts.TOPWARNS_EMPTY)
        return
    lines = [texts.TOPWARNS_HEADER]
    for i, row in enumerate(rows, start=1):
        name = row["target_username"] and f"@{row['target_username']}" or row["target_name"] or str(row["target_id"])
        lines.append(f"{i}. {name} — {row['c']}")
    await message.reply("\n".join(lines))


# ------------------------------------------------------------------
# GroupHelpBot'dan ilhomlanib: /top - eng faol a'zolar reytingi
# ------------------------------------------------------------------


@router.message(Command("top"))
async def cmd_top(message: Message) -> None:
    """
    Guruhda kim ko'p yozganini ko'rsatadi (xabar soni bo'yicha reyting).
    /topwarns'dan farqi: bu ijobiy faollik reytingi, jazoga aloqasi yo'q.
    """
    if message.chat.type not in ("group", "supergroup"):
        await message.reply(texts.ONLY_IN_GROUP)
        return
    rows = await db.top_active_members(message.chat.id, limit=10)
    if not rows:
        await message.reply(texts.TOP_EMPTY)
        return
    lines = [texts.TOP_HEADER]
    medals = {1: "1.", 2: "2.", 3: "3."}
    for i, row in enumerate(rows, start=1):
        pos_label = medals.get(i, f"{i}.")
        name = f"@{row['username']}" if row["username"] else (row["full_name"] or str(row["user_id"]))
        lines.append(texts.TOP_ITEM.format(pos=pos_label, name=name, count=row["message_count"]))
    await message.reply("\n".join(lines))


# ------------------------------------------------------------------
# GroupHelpBot'dan ilhomlanib: /setfloodmode - flood limitiga
# yetganda nima qilinishi (standart: mute)
# ------------------------------------------------------------------

_VALID_FLOOD_ACTIONS = ("warn", "mute", "kick", "ban", "tban", "tmute")


@router.message(Command("setfloodmode"))
async def cmd_setfloodmode(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return
    action = (command.args or "").strip().lower()
    if action not in _VALID_FLOOD_ACTIONS:
        await message.reply(texts.SETFLOODMODE_USAGE)
        return
    await db.ensure_chat(message.chat.id, message.chat.title)
    await db.update_chat_setting(message.chat.id, flood_action=action)
    await message.reply(texts.SETFLOODMODE_SET.format(action=action))


# ------------------------------------------------------------------
# 11. /invite
# ------------------------------------------------------------------


@router.message(Command("invite"))
async def cmd_invite(message: Message, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return
    try:
        chat = await bot.get_chat(message.chat.id)
        link = chat.invite_link
        if not link:
            link = await bot.export_chat_invite_link(message.chat.id)
    except TelegramAPIError:
        await message.reply(texts.BOT_NOT_ADMIN)
        return
    await message.reply(texts.INVITE_RESULT.format(link=link))


# ------------------------------------------------------------------
# 12. /feedback - bot egasiga fikr yuborish
# ------------------------------------------------------------------


@router.message(Command("feedback"))
async def cmd_feedback(message: Message, command: CommandObject, bot: Bot) -> None:
    text = (command.args or "").strip()
    if not text:
        await message.reply(texts.FEEDBACK_USAGE)
        return
    sender = user_display_name(message.from_user) if message.from_user else "?"
    chat_label = message.chat.title or str(message.chat.id)
    delivered = False
    for admin_id in settings.super_admins:
        try:
            await bot.send_message(
                admin_id, texts.FEEDBACK_FORWARDED.format(sender=sender, chat=chat_label, text=text)
            )
            delivered = True
        except TelegramAPIError:
            continue
    if delivered:
        await message.reply(texts.FEEDBACK_SENT)
    else:
        await message.reply(texts.FEEDBACK_FAILED)


# ------------------------------------------------------------------
# 13. /cancel - DM panel FSM holatini bekor qilish
# ------------------------------------------------------------------


@router.message(Command("cancel"), StateFilter(PanelFSM.waiting_text))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(texts.PANEL_CANCELLED)


# ------------------------------------------------------------------
# Slowmode ("yumshoq" tezlik cheklovi) - amaliy tekshiruv
# ------------------------------------------------------------------
#
# Telegram'ning o'z rasmiy "slow mode" funksiyasi bot API orqali
# o'rnatilmaydi (faqat odam admin UI orqali sozlay oladi), shu sabab
# bot o'zi kuzatib, chegaradan tezroq yozilgan xabarlarni o'chiradi -
# bu "yumshoq" (approximate) slowmode, lekin amaliyotda bir xil natija
# beradi: guruh tinchroq bo'ladi.
_last_message_time: dict[tuple[int, int], float] = {}


async def _check_slowmode(message: Message, bot: Bot):
    if not message.text or not message.from_user or message.from_user.is_bot:
        return False
    if message.chat.type not in ("group", "supergroup"):
        return False
    if await is_chat_admin(bot, message.chat.id, message.from_user.id):
        return False

    row = await db.get_chat_settings(message.chat.id)
    seconds = row["slowmode_seconds"] if row else 0
    if not seconds:
        return False

    key = (message.chat.id, message.from_user.id)
    now = time.time()
    last = _last_message_time.get(key)
    _last_message_time[key] = now
    if last and now - last < seconds:
        return {"wait_seconds": seconds}
    return False


@router.message(_check_slowmode)
async def enforce_slowmode(message: Message, wait_seconds: int) -> None:
    try:
        await message.delete()
    except Exception:
        pass
