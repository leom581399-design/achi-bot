"""
ACHI BOT - filter (avtomatik javob), notes (eslatmalar), rules (qoidalar)
va "personal" (o'zingiz yaratadigan maxsus buyruq).
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

# Botning o'zi ishlatadigan barcha buyruq nomlari - "personal" orqali
# yaratilgan custom buyruq shu nomlar bilan TO'QNASHMASLIGI kerak
# (aks holda, masalan /personal ban deb yozilsa, /ban buyrug'i butunlay
# ishlamay qoladi). Ro'yxat butun loyihadagi barcha @router.message(
# Command("...")) chaqiruvlaridan yig'ilgan.
RESERVED_COMMAND_NAMES = frozenset(
    {
        "start", "help",
        "ban", "tban", "unban", "mute", "tmute", "unmute", "kick",
        "warn", "unwarn", "warns",
        "lock", "unlock", "locks",
        "setwelcome", "setgoodbye", "cleanservice", "captcha", "autoapprove",
        "filter", "stopfilter", "filters",
        "personal", "stoppersonal", "personallist",
        "save", "get", "notes", "delnote",
        "setrules", "rules",
        "r", "report", "exportcsv",
        "premium", "grantpremium", "broadcast", "premiumber",
        "fnew", "fjoin", "fleave", "finfo", "fban", "funban", "fed", "federation",
        "adminber", "adminol", "tag", "staff", "achi", "info",
    }
)


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
    1. Agar "#nom" bilan boshlansa - eslatmani qidiradi.
    2. Aks holda - saqlangan filtrlar bilan solishtiradi.

    ("/nom" bilan boshlangan "personal" (custom) buyruqlar bu handlerga
    umuman kelmaydi - ular pastdagi `handle_custom_command` orqali,
    barcha real buyruqlar (Command filtrlari) tekshirilib bo'lgandan
    KEYIN ishlaydi, chunki bu handler ~F.text.startswith("/") bilan
    "/" belgisi bilan boshlangan xabarlarni ataylab chetlab o'tadi.)
    """
    if not message.text:
        return

    text = message.text.strip()
    lowered = text.lower()

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
# Personal - o'zingiz yaratadigan maxsus buyruq
# ------------------------------------------------------------------
#
# Masalan: admin "Lorem ipsum" degan xabarga reply qilib
# "/personal salom Xush kelibsiz, aka!" deb yozsa (yoki shunchaki
# "/personal salom Xush kelibsiz, aka!" deb to'g'ridan-to'g'ri yozsa),
# guruhda keyinchalik kimdur "/salom" deb yozganda bot "Xush kelibsiz,
# aka!" deb javob beradi.


@router.message(Command("personal"))
async def cmd_personal(message: Message, command: CommandObject, bot) -> None:
    if not await _guard_admin(message, bot):
        return

    raw = (command.args or "").strip()
    parts = raw.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply(texts.PERSONAL_USAGE)
        return

    name, content = parts[0].lstrip("/").lower(), parts[1]

    if not name.isascii() or not name.replace("_", "").isalnum():
        await message.reply(texts.PERSONAL_BAD_NAME)
        return

    if name in RESERVED_COMMAND_NAMES:
        await message.reply(texts.PERSONAL_NAME_RESERVED.format(name=name))
        return

    await db.add_custom_command(message.chat.id, name, content, message.from_user.id)
    await message.reply(texts.PERSONAL_ADDED.format(name=name))


@router.message(Command("stoppersonal"))
async def cmd_stoppersonal(message: Message, command: CommandObject, bot) -> None:
    if not await _guard_admin(message, bot):
        return
    name = (command.args or "").strip().lstrip("/").lower()
    if not name:
        await message.reply(texts.PERSONAL_USAGE)
        return
    removed = await db.remove_custom_command(message.chat.id, name)
    await message.reply(
        texts.PERSONAL_REMOVED.format(name=name) if removed else texts.PERSONAL_NOT_FOUND
    )


@router.message(Command("personallist"))
async def cmd_personallist(message: Message) -> None:
    if message.chat.type not in ("group", "supergroup"):
        await message.reply(texts.ONLY_IN_GROUP)
        return
    rows = await db.list_custom_commands(message.chat.id)
    if not rows:
        await message.reply(texts.PERSONAL_LIST_EMPTY)
        return
    lines = "\n".join(f"- /{r['name']}" for r in rows)
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


# ------------------------------------------------------------------
# "Personal" custom buyruqlarni ishlatish - FALLBACK ROUTER
# ------------------------------------------------------------------
#
# MUHIM: bu ALOHIDA router (`content.router`ning o'zi emas)! Sababi:
# main.py'da routerlar ro'yxatga olinish TARTIBIDA tekshiriladi, va
# content.router report.router'dan OLDIN turadi. Agar shu handler
# content.router ICHIDA bo'lganida, u "/r", "/report", "/exportcsv"
# kabi HAQIQIY buyruqlarni ular tekshirilishidan oldin "yutib qo'yardi"
# (chunki F.text.startswith("/") "/" bilan boshlangan HAR QANDAY
# xabarga mos keladi). Shu sabab bu handler alohida `fallback_router`
# ichida va main.py'da BARCHA boshqa routerlardan KEYIN (eng oxirida)
# ro'yxatga olinishi SHART - shundagina haqiqiy buyruqlar birinchi
# navbatda ishlab, faqat ULARGA mos kelmagan "/" bilan boshlangan
# xabarlar shu yerga (custom buyruqni qidirishga) yetib keladi.
fallback_router = Router(name="content_fallback")


@fallback_router.message(F.chat.type.in_({"group", "supergroup"}), F.text.startswith("/"))
async def handle_custom_command(message: Message) -> None:
    if not message.text:
        return
    name = message.text.strip().split()[0].lstrip("/").split("@")[0].lower()
    if not name:
        return
    content = await db.get_custom_command(message.chat.id, name)
    if content:
        await message.reply(content)
