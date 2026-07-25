"""
ACHI BOT - DM boshqarish paneli.

MUHIM YO'NALISH O'ZGARISHI (foydalanuvchi so'roviga ko'ra): guruh
sozlamalari endi guruh ICHIDA buyruq yozib emas, balki botning
SHAXSIY CHATIDA (DM) inline tugmalar orqali boshqariladi. Guruh
ichidagi eski buyruqlar (/lock, /setwelcome va h.k.) HAM ishlashda
davom etadi (orqaga moslik uchun, ayrim adminlar buyruqni afzal
ko'rishi mumkin) - lekin ASOSIY, TAVSIYA ETILGAN yo'l endi shu DM
panel.

MUHIM TELEGRAM CHEKLOVI (aylanib o'tib bo'lmaydi): bot hech qachon
biror foydalanuvchiga BIRINCHI bo'lib DM yoza olmaydi - foydalanuvchi
avval botga shaxsan "/start" bosgan/yozgan bo'lishi SHART. Shu sabab:
- Agar admin botga hali umuman yozmagan bo'lsa, "onboarding" xabari
  (handlers/greetings.py'dagi my_chat_member handleri) yetib bormaydi -
  bu holda guruh ichida "DM orqali sozlash uchun menga shaxsan yozing"
  degan signal beriladi.
- Panelning o'zi ham faqat botga yozgan (start bosgan) adminlar uchun
  ishlaydi - bu Telegram platformasining o'zgarmas qoidasi.

Callback-data sxemasi (64 bayt chegarasiga sig'ishi uchun qisqa kodlar):
  p:l                          - guruhlar ro'yxati
  p:g:<cid>                    - guruh asosiy menyusi
  p:lk:<cid>                   - qulflar menyusi
  p:lk:<cid>:<type>            - qulf turini yoqish/o'chirish
  p:gr:<cid>                   - salomlashish/captcha menyusi
  p:gr:<cid>:cap|aa|cs         - captcha/autoapprove/cleanservice toggle
  p:gr:<cid>:sw|sg             - welcome/goodbye matnini o'zgartirish (FSM)
  p:ft:<cid>                   - filtrlar ro'yxati
  p:ft:<cid>:add                - yangi filtr qo'shish (FSM)
  p:ft:<cid>:rm:<trigger>       - filtrni o'chirish
  p:nt:<cid>                   - eslatmalar ro'yxati
  p:nt:<cid>:add / :rm:<name>   - eslatma qo'shish/o'chirish
  p:ps:<cid>                    - personal buyruqlar ro'yxati
  p:ps:<cid>:add / :rm:<name>   - personal qo'shish/o'chirish
  p:rl:<cid>                    - qoidalarni ko'rish/o'zgartirish
  p:pr:<cid>                    - premium holati/xarid
  p:pr:<cid>:30d|life           - premium xarid (DM'da invoice)
  p:ai:<cid>                    - AI moderatsiya yoqish/o'chirish
  p:rp:<cid>                    - hisobot menyusi
  p:rp:<cid>:txt|pdf|csv:<per>  - hisobotni tayyorlab DM'ga yuborish
  p:fd:<cid>                    - federatsiya holati
  p:ad:<cid>                    - admin vositalari (adminlar ro'yxati)
"""
from __future__ import annotations

import time

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    ChatMemberUpdated,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

import texts
from config import is_super_admin, settings
from database import db
from states import PanelFSM
from utils import format_timestamp, is_chat_admin

router = Router(name="panel")

_PERIODS = (("soat", "1 soat"), ("kun", "bugun"), ("hafta", "1 hafta"))


# ------------------------------------------------------------------
# Umumiy yordamchilar
# ------------------------------------------------------------------


async def _verify_admin(bot: Bot, user_id: int, chat_id: int) -> bool:
    """
    DM'dan kelgan har bir callback uchun QAYTA tekshiramiz - foydalanuvchi
    o'sha guruhda HALI HAM admin ekanligini. Bu muhim, chunki DM sessiyasi
    guruh a'zoligi bilan bog'liq emas - agar admin o'zgartirilgan bo'lsa
    (masalan adminlikdan olingan bo'lsa), eski DM tugmalari orqali
    guruhni boshqarishni davom ettirmasligi kerak.
    """
    return await is_chat_admin(bot, chat_id, user_id)


async def _admin_group_list(bot: Bot, user_id: int) -> list[dict]:
    """Foydalanuvchi ADMIN bo'lgan barcha guruhlarni qaytaradi (bot
    ko'rgan guruhlar orasidan, har biri uchun jonli tekshiruv qilinadi)."""
    chats = await db.list_all_chats()
    result = []
    for row in chats:
        if await is_chat_admin(bot, row["chat_id"], user_id):
            result.append(dict(row))
    return result


def _back_row(chat_id: int) -> list[InlineKeyboardButton]:
    return [InlineKeyboardButton(text=texts.PANEL_BTN_BACK, callback_data=f"p:g:{chat_id}")]


def _to_list_row() -> list[InlineKeyboardButton]:
    return [InlineKeyboardButton(text=texts.PANEL_BTN_TO_LIST, callback_data="p:l")]


def _groups_keyboard(chats: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    now = time.time()
    for row in chats:
        is_premium = bool(row["premium_lifetime"]) or (
            row["premium_until"] and row["premium_until"] > now
        )
        mark = "* " if is_premium else ""
        title = row["chat_title"] or f"ID: {row['chat_id']}"
        rows.append(
            [InlineKeyboardButton(text=f"{mark}{title}"[:64], callback_data=f"p:g:{row['chat_id']}")]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _group_menu_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    def cb(code: str) -> str:
        return f"p:{code}:{chat_id}"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=texts.PANEL_BTN_LOCKS, callback_data=cb("lk")),
                InlineKeyboardButton(text=texts.PANEL_BTN_GREETINGS, callback_data=cb("gr")),
            ],
            [
                InlineKeyboardButton(text=texts.PANEL_BTN_FILTERS, callback_data=cb("ft")),
                InlineKeyboardButton(text=texts.PANEL_BTN_NOTES, callback_data=cb("nt")),
            ],
            [
                InlineKeyboardButton(text=texts.PANEL_BTN_PERSONAL, callback_data=cb("ps")),
                InlineKeyboardButton(text=texts.PANEL_BTN_RULES, callback_data=cb("rl")),
            ],
            [
                InlineKeyboardButton(text=texts.PANEL_BTN_PREMIUM, callback_data=cb("pr")),
                InlineKeyboardButton(text=texts.PANEL_BTN_AI_MOD, callback_data=cb("ai")),
            ],
            [
                InlineKeyboardButton(text=texts.PANEL_BTN_REPORTS, callback_data=cb("rp")),
                InlineKeyboardButton(text=texts.PANEL_BTN_FEDERATION, callback_data=cb("fd")),
            ],
            [InlineKeyboardButton(text=texts.PANEL_BTN_ADMIN_TOOLS, callback_data=cb("ad"))],
            _to_list_row(),
        ]
    )


async def _show_group_menu(callback: CallbackQuery, chat_id: int) -> None:
    row = await db.get_chat_settings(chat_id)
    title = (row["chat_title"] if row else None) or f"ID: {chat_id}"
    await callback.message.edit_text(
        texts.PANEL_GROUP_MENU_HEADER.format(title=title),
        reply_markup=_group_menu_keyboard(chat_id),
    )


# ------------------------------------------------------------------
# /start (deep-link) va /panel
# ------------------------------------------------------------------


async def cmd_start(message: Message, command: CommandObject, bot: Bot) -> None:
    payload = (command.args or "").strip()
    if payload.startswith("panel_") and message.chat.type == "private":
        raw_chat_id = payload[len("panel_"):]
        try:
            chat_id = int(raw_chat_id)
        except ValueError:
            await message.answer(texts.START)
            return
        if not message.from_user or not await _verify_admin(bot, message.from_user.id, chat_id):
            await message.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP)
            return
        row = await db.get_chat_settings(chat_id)
        title = (row["chat_title"] if row else None) or f"ID: {chat_id}"
        await message.answer(
            texts.PANEL_GROUP_MENU_HEADER.format(title=title),
            reply_markup=_group_menu_keyboard(chat_id),
        )
        return

    await message.answer(texts.START)


async def cmd_panel(message: Message, bot: Bot) -> None:
    if message.chat.type != "private":
        me = await bot.get_me()
        await message.reply(texts.PANEL_ONLY_DM.format(bot_username=f"@{me.username}"))
        return
    if not message.from_user:
        return
    chats = await _admin_group_list(bot, message.from_user.id)
    if not chats:
        await message.answer(texts.PANEL_NO_GROUPS)
        return
    await message.answer(texts.PANEL_PICK_GROUP, reply_markup=_groups_keyboard(chats))


# ------------------------------------------------------------------
# Guruhlar ro'yxatiga qaytish / guruh menyusi
# ------------------------------------------------------------------


@router.callback_query(F.data == "p:l")
async def on_back_to_list(callback: CallbackQuery, bot: Bot) -> None:
    if not callback.from_user or not callback.message:
        await callback.answer()
        return
    chats = await _admin_group_list(bot, callback.from_user.id)
    await callback.answer()
    if not chats:
        await callback.message.edit_text(texts.PANEL_NO_GROUPS)
        return
    await callback.message.edit_text(texts.PANEL_PICK_GROUP, reply_markup=_groups_keyboard(chats))


@router.callback_query(F.data.startswith("p:g:"))
async def on_group_menu(callback: CallbackQuery, bot: Bot) -> None:
    chat_id = int(callback.data.split(":")[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return
    await callback.answer()
    await _show_group_menu(callback, chat_id)


# ------------------------------------------------------------------
# Qulflar (Locks)
# ------------------------------------------------------------------

_LOCK_TYPES = ("link", "photo", "video", "sticker", "gif", "forward")


def _locks_keyboard(chat_id: int, active: set[str]) -> InlineKeyboardMarkup:
    rows = []
    for lock_type in _LOCK_TYPES:
        mark = "[x] " if lock_type in active else "[ ] "
        name = texts.LOCK_NAMES.get(lock_type, lock_type)
        rows.append(
            [InlineKeyboardButton(text=f"{mark}{name}", callback_data=f"p:lk:{chat_id}:{lock_type}")]
        )
    rows.append(_back_row(chat_id))
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data.startswith("p:lk:"))
async def on_locks_menu(callback: CallbackQuery, bot: Bot) -> None:
    parts = callback.data.split(":")
    chat_id = int(parts[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return

    if len(parts) == 4:
        # p:lk:<cid>:<type> - toggle
        lock_type = parts[3]
        if await db.is_locked(chat_id, lock_type):
            await db.unset_lock(chat_id, lock_type)
        else:
            await db.set_lock(chat_id, lock_type)

    active = set(await db.list_locks(chat_id))
    await callback.answer()
    await callback.message.edit_text(
        texts.PANEL_LOCKS_HEADER, reply_markup=_locks_keyboard(chat_id, active)
    )


# ------------------------------------------------------------------
# Salomlashish / Captcha / Autoapprove / Clean-service
# ------------------------------------------------------------------


def _greetings_keyboard(chat_id: int, row) -> InlineKeyboardMarkup:
    captcha_on = bool(row and row["captcha_enabled"])
    aa_on = bool(row and row["auto_approve_join"])
    cs_on = bool(row and row["clean_service"])

    def mark(v: bool) -> str:
        return "[x] " if v else "[ ] "

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=texts.PANEL_BTN_SET_WELCOME, callback_data=f"p:gr:{chat_id}:sw")],
            [InlineKeyboardButton(text=texts.PANEL_BTN_SET_GOODBYE, callback_data=f"p:gr:{chat_id}:sg")],
            [
                InlineKeyboardButton(
                    text=f"{mark(captcha_on)}{texts.PANEL_BTN_CAPTCHA}",
                    callback_data=f"p:gr:{chat_id}:cap",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"{mark(aa_on)}{texts.PANEL_BTN_AUTOAPPROVE}",
                    callback_data=f"p:gr:{chat_id}:aa",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"{mark(cs_on)}{texts.PANEL_BTN_CLEANSERVICE}",
                    callback_data=f"p:gr:{chat_id}:cs",
                )
            ],
            _back_row(chat_id),
        ]
    )


@router.callback_query(F.data.startswith("p:gr:"))
async def on_greetings_menu(callback: CallbackQuery, bot: Bot, state: FSMContext) -> None:
    parts = callback.data.split(":")
    chat_id = int(parts[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return

    action = parts[3] if len(parts) > 3 else None

    if action == "sw":
        await state.set_state(PanelFSM.waiting_text)
        await state.update_data(chat_id=chat_id, kind="welcome")
        await callback.answer()
        await callback.message.edit_text(texts.PANEL_ASK_WELCOME_TEXT)
        return
    if action == "sg":
        await state.set_state(PanelFSM.waiting_text)
        await state.update_data(chat_id=chat_id, kind="goodbye")
        await callback.answer()
        await callback.message.edit_text(texts.PANEL_ASK_GOODBYE_TEXT)
        return

    await db.ensure_chat(chat_id, None)
    if action == "cap":
        row = await db.get_chat_settings(chat_id)
        new_val = 0 if (row and row["captcha_enabled"]) else 1
        await db.update_chat_setting(chat_id, captcha_enabled=new_val)
    elif action == "aa":
        row = await db.get_chat_settings(chat_id)
        new_val = 0 if (row and row["auto_approve_join"]) else 1
        await db.update_chat_setting(chat_id, auto_approve_join=new_val)
    elif action == "cs":
        row = await db.get_chat_settings(chat_id)
        new_val = 0 if (row and row["clean_service"]) else 1
        await db.update_chat_setting(chat_id, clean_service=new_val)

    row = await db.get_chat_settings(chat_id)
    await callback.answer()
    await callback.message.edit_text(
        texts.PANEL_GREETINGS_HEADER, reply_markup=_greetings_keyboard(chat_id, row)
    )


# ------------------------------------------------------------------
# Filtrlar
# ------------------------------------------------------------------


def _filters_keyboard(chat_id: int, rows: list) -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text=f"- {r['trigger']}", callback_data=f"p:ft:{chat_id}:rm:{r['trigger']}")]
        for r in rows
    ]
    kb.append([InlineKeyboardButton(text=texts.PANEL_BTN_ADD_NEW, callback_data=f"p:ft:{chat_id}:add")])
    kb.append(_back_row(chat_id))
    return InlineKeyboardMarkup(inline_keyboard=kb)


@router.callback_query(F.data.startswith("p:ft:"))
async def on_filters_menu(callback: CallbackQuery, bot: Bot, state: FSMContext) -> None:
    parts = callback.data.split(":", maxsplit=4)
    chat_id = int(parts[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return

    action = parts[3] if len(parts) > 3 else None
    if action == "add":
        await state.set_state(PanelFSM.waiting_text)
        await state.update_data(chat_id=chat_id, kind="filter_add")
        await callback.answer()
        await callback.message.edit_text(texts.PANEL_ASK_FILTER)
        return
    if action == "rm" and len(parts) > 4:
        await db.remove_filter(chat_id, parts[4])
        await callback.answer(texts.PANEL_REMOVED_OK)

    rows = await db.list_filters(chat_id)
    if action is None:
        await callback.answer()
    await callback.message.edit_text(
        texts.PANEL_FILTERS_HEADER if rows else texts.PANEL_FILTERS_EMPTY,
        reply_markup=_filters_keyboard(chat_id, rows),
    )


# ------------------------------------------------------------------
# Eslatmalar (Notes)
# ------------------------------------------------------------------


def _notes_keyboard(chat_id: int, rows: list) -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text=f"#{r['name']}", callback_data=f"p:nt:{chat_id}:rm:{r['name']}")]
        for r in rows
    ]
    kb.append([InlineKeyboardButton(text=texts.PANEL_BTN_ADD_NEW, callback_data=f"p:nt:{chat_id}:add")])
    kb.append(_back_row(chat_id))
    return InlineKeyboardMarkup(inline_keyboard=kb)


@router.callback_query(F.data.startswith("p:nt:"))
async def on_notes_menu(callback: CallbackQuery, bot: Bot, state: FSMContext) -> None:
    parts = callback.data.split(":", maxsplit=4)
    chat_id = int(parts[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return

    action = parts[3] if len(parts) > 3 else None
    if action == "add":
        await state.set_state(PanelFSM.waiting_text)
        await state.update_data(chat_id=chat_id, kind="note_add")
        await callback.answer()
        await callback.message.edit_text(texts.PANEL_ASK_NOTE)
        return
    if action == "rm" and len(parts) > 4:
        await db.remove_note(chat_id, parts[4])
        await callback.answer(texts.PANEL_REMOVED_OK)

    rows = await db.list_notes(chat_id)
    if action is None:
        await callback.answer()
    await callback.message.edit_text(
        texts.PANEL_NOTES_HEADER if rows else texts.PANEL_NOTES_EMPTY,
        reply_markup=_notes_keyboard(chat_id, rows),
    )


# ------------------------------------------------------------------
# Personal (custom buyruqlar)
# ------------------------------------------------------------------


def _personal_keyboard(chat_id: int, rows: list) -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text=f"/{r['name']}", callback_data=f"p:ps:{chat_id}:rm:{r['name']}")]
        for r in rows
    ]
    kb.append([InlineKeyboardButton(text=texts.PANEL_BTN_ADD_NEW, callback_data=f"p:ps:{chat_id}:add")])
    kb.append(_back_row(chat_id))
    return InlineKeyboardMarkup(inline_keyboard=kb)


@router.callback_query(F.data.startswith("p:ps:"))
async def on_personal_menu(callback: CallbackQuery, bot: Bot, state: FSMContext) -> None:
    parts = callback.data.split(":", maxsplit=4)
    chat_id = int(parts[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return

    action = parts[3] if len(parts) > 3 else None
    if action == "add":
        await state.set_state(PanelFSM.waiting_text)
        await state.update_data(chat_id=chat_id, kind="personal_add")
        await callback.answer()
        await callback.message.edit_text(texts.PANEL_ASK_PERSONAL)
        return
    if action == "rm" and len(parts) > 4:
        await db.remove_custom_command(chat_id, parts[4])
        await callback.answer(texts.PANEL_REMOVED_OK)

    rows = await db.list_custom_commands(chat_id)
    if action is None:
        await callback.answer()
    await callback.message.edit_text(
        texts.PANEL_PERSONAL_HEADER if rows else texts.PANEL_PERSONAL_EMPTY,
        reply_markup=_personal_keyboard(chat_id, rows),
    )


# ------------------------------------------------------------------
# Qoidalar (Rules)
# ------------------------------------------------------------------


@router.callback_query(F.data.startswith("p:rl:"))
async def on_rules_menu(callback: CallbackQuery, bot: Bot, state: FSMContext) -> None:
    parts = callback.data.split(":")
    chat_id = int(parts[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return

    if len(parts) > 3 and parts[3] == "set":
        await state.set_state(PanelFSM.waiting_text)
        await state.update_data(chat_id=chat_id, kind="rules")
        await callback.answer()
        await callback.message.edit_text(texts.PANEL_ASK_RULES)
        return

    row = await db.get_chat_settings(chat_id)
    rules_text = row["rules_text"] if row and row["rules_text"] else texts.RULES_EMPTY
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=texts.PANEL_BTN_EDIT_RULES, callback_data=f"p:rl:{chat_id}:set")],
            _back_row(chat_id),
        ]
    )
    await callback.answer()
    await callback.message.edit_text(f"{texts.RULES_HEADER}{rules_text}", reply_markup=kb)


# ------------------------------------------------------------------
# Premium
# ------------------------------------------------------------------


@router.callback_query(F.data.startswith("p:pr:"))
async def on_premium_menu(callback: CallbackQuery, bot: Bot) -> None:
    from handlers.premium import _send_invoice  # aylanma import'ni oldini olish uchun shu yerda

    parts = callback.data.split(":")
    chat_id = int(parts[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return

    action = parts[3] if len(parts) > 3 else None
    if action in ("30d", "life"):
        await callback.answer()
        plan = "lifetime" if action == "life" else "30d"
        await _send_invoice(bot, callback.from_user.id, plan, target_group_chat_id=chat_id)
        return

    row = await db.get_chat_settings(chat_id)
    now = time.time()
    if is_super_admin(callback.from_user.id):
        status = texts.PREMIUM_STATUS_SUPERADMIN
        already = True
    elif row and row["premium_lifetime"]:
        status = texts.PREMIUM_STATUS_LIFETIME
        already = True
    elif row and row["premium_until"] and row["premium_until"] > now:
        status = texts.PREMIUM_STATUS_ACTIVE_UNTIL.format(
            date=format_timestamp(row["premium_until"], "%d.%m.%Y")
        )
        already = True
    else:
        status = texts.PREMIUM_STATUS_NONE
        already = False

    kb_rows = []
    if not already:
        kb_rows.append(
            [
                InlineKeyboardButton(
                    text=texts.PREMIUM_BUTTON_30D.format(price=settings.premium_30d_price_stars),
                    callback_data=f"p:pr:{chat_id}:30d",
                )
            ]
        )
        kb_rows.append(
            [
                InlineKeyboardButton(
                    text=texts.PREMIUM_BUTTON_LIFETIME.format(price=settings.premium_lifetime_price_stars),
                    callback_data=f"p:pr:{chat_id}:life",
                )
            ]
        )
    kb_rows.append(_back_row(chat_id))

    await callback.answer()
    await callback.message.edit_text(
        texts.PANEL_PREMIUM_HEADER.format(status=status),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows),
    )


# ------------------------------------------------------------------
# AI moderatsiya
# ------------------------------------------------------------------


@router.callback_query(F.data.startswith("p:ai:"))
async def on_ai_menu(callback: CallbackQuery, bot: Bot) -> None:
    chat_id = int(callback.data.split(":")[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return

    if not await db.is_chat_premium(chat_id):
        await callback.answer()
        await callback.message.edit_text(
            texts.AI_MODERATION_REQUIRES_PREMIUM,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[_back_row(chat_id)]),
        )
        return

    row = await db.get_chat_settings(chat_id)
    new_val = 0 if (row and row["ai_moderation_enabled"]) else 1
    await db.ensure_chat(chat_id, None)
    await db.update_chat_setting(chat_id, ai_moderation_enabled=new_val)

    mark = "[x] " if new_val else "[ ] "
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{mark}{texts.PANEL_BTN_AI_MOD}", callback_data=f"p:ai:{chat_id}")],
            _back_row(chat_id),
        ]
    )
    await callback.answer(texts.AI_MODERATION_ON if new_val else texts.AI_MODERATION_OFF)
    await callback.message.edit_text(texts.PANEL_AI_MOD_HEADER, reply_markup=kb)


# ------------------------------------------------------------------
# Hisobotlar (Reports)
# ------------------------------------------------------------------


def _reports_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    rows = []
    for period_key, period_label in _PERIODS:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{texts.PANEL_BTN_REPORT_TEXT} ({period_label})",
                    callback_data=f"p:rp:{chat_id}:txt:{period_key}",
                ),
                InlineKeyboardButton(
                    text=f"{texts.PANEL_BTN_REPORT_PDF} ({period_label})",
                    callback_data=f"p:rp:{chat_id}:pdf:{period_key}",
                ),
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=texts.PANEL_BTN_REPORT_CSV, callback_data=f"p:rp:{chat_id}:csv:hafta"
            )
        ]
    )
    rows.append(_back_row(chat_id))
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data.startswith("p:rp:"))
async def on_reports_menu(callback: CallbackQuery, bot: Bot) -> None:
    from handlers.report import (
        _period_bounds,
        build_text_report_chunks,
        generate_and_send_csv,
        generate_and_send_pdf,
    )

    parts = callback.data.split(":")
    chat_id = int(parts[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return

    if len(parts) < 5:
        await callback.answer()
        await callback.message.edit_text(
            texts.PANEL_REPORTS_HEADER, reply_markup=_reports_keyboard(chat_id)
        )
        return

    kind, period_key = parts[3], parts[4]
    bounds = _period_bounds(period_key) or (time.time() - 3600, "so'nggi 1 soat")
    since_ts, period_label = bounds
    row = await db.get_chat_settings(chat_id)
    chat_title = (row["chat_title"] if row else None) or f"ID: {chat_id}"
    dm_chat_id = callback.from_user.id

    await callback.answer(texts.PANEL_REPORT_PREPARING)

    if kind == "txt":
        from database import db as _db

        actions = await _db.get_actions_since(chat_id, since_ts)
        with_ai = await db.is_chat_premium(chat_id)
        chunks = await build_text_report_chunks(chat_title, actions, period_label, with_ai_summary=with_ai)
        for chunk in chunks:
            await bot.send_message(dm_chat_id, chunk)
    elif kind == "pdf":
        ok = await generate_and_send_pdf(
            bot, chat_id, chat_title, since_ts, period_label, send_to_chat_id=dm_chat_id
        )
        if not ok:
            await bot.send_message(dm_chat_id, texts.REPORT_EMPTY_PERIOD)
    elif kind == "csv":
        if not await db.is_chat_premium(chat_id):
            await bot.send_message(dm_chat_id, texts.PREMIUM_REQUIRED_EXPORT)
        else:
            ok = await generate_and_send_csv(
                bot, chat_id, chat_title, since_ts, period_label, send_to_chat_id=dm_chat_id
            )
            if not ok:
                await bot.send_message(dm_chat_id, texts.REPORT_EMPTY_PERIOD)


# ------------------------------------------------------------------
# Federatsiya
# ------------------------------------------------------------------


@router.callback_query(F.data.startswith("p:fd:"))
async def on_federation_menu(callback: CallbackQuery, bot: Bot) -> None:
    chat_id = int(callback.data.split(":")[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return

    fed_id = await db.get_chat_federation(chat_id)
    await callback.answer()
    if not fed_id:
        text = texts.PANEL_FEDERATION_NONE
    else:
        fed = await db.get_federation(fed_id)
        chats = await db.get_federation_chats(fed_id)
        bans_count = await db.count_fed_bans(fed_id)
        text = texts.FED_INFO.format(
            name=fed["name"] if fed else "?",
            fed_id=fed_id,
            chats_count=len(chats),
            bans_count=bans_count,
        )
    await callback.message.edit_text(
        text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[_back_row(chat_id)])
    )


# ------------------------------------------------------------------
# Admin vositalari
# ------------------------------------------------------------------


@router.callback_query(F.data.startswith("p:ad:"))
async def on_admin_tools_menu(callback: CallbackQuery, bot: Bot) -> None:
    from aiogram.exceptions import TelegramAPIError
    from aiogram.types import ChatMemberOwner

    from utils import mention_html

    chat_id = int(callback.data.split(":")[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return

    await callback.answer()
    try:
        admins = await bot.get_chat_administrators(chat_id)
    except TelegramAPIError:
        admins = []

    real_admins = [a for a in admins if not a.user.is_bot]
    if not real_admins:
        text = texts.STAFF_EMPTY
    else:
        lines = [texts.PANEL_ADMIN_TOOLS_HEADER]
        for a in real_admins:
            mention = mention_html(a.user.id, a.user.full_name)
            if isinstance(a, ChatMemberOwner):
                lines.append(texts.STAFF_OWNER_LINE.format(mention=mention))
            else:
                lines.append(texts.STAFF_ADMIN_LINE.format(mention=mention))
        text = "\n".join(lines)

    await callback.message.edit_text(
        text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[_back_row(chat_id)])
    )


# ------------------------------------------------------------------
# FSM - matn kiritish (welcome/goodbye/rules/filter/note/personal)
# ------------------------------------------------------------------


@router.message(StateFilter(PanelFSM.waiting_text))
async def on_panel_text_input(message: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    chat_id = data.get("chat_id")
    kind = data.get("kind")
    await state.clear()

    if not chat_id or not kind or not message.from_user:
        return
    if not await _verify_admin(bot, message.from_user.id, chat_id):
        await message.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP)
        return

    text_value = (message.text or "").strip()
    if not text_value:
        await message.answer(texts.PANEL_TEXT_EMPTY)
        return

    await db.ensure_chat(chat_id, None)

    if kind == "welcome":
        await db.update_chat_setting(chat_id, welcome_text=text_value)
        await message.answer(texts.WELCOME_SET)
    elif kind == "goodbye":
        await db.update_chat_setting(chat_id, goodbye_text=text_value)
        await message.answer(texts.GOODBYE_SET)
    elif kind == "rules":
        await db.update_chat_setting(chat_id, rules_text=text_value)
        await message.answer(texts.RULES_SET)
    elif kind == "filter_add":
        if "|" not in text_value:
            await message.answer(texts.FILTER_USAGE)
            return
        trigger, reply = text_value.split("|", maxsplit=1)
        trigger, reply = trigger.strip(), reply.strip()
        if not trigger or not reply:
            await message.answer(texts.FILTER_USAGE)
            return
        await db.set_filter(chat_id, trigger, reply)
        await message.answer(texts.FILTER_SAVED.format(trigger=trigger))
    elif kind == "note_add":
        parts = text_value.split(maxsplit=1)
        if len(parts) < 2:
            await message.answer(texts.NOTE_USAGE)
            return
        await db.save_note(chat_id, parts[0], parts[1])
        await message.answer(texts.NOTE_SAVED.format(name=parts[0]))
    elif kind == "personal_add":
        from handlers.content import RESERVED_COMMAND_NAMES

        parts = text_value.split(maxsplit=1)
        if len(parts) < 2:
            await message.answer(texts.PERSONAL_USAGE)
            return
        name = parts[0].lstrip("/").lower()
        if not name.isascii() or not name.replace("_", "").isalnum():
            await message.answer(texts.PERSONAL_BAD_NAME)
            return
        if name in RESERVED_COMMAND_NAMES:
            await message.answer(texts.PERSONAL_NAME_RESERVED.format(name=name))
            return
        await db.add_custom_command(chat_id, name, parts[1], message.from_user.id)
        await message.answer(texts.PERSONAL_ADDED.format(name=name))


# ------------------------------------------------------------------
# Onboarding - bot guruhga admin qilib qo'shilganda
# ------------------------------------------------------------------
#
# MUHIM TELEGRAM CHEKLOVI: bot hech qachon biror foydalanuvchiga
# BIRINCHI bo'lib DM yoza olmaydi - o'sha foydalanuvchi avval botga
# shaxsan "/start" bosgan/yozgan bo'lishi SHART (bu Telegram
# platformasining o'zgarmas qoidasi, aylanib o'tib bo'lmaydi). Shu
# sabab quyidagi mantiq IKKI BOSQICHLI:
#   1. Avval DM'ga yozib ko'ramiz (agar admin avval botga yozgan
#      bo'lsa - ishlaydi).
#   2. Agar DM ketmasa (TelegramForbiddenError/BadRequest - "user
#      hasn't started the bot"), guruhning O'ZIGA signal qoldiramiz:
#      "DM orqali sozlash uchun menga shaxsan yozing" + deep-link tugma.


def _deep_link_keyboard(bot_username: str, chat_id: int) -> InlineKeyboardMarkup:
    url = f"https://t.me/{bot_username}?start=panel_{chat_id}"
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=texts.PANEL_OPEN_BUTTON, url=url)]]
    )


@router.my_chat_member()
async def on_bot_membership_changed(event: ChatMemberUpdated, bot: Bot) -> None:
    if event.chat.type not in ("group", "supergroup"):
        return

    old_status = event.old_chat_member.status
    new_status = event.new_chat_member.status
    was_outside = old_status in ("left", "kicked")
    is_inside_now = new_status in ("member", "administrator")
    if not (was_outside and is_inside_now):
        return

    await db.ensure_chat(event.chat.id, event.chat.title)

    adder = event.from_user
    if not adder or adder.is_bot:
        return

    me = await bot.get_me()
    keyboard = _deep_link_keyboard(me.username, event.chat.id)

    dm_sent = False
    try:
        await bot.send_message(
            adder.id,
            texts.PANEL_ONBOARDING_DM.format(chat_title=event.chat.title or ""),
            reply_markup=keyboard,
        )
        dm_sent = True
    except TelegramAPIError:
        dm_sent = False

    if not dm_sent:
        try:
            await bot.send_message(
                event.chat.id,
                texts.PANEL_ONBOARDING_GROUP_FALLBACK.format(bot_username=me.username),
                reply_markup=keyboard,
            )
        except TelegramAPIError:
            pass
