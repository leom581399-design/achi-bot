"""
ACHI BOT - filter (avtomatik javob), notes (eslatmalar), rules (qoidalar)
va "personal" (so'z bo'yicha avtomatik o'chirish).
"""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

import texts
from config import settings
from database import db
from handlers.premium import is_premium_or_free
from utils import is_chat_admin

router = Router(name="content")


async def _guard_admin(message: Message, bot) -> bool:
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
# Filters
# ------------------------------------------------------------------


@router.message(Command("filter"))
async def cmd_filter(message: Message, command: CommandObject, bot) -> None:
    if not await _guard_admin(message, bot):
        return
    raw = command.args or ""
    if "|" not in raw:
        await message.reply(texts.FILTER_USAGE)
        return
    trigger, reply = raw.split("|", maxsplit=1)
    trigger = trigger.strip()
    reply = reply.strip()
    if not trigger or not reply:
        await message.reply(texts.FILTER_USAGE)
        return

    # Yangi filtr qo'shishdan oldin limitni tekshiramiz (mavjud filtrni
    # yangilash - ya'ni trigger allaqachon bor bo'lsa - cheklovga
    # tegmaydi, faqat yangi trigger qo'shish sanaladi).
    existing = await db.get_filter(message.chat.id, trigger)
    if existing is None:
        premium = await is_premium_or_free(message.chat.id, message.from_user.id)
        if not premium:
            count = await db.count_filters(message.chat.id)
            if count >= settings.free_filter_limit:
                await message.reply(
                    texts.PREMIUM_REQUIRED_FILTER_LIMIT.format(
                        limit=settings.free_filter_limit
                    )
                )
                return

    await db.set_filter(message.chat.id, trigger, reply)
    await message.reply(texts.FILTER_SAVED.format(trigger=trigger))


@router.message(Command("stopfilter"))
async def cmd_stopfilter(message: Message, command: CommandObject, bot) -> None:
    if not await _guard_admin(message, bot):
        return
    trigger = (command.args or "").strip()
    if not trigger:
        await message.reply("Qaysi filtrni o'chirishni yozing: /stopfilter so'z")
        return
    removed = await db.remove_filter(message.chat.id, trigger)
    await message.reply(
        texts.FILTER_REMOVED.format(trigger=trigger) if removed else texts.FILTER_NOT_FOUND
    )


@router.message(Command("filters"))
async def cmd_filters(message: Message) -> None:
    if message.chat.type not in ("group", "supergroup"):
        await message.reply(texts.ONLY_IN_GROUP)
        return
    rows = await db.list_filters(message.chat.id)
    if not rows:
        await message.reply(f"{texts.FILTERS_HEADER}\n{texts.FILTERS_EMPTY}")
        return
    names = "\n".join(f"- {r['trigger']}" for r in rows)
    await message.reply(f"{texts.FILTERS_HEADER}\n{names}")


@router.message(
    F.chat.type.in_({"group", "supergroup"}),
    F.text,
    ~F.text.startswith("/"),
)
async def apply_filters_and_notes(message: Message, bot) -> None:
    """
    Guruhdagi oddiy matnli xabarlarni tekshiradi:
    1. Avval "personal" so'zlarga qarshi tekshiradi (agar admin bo'lmagan
       kishi taqiqlangan so'zni yozsa - o'chiriladi, boshqa hech narsa
       qilinmaydi).
    2. Agar "#nom" bilan boshlansa - eslatmani qidiradi.
    3. Aks holda - saqlangan filtrlar bilan solishtiradi.

    (Bularning barchasi bitta handlerda, chunki aiogram'da bir update
    uchun odatda faqat bitta handler ishlaydi - shu sabab ularni ajratib
    qo'ysak, biri ikkinchisini "yutib qo'yardi".)
    """
    if not message.text:
        return

    text = message.text.strip()
    lowered = text.lower()

    # 1) "Personal" so'zlar - admin bo'lmagan kishi taqiqlangan so'zni
    # ishlatsa xabarni o'chiramiz. Admin o'zi bu so'zlarni yoza olishi
    # kerak (masalan tushuntirish/muhokama uchun), shu sabab avval
    # tekshiramiz.
    if message.from_user and not await is_chat_admin(
        bot, message.chat.id, message.from_user.id
    ):
        personal_words = await db.list_personal_words(message.chat.id)
        for word in personal_words:
            if word in lowered:
                try:
                    await message.delete()
                except Exception:
                    pass
                return

    if text.startswith("#") and len(text) > 1:
        name = text.lstrip("#").split()[0]
        content = await db.get_note(message.chat.id, name)
        if content:
            await message.reply(content)
            return

    all_filters = await db.all_filters(message.chat.id)
    if not all_filters:
        return
    for row in all_filters:
        trigger = row["trigger"]
        if trigger in lowered:
            await message.reply(row["reply"])
            return


# ------------------------------------------------------------------
# Personal - so'z bo'yicha avtomatik o'chirish
# ------------------------------------------------------------------


@router.message(Command("personal"))
async def cmd_personal(message: Message, command: CommandObject, bot) -> None:
    if not await _guard_admin(message, bot):
        return
    word = (command.args or "").strip().lower()
    if not word:
        await message.reply(texts.PERSONAL_USAGE)
        return
    await db.add_personal_word(message.chat.id, word, message.from_user.id)
    await message.reply(texts.PERSONAL_ADDED.format(word=word))


@router.message(Command("stoppersonal"))
async def cmd_stoppersonal(message: Message, command: CommandObject, bot) -> None:
    if not await _guard_admin(message, bot):
        return
    word = (command.args or "").strip().lower()
    if not word:
        await message.reply(texts.PERSONAL_USAGE)
        return
    removed = await db.remove_personal_word(message.chat.id, word)
    await message.reply(
        texts.PERSONAL_REMOVED.format(word=word) if removed else texts.PERSONAL_NOT_FOUND
    )


@router.message(Command("personallist"))
async def cmd_personallist(message: Message) -> None:
    if message.chat.type not in ("group", "supergroup"):
        await message.reply(texts.ONLY_IN_GROUP)
        return
    words = await db.list_personal_words(message.chat.id)
    if not words:
        await message.reply(texts.PERSONAL_LIST_EMPTY)
        return
    lines = "\n".join(f"- {w}" for w in words)
    await message.reply(f"{texts.PERSONAL_LIST_HEADER}\n{lines}")


# ------------------------------------------------------------------
# Notes
# ------------------------------------------------------------------


@router.message(Command("save"))
async def cmd_save(message: Message, command: CommandObject, bot) -> None:
    if not await _guard_admin(message, bot):
        return
    raw = (command.args or "").strip()
    parts = raw.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply(texts.NOTE_USAGE)
        return
    name, content = parts[0], parts[1]

    existing = await db.get_note(message.chat.id, name)
    if existing is None:
        premium = await is_premium_or_free(message.chat.id, message.from_user.id)
        if not premium:
            count = await db.count_notes(message.chat.id)
            if count >= settings.free_note_limit:
                await message.reply(
                    texts.PREMIUM_REQUIRED_NOTE_LIMIT.format(
                        limit=settings.free_note_limit
                    )
                )
                return

    await db.save_note(message.chat.id, name, content)
    await message.reply(texts.NOTE_SAVED.format(name=name))


@router.message(Command("get"))
async def cmd_get(message: Message, command: CommandObject) -> None:
    if message.chat.type not in ("group", "supergroup"):
        await message.reply(texts.ONLY_IN_GROUP)
        return
    name = (command.args or "").strip()
    if not name:
        await message.reply(texts.NOTE_USAGE)
        return
    content = await db.get_note(message.chat.id, name)
    if not content:
        await message.reply(texts.NOTE_NOT_FOUND)
        return
    await message.reply(content)


@router.message(Command("notes"))
async def cmd_notes(message: Message) -> None:
    if message.chat.type not in ("group", "supergroup"):
        await message.reply(texts.ONLY_IN_GROUP)
        return
    rows = await db.list_notes(message.chat.id)
    if not rows:
        await message.reply(texts.NOTES_EMPTY)
        return
    names = "\n".join(f"- #{r['name']}" for r in rows)
    await message.reply(f"{texts.NOTES_HEADER}\n{names}")


@router.message(Command("delnote"))
async def cmd_delnote(message: Message, command: CommandObject, bot) -> None:
    if not await _guard_admin(message, bot):
        return
    name = (command.args or "").strip()
    removed = await db.remove_note(message.chat.id, name)
    await message.reply(
        texts.NOTE_REMOVED.format(name=name) if removed else texts.NOTE_NOT_FOUND
    )


# ------------------------------------------------------------------
# Rules
# ------------------------------------------------------------------


@router.message(Command("setrules"))
async def cmd_setrules(message: Message, command: CommandObject, bot) -> None:
    if not await _guard_admin(message, bot):
        return
    text = (command.args or "").strip()
    if not text:
        await message.reply("Qoidalar matnini yozing: /setrules matn")
        return
    await db.ensure_chat(message.chat.id, message.chat.title)
    await db.update_chat_setting(message.chat.id, rules_text=text)
    await message.reply(texts.RULES_SET)


@router.message(Command("rules"))
async def cmd_rules(message: Message) -> None:
    if message.chat.type not in ("group", "supergroup"):
        await message.reply(texts.ONLY_IN_GROUP)
        return
    settings_row = await db.get_chat_settings(message.chat.id)
    rules_text = settings_row["rules_text"] if settings_row else None
    if not rules_text:
        await message.reply(texts.RULES_EMPTY)
        return
    await message.reply(f"{texts.RULES_HEADER}{rules_text}")
