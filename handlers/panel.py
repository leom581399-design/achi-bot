"""
ACHI BOT - DM boshqarish paneli.

MUHIM YO'NALISH O'ZGARISHI (foydalanuvchi so'roviga ko'ra): guruh
sozlamalari endi guruh ICHIDA buyruq yozib emas, balki botning
SHAXSIY CHATIDA (DM) inline tugmalar orqali boshqariladi. Guruh
ichidagi eski buyruqlar HAM ishlashda davom etadi (orqaga moslik
uchun) - lekin ASOSIY, TAVSIYA ETILGAN yo'l endi shu DM panel.

MENYU TUZILISHI (foydalanuvchi "chunarsiz" degan shikoyatidan keyin
qayta qurilgan - endi 5 mantiqiy bo'limga guruhlangan, bitta yassi
6-qatorli ro'yxat emas):
  Asosiy menyu
    -> Moderatsiya      (qulflar, taqiqlangan so'zlar, tezlik
                          cheklovi, ogohlantirish limiti/muddati,
                          flood chegarasi, anti-raid, tungi rejim,
                          havola oq ro'yxati, matn-captcha)
    -> Sozlamalar        (salomlashish/captcha/autoapprove/
                          cleanservice, qoidalar, til, avto-pin,
                          silent rejim)
    -> Filtr va eslatma   (filtrlar, eslatmalar, personal buyruqlar)
    -> Premium markazi    (premium holati/xarid, aqlli moderatsiya,
                          VIP, moderatorlar, rejalashtirilgan xabar,
                          avto-o'chirish, kunlik hisobot, zaxira)
    -> Boshqalar          (hisobot, federatsiya, adminlar,
                          statistika, taklif havolasi)

TIL: har bir guruh o'z tilini (o'zbek/rus) tanlaydi - shu sabab
BARCHA matn chiqarishlar `i18n.tr_sync(lang, KEY, **kwargs)` orqali
ishlaydi, to'g'ridan-to'g'ri `texts.KEY` emas.

MUHIM TELEGRAM CHEKLOVI (aylanib o'tib bo'lmaydi): bot hech qachon
biror foydalanuvchiga BIRINCHI bo'lib DM yoza olmaydi - foydalanuvchi
avval botga shaxsan "/start" bosgan/yozgan bo'lishi SHART.

Callback-data sxemasi (64 bayt chegarasiga sig'ishi uchun qisqa kodlar):
  p:l                        - guruhlar ro'yxati
  p:g:<cid>                  - asosiy menyu
  p:mo:<cid>                 - Moderatsiya bo'limi
  p:se:<cid>                 - Sozlamalar bo'limi
  p:co:<cid>                 - Filtr va eslatma bo'limi
  p:pc:<cid>                 - Premium markazi bo'limi
  p:ot:<cid>                 - Boshqalar bo'limi
  p:lk:<cid>[:<type>]        - qulflar
  p:bw:<cid>[:add|:rm:<w>]   - taqiqlangan so'zlar
  p:sm:<cid>[:set]           - tezlik cheklovi
  p:wa:<cid>[:ban|:mute]     - ogohlantirish limiti
  p:fl:<cid>[:set]           - flood chegarasi (premium)
  p:ar:<cid>[:set]           - anti-raid (premium)
  p:nm:<cid>[:set]           - tungi rejim (premium)
  p:lw:<cid>[:add|:rm:<d>]   - havola oq ro'yxati (premium)
  p:we:<cid>[:set]           - ogohlantirish muddati (premium)
  p:tc:<cid>[:set]           - matn-captcha (premium)
  p:gr:<cid>[:cap|aa|cs|sw|sg] - salomlashish
  p:lang:<cid>[:uz|:ru]      - til
  p:ap:<cid>                 - avto-pin (premium)
  p:sl:<cid>                 - silent rejim (premium)
  p:rl:<cid>[:set]           - qoidalar
  p:ft:<cid>[:add|:rm:<t>]   - filtrlar
  p:nt:<cid>[:add|:rm:<n>]   - eslatmalar
  p:ps:<cid>[:add|:rm:<n>]   - personal buyruqlar
  p:pr:<cid>[:30d|:life]     - premium holati/xarid
  p:ai:<cid>                 - aqlli moderatsiya (premium)
  p:vip:<cid>[:add|:rm:<u>]  - VIP (premium)
  p:mod:<cid>[:add|:rm:<u>]  - moderatorlar (premium)
  p:sch:<cid>[:add|:rm:<i>]  - rejalashtirilgan xabar (premium)
  p:adt:<cid>[:set]          - avto-o'chirish (premium)
  p:dr:<cid>[:set]           - kunlik hisobot (premium)
  p:bk:<cid>                 - zaxira nusxa (premium)
  p:rp:<cid>[:txt|pdf|csv:<per>] - hisobot
  p:fd:<cid>                 - federatsiya
  p:ad:<cid>                 - admin vositalari
  p:st:<cid>                 - statistika
  p:iv:<cid>                 - taklif havolasi
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
from handlers.premium import is_premium_or_free
from i18n import get_lang, tr_sync
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
    o'sha guruhda HALI HAM admin ekanligini.
    """
    return await is_chat_admin(bot, chat_id, user_id)


async def _admin_group_list(bot: Bot, user_id: int) -> list[dict]:
    chats = await db.list_all_chats()
    result = []
    for row in chats:
        if await is_chat_admin(bot, row["chat_id"], user_id):
            result.append(dict(row))
    return result


def _back_row(chat_id: int, lang: str, to: str = "g") -> list[InlineKeyboardButton]:
    return [
        InlineKeyboardButton(
            text=tr_sync(lang, "PANEL_BTN_BACK"), callback_data=f"p:{to}:{chat_id}"
        )
    ]


def _to_list_row(lang: str) -> list[InlineKeyboardButton]:
    return [InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_TO_LIST"), callback_data="p:l")]


def _on_off(lang: str, value: bool) -> str:
    return tr_sync(lang, "PANEL_STATUS_ON") if value else tr_sync(lang, "PANEL_STATUS_OFF")


def _mark(v: bool) -> str:
    return "[x] " if v else "[ ] "


async def _resolve_id_from_text(chat_id: int, text_value: str) -> int | None:
    """
    DM panelida (reply konteksti bo'lmagan holatda) matn orqali
    foydalanuvchini aniqlaydi - @username (bot ko'rgan a'zolar
    ro'yxatidan) yoki to'g'ridan-to'g'ri raqamli ID.
    """
    text_value = text_value.strip()
    if text_value.startswith("@") and len(text_value) > 1:
        row = await db.get_known_member_by_username(chat_id, text_value.lstrip("@"))
        return row["user_id"] if row else None
    stripped = text_value.lstrip("-")
    if stripped.isdigit() and stripped:
        return int(text_value)
    return None


def _groups_keyboard(chats: list[dict], lang: str) -> InlineKeyboardMarkup:
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


def _main_menu_keyboard(chat_id: int, lang: str) -> InlineKeyboardMarkup:
    def cb(code: str) -> str:
        return f"p:{code}:{chat_id}"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_MODERATION_MENU"), callback_data=cb("mo")),
                InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_SETTINGS_MENU"), callback_data=cb("se")),
            ],
            [
                InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_CONTENT_MENU"), callback_data=cb("co")),
                InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_PREMIUM_CENTER_MENU"), callback_data=cb("pc")),
            ],
            [InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_OTHER_MENU"), callback_data=cb("ot"))],
            _to_list_row(lang),
        ]
    )


async def _show_main_menu(callback: CallbackQuery, chat_id: int, lang: str) -> None:
    row = await db.get_chat_settings(chat_id)
    title = (row["chat_title"] if row else None) or f"ID: {chat_id}"
    is_premium = await db.is_chat_premium(chat_id)
    premium_line = tr_sync(lang, "PANEL_PREMIUM_LINE_ACTIVE" if is_premium else "PANEL_PREMIUM_LINE_NONE")
    lang_name = "O'zbekcha" if lang == "uz" else "Русский"
    await callback.message.edit_text(
        tr_sync(lang, "PANEL_MAIN_MENU_HEADER", title=title, premium_line=premium_line, language=lang_name),
        reply_markup=_main_menu_keyboard(chat_id, lang),
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
        lang = await get_lang(chat_id)
        row = await db.get_chat_settings(chat_id)
        title = (row["chat_title"] if row else None) or f"ID: {chat_id}"
        is_premium = await db.is_chat_premium(chat_id)
        premium_line = tr_sync(lang, "PANEL_PREMIUM_LINE_ACTIVE" if is_premium else "PANEL_PREMIUM_LINE_NONE")
        lang_name = "O'zbekcha" if lang == "uz" else "Русский"
        await message.answer(
            tr_sync(lang, "PANEL_MAIN_MENU_HEADER", title=title, premium_line=premium_line, language=lang_name),
            reply_markup=_main_menu_keyboard(chat_id, lang),
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
    await message.answer(texts.PANEL_PICK_GROUP, reply_markup=_groups_keyboard(chats, "uz"))


# ------------------------------------------------------------------
# Guruhlar ro'yxati / Asosiy menyu
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
    await callback.message.edit_text(texts.PANEL_PICK_GROUP, reply_markup=_groups_keyboard(chats, "uz"))


@router.callback_query(F.data.startswith("p:g:"))
async def on_main_menu(callback: CallbackQuery, bot: Bot) -> None:
    chat_id = int(callback.data.split(":")[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return
    lang = await get_lang(chat_id)
    await callback.answer()
    await _show_main_menu(callback, chat_id, lang)


# ------------------------------------------------------------------
# Bo'lim menyulari (Moderatsiya / Sozlamalar / Filtr-eslatma /
# Premium markazi / Boshqalar)
# ------------------------------------------------------------------


def _moderation_menu_keyboard(chat_id: int, lang: str) -> InlineKeyboardMarkup:
    def cb(code: str) -> str:
        return f"p:{code}:{chat_id}"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_LOCKS"), callback_data=cb("lk")),
                InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_BADWORDS"), callback_data=cb("bw")),
            ],
            [
                InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_SLOWMODE"), callback_data=cb("sm")),
                InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_WARNACTION"), callback_data=cb("wa")),
            ],
            [
                InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_FLOODLIMIT"), callback_data=cb("fl")),
                InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_ANTIRAID"), callback_data=cb("ar")),
            ],
            [
                InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_NIGHTMODE"), callback_data=cb("nm")),
                InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_LINKWHITELIST"), callback_data=cb("lw")),
            ],
            [
                InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_WARNEXPIRY"), callback_data=cb("we")),
                InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_TEXTCAPTCHA"), callback_data=cb("tc")),
            ],
            _back_row(chat_id, lang),
        ]
    )


@router.callback_query(F.data.startswith("p:mo:"))
async def on_moderation_menu(callback: CallbackQuery, bot: Bot) -> None:
    chat_id = int(callback.data.split(":")[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return
    lang = await get_lang(chat_id)
    await callback.answer()
    await callback.message.edit_text(
        tr_sync(lang, "PANEL_MODERATION_MENU_HEADER"),
        reply_markup=_moderation_menu_keyboard(chat_id, lang),
    )


def _settings_menu_keyboard(chat_id: int, lang: str) -> InlineKeyboardMarkup:
    def cb(code: str) -> str:
        return f"p:{code}:{chat_id}"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_GREETINGS"), callback_data=cb("gr"))],
            [InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_RULES"), callback_data=cb("rl"))],
            [InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_LANGUAGE"), callback_data=cb("lang"))],
            [
                InlineKeyboardButton(text="Avto pin" if lang == "uz" else "Авто-закреп", callback_data=cb("ap")),
                InlineKeyboardButton(text="Silent rejim" if lang == "uz" else "Тихий режим", callback_data=cb("sl")),
            ],
            _back_row(chat_id, lang),
        ]
    )


@router.callback_query(F.data.startswith("p:se:"))
async def on_settings_menu(callback: CallbackQuery, bot: Bot) -> None:
    chat_id = int(callback.data.split(":")[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return
    lang = await get_lang(chat_id)
    await callback.answer()
    await callback.message.edit_text(
        tr_sync(lang, "PANEL_SETTINGS_MENU_HEADER"),
        reply_markup=_settings_menu_keyboard(chat_id, lang),
    )


def _content_menu_keyboard(chat_id: int, lang: str) -> InlineKeyboardMarkup:
    def cb(code: str) -> str:
        return f"p:{code}:{chat_id}"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_FILTERS"), callback_data=cb("ft")),
                InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_NOTES"), callback_data=cb("nt")),
            ],
            [InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_PERSONAL"), callback_data=cb("ps"))],
            _back_row(chat_id, lang),
        ]
    )


@router.callback_query(F.data.startswith("p:co:"))
async def on_content_menu(callback: CallbackQuery, bot: Bot) -> None:
    chat_id = int(callback.data.split(":")[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return
    lang = await get_lang(chat_id)
    await callback.answer()
    await callback.message.edit_text(
        tr_sync(lang, "PANEL_CONTENT_MENU_HEADER"),
        reply_markup=_content_menu_keyboard(chat_id, lang),
    )


def _premium_center_keyboard(chat_id: int, lang: str) -> InlineKeyboardMarkup:
    def cb(code: str) -> str:
        return f"p:{code}:{chat_id}"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_PREMIUM"), callback_data=cb("pr"))],
            [
                InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_AI_MOD"), callback_data=cb("ai")),
                InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_VIP"), callback_data=cb("vip")),
            ],
            [
                InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_MODERATORS"), callback_data=cb("mod")),
                InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_SCHEDULE"), callback_data=cb("sch")),
            ],
            [
                InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_AUTODELETE"), callback_data=cb("adt")),
                InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_DAILYREPORT"), callback_data=cb("dr")),
            ],
            [InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_BACKUP"), callback_data=cb("bk"))],
            _back_row(chat_id, lang),
        ]
    )


@router.callback_query(F.data.startswith("p:pc:"))
async def on_premium_center_menu(callback: CallbackQuery, bot: Bot) -> None:
    chat_id = int(callback.data.split(":")[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return
    lang = await get_lang(chat_id)
    is_premium = await db.is_chat_premium(chat_id)
    status = tr_sync(lang, "PANEL_PREMIUM_LINE_ACTIVE" if is_premium else "PANEL_PREMIUM_LINE_NONE")
    await callback.answer()
    await callback.message.edit_text(
        tr_sync(lang, "PANEL_PREMIUM_CENTER_HEADER", status=status),
        reply_markup=_premium_center_keyboard(chat_id, lang),
    )


def _other_menu_keyboard(chat_id: int, lang: str) -> InlineKeyboardMarkup:
    def cb(code: str) -> str:
        return f"p:{code}:{chat_id}"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_REPORTS"), callback_data=cb("rp")),
                InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_FEDERATION"), callback_data=cb("fd")),
            ],
            [
                InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_ADMIN_TOOLS"), callback_data=cb("ad")),
                InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_STATS"), callback_data=cb("st")),
            ],
            [InlineKeyboardButton(text="Taklif havolasi" if lang == "uz" else "Пригласительная ссылка", callback_data=cb("iv"))],
            _back_row(chat_id, lang),
        ]
    )


@router.callback_query(F.data.startswith("p:ot:"))
async def on_other_menu(callback: CallbackQuery, bot: Bot) -> None:
    chat_id = int(callback.data.split(":")[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return
    lang = await get_lang(chat_id)
    await callback.answer()
    await callback.message.edit_text(
        tr_sync(lang, "PANEL_OTHER_MENU_HEADER"),
        reply_markup=_other_menu_keyboard(chat_id, lang),
    )


# ------------------------------------------------------------------
# Til (Language)
# ------------------------------------------------------------------


def _language_keyboard(chat_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="O'zbekcha", callback_data=f"p:lang:{chat_id}:uz"),
                InlineKeyboardButton(text="Русский", callback_data=f"p:lang:{chat_id}:ru"),
            ],
            _back_row(chat_id, lang, to="se"),
        ]
    )


@router.callback_query(F.data.startswith("p:lang:"))
async def on_language_menu(callback: CallbackQuery, bot: Bot) -> None:
    parts = callback.data.split(":")
    chat_id = int(parts[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return

    if len(parts) > 3 and parts[3] in ("uz", "ru"):
        await db.set_chat_language(chat_id, parts[3])
        lang = parts[3]
        await callback.answer(tr_sync(lang, "PANEL_LANGUAGE_SET"))
    else:
        lang = await get_lang(chat_id)
        await callback.answer()

    await callback.message.edit_text(
        tr_sync(lang, "PANEL_LANGUAGE_HEADER"), reply_markup=_language_keyboard(chat_id, lang)
    )


# ------------------------------------------------------------------
# Qulflar (Locks)
# ------------------------------------------------------------------

_LOCK_TYPES = ("link", "photo", "video", "sticker", "gif", "forward")


def _locks_keyboard(chat_id: int, active: set[str], lang: str) -> InlineKeyboardMarkup:
    from i18n import get_lock_names

    names = get_lock_names(lang)
    rows = []
    for lock_type in _LOCK_TYPES:
        mark = _mark(lock_type in active)
        name = names.get(lock_type, lock_type)
        rows.append(
            [InlineKeyboardButton(text=f"{mark}{name}", callback_data=f"p:lk:{chat_id}:{lock_type}")]
        )
    rows.append(_back_row(chat_id, lang, to="mo"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data.startswith("p:lk:"))
async def on_locks_menu(callback: CallbackQuery, bot: Bot) -> None:
    parts = callback.data.split(":")
    chat_id = int(parts[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return

    if len(parts) == 4:
        lock_type = parts[3]
        if await db.is_locked(chat_id, lock_type):
            await db.unset_lock(chat_id, lock_type)
        else:
            await db.set_lock(chat_id, lock_type)

    lang = await get_lang(chat_id)
    active = set(await db.list_locks(chat_id))
    await callback.answer()
    await callback.message.edit_text(
        tr_sync(lang, "PANEL_LOCKS_HEADER"), reply_markup=_locks_keyboard(chat_id, active, lang)
    )


# ------------------------------------------------------------------
# Taqiqlangan so'zlar (Bad words)
# ------------------------------------------------------------------


def _badwords_keyboard(chat_id: int, words: list[str], lang: str) -> InlineKeyboardMarkup:
    kb = [[InlineKeyboardButton(text=f"- {w}", callback_data=f"p:bw:{chat_id}:rm:{w}")] for w in words]
    kb.append([InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_ADD_NEW"), callback_data=f"p:bw:{chat_id}:add")])
    kb.append(_back_row(chat_id, lang, to="mo"))
    return InlineKeyboardMarkup(inline_keyboard=kb)


@router.callback_query(F.data.startswith("p:bw:"))
async def on_badwords_menu(callback: CallbackQuery, bot: Bot, state: FSMContext) -> None:
    parts = callback.data.split(":", maxsplit=4)
    chat_id = int(parts[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return

    lang = await get_lang(chat_id)
    action = parts[3] if len(parts) > 3 else None
    if action == "add":
        await state.set_state(PanelFSM.waiting_text)
        await state.update_data(chat_id=chat_id, kind="badword_add")
        await callback.answer()
        await callback.message.edit_text(tr_sync(lang, "PANEL_ASK_BADWORD"))
        return
    if action == "rm" and len(parts) > 4:
        await db.remove_bad_word(chat_id, parts[4])
        await callback.answer(tr_sync(lang, "PANEL_REMOVED_OK"))

    words = await db.list_bad_words(chat_id)
    if action is None:
        await callback.answer()
    await callback.message.edit_text(
        tr_sync(lang, "PANEL_BADWORDS_HEADER") if words else tr_sync(lang, "PANEL_BADWORDS_EMPTY"),
        reply_markup=_badwords_keyboard(chat_id, words, lang),
    )


# ------------------------------------------------------------------
# Tezlik cheklovi (Slowmode)
# ------------------------------------------------------------------


@router.callback_query(F.data.startswith("p:sm:"))
async def on_slowmode_menu(callback: CallbackQuery, bot: Bot, state: FSMContext) -> None:
    parts = callback.data.split(":")
    chat_id = int(parts[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return
    lang = await get_lang(chat_id)

    if len(parts) > 3 and parts[3] == "set":
        await state.set_state(PanelFSM.waiting_text)
        await state.update_data(chat_id=chat_id, kind="slowmode_set")
        await callback.answer()
        await callback.message.edit_text(tr_sync(lang, "PANEL_ASK_SLOWMODE"))
        return

    row = await db.get_chat_settings(chat_id)
    seconds = row["slowmode_seconds"] if row else 0
    status = f"{seconds}s" if seconds else _on_off(lang, False)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_ADD_NEW"), callback_data=f"p:sm:{chat_id}:set")],
            _back_row(chat_id, lang, to="mo"),
        ]
    )
    await callback.answer()
    await callback.message.edit_text(tr_sync(lang, "PANEL_SLOWMODE_HEADER", status=status), reply_markup=kb)


# ------------------------------------------------------------------
# Ogohlantirish limiti (warn action: ban/mute)
# ------------------------------------------------------------------


@router.callback_query(F.data.startswith("p:wa:"))
async def on_warnaction_menu(callback: CallbackQuery, bot: Bot) -> None:
    parts = callback.data.split(":")
    chat_id = int(parts[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return
    lang = await get_lang(chat_id)

    if not await db.is_chat_premium(chat_id):
        await callback.answer()
        await callback.message.edit_text(
            tr_sync(lang, "WARNACTION_REQUIRES_PREMIUM"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[_back_row(chat_id, lang, to="mo")]),
        )
        return

    if len(parts) > 3 and parts[3] in ("ban", "mute"):
        await db.ensure_chat(chat_id, None)
        await db.update_chat_setting(chat_id, warn_action=parts[3])
        await callback.answer(tr_sync(lang, "WARNACTION_SET", action=parts[3]))

    row = await db.get_chat_settings(chat_id)
    current = (row["warn_action"] if row else "ban") or "ban"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{_mark(current == 'ban')}{tr_sync(lang, 'PANEL_BTN_WARNACTION_BAN')}",
                    callback_data=f"p:wa:{chat_id}:ban",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"{_mark(current == 'mute')}{tr_sync(lang, 'PANEL_BTN_WARNACTION_MUTE')}",
                    callback_data=f"p:wa:{chat_id}:mute",
                )
            ],
            _back_row(chat_id, lang, to="mo"),
        ]
    )
    await callback.answer()
    await callback.message.edit_text(tr_sync(lang, "PANEL_WARNACTION_HEADER"), reply_markup=kb)


# ------------------------------------------------------------------
# Flood chegarasi (premium)
# ------------------------------------------------------------------


@router.callback_query(F.data.startswith("p:fl:"))
async def on_floodlimit_menu(callback: CallbackQuery, bot: Bot, state: FSMContext) -> None:
    parts = callback.data.split(":")
    chat_id = int(parts[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return
    lang = await get_lang(chat_id)

    if not await db.is_chat_premium(chat_id):
        await callback.answer()
        await callback.message.edit_text(
            tr_sync(lang, "FLOODLIMIT_REQUIRES_PREMIUM"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[_back_row(chat_id, lang, to="mo")]),
        )
        return

    if len(parts) > 3 and parts[3] == "set":
        await state.set_state(PanelFSM.waiting_text)
        await state.update_data(chat_id=chat_id, kind="floodlimit_set")
        await callback.answer()
        await callback.message.edit_text(tr_sync(lang, "PANEL_ASK_FLOODLIMIT"))
        return

    row = await db.get_chat_settings(chat_id)
    if row and row["flood_limit_override"]:
        status = f"{row['flood_limit_override']} / {row['flood_window_override']}s"
    else:
        status = _on_off(lang, False)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_ADD_NEW"), callback_data=f"p:fl:{chat_id}:set")],
            _back_row(chat_id, lang, to="mo"),
        ]
    )
    await callback.answer()
    await callback.message.edit_text(tr_sync(lang, "PANEL_FLOODLIMIT_HEADER", status=status), reply_markup=kb)


# ------------------------------------------------------------------
# Anti-raid (premium)
# ------------------------------------------------------------------


@router.callback_query(F.data.startswith("p:ar:"))
async def on_antiraid_menu(callback: CallbackQuery, bot: Bot, state: FSMContext) -> None:
    parts = callback.data.split(":")
    chat_id = int(parts[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return
    lang = await get_lang(chat_id)

    if not await db.is_chat_premium(chat_id):
        await callback.answer()
        await callback.message.edit_text(
            tr_sync(lang, "ANTIRAID_REQUIRES_PREMIUM"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[_back_row(chat_id, lang, to="mo")]),
        )
        return

    if len(parts) > 3 and parts[3] == "set":
        await state.set_state(PanelFSM.waiting_text)
        await state.update_data(chat_id=chat_id, kind="antiraid_set")
        await callback.answer()
        await callback.message.edit_text(tr_sync(lang, "PANEL_ASK_ANTIRAID"))
        return

    row = await db.get_chat_settings(chat_id)
    if row and row["anti_raid_enabled"]:
        status = f"{row['anti_raid_threshold']} / {row['anti_raid_window_sec']}s"
    else:
        status = _on_off(lang, False)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_ADD_NEW"), callback_data=f"p:ar:{chat_id}:set")],
            _back_row(chat_id, lang, to="mo"),
        ]
    )
    await callback.answer()
    await callback.message.edit_text(tr_sync(lang, "PANEL_ANTIRAID_HEADER", status=status), reply_markup=kb)


# ------------------------------------------------------------------
# Tungi rejim (premium)
# ------------------------------------------------------------------


@router.callback_query(F.data.startswith("p:nm:"))
async def on_nightmode_menu(callback: CallbackQuery, bot: Bot, state: FSMContext) -> None:
    parts = callback.data.split(":")
    chat_id = int(parts[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return
    lang = await get_lang(chat_id)

    if not await db.is_chat_premium(chat_id):
        await callback.answer()
        await callback.message.edit_text(
            tr_sync(lang, "NIGHTMODE_REQUIRES_PREMIUM"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[_back_row(chat_id, lang, to="mo")]),
        )
        return

    if len(parts) > 3 and parts[3] == "set":
        await state.set_state(PanelFSM.waiting_text)
        await state.update_data(chat_id=chat_id, kind="nightmode_set")
        await callback.answer()
        await callback.message.edit_text(tr_sync(lang, "PANEL_ASK_NIGHTMODE"))
        return

    row = await db.get_chat_settings(chat_id)
    if row and row["night_mode_enabled"]:
        status = f"{row['night_start_hour']}-{row['night_end_hour']}"
    else:
        status = _on_off(lang, False)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_ADD_NEW"), callback_data=f"p:nm:{chat_id}:set")],
            _back_row(chat_id, lang, to="mo"),
        ]
    )
    await callback.answer()
    await callback.message.edit_text(tr_sync(lang, "PANEL_NIGHTMODE_HEADER", status=status), reply_markup=kb)


# ------------------------------------------------------------------
# Havola oq ro'yxati (premium)
# ------------------------------------------------------------------


def _linkwhitelist_keyboard(chat_id: int, domains: list[str], lang: str) -> InlineKeyboardMarkup:
    kb = [[InlineKeyboardButton(text=f"- {d}", callback_data=f"p:lw:{chat_id}:rm:{d}")] for d in domains]
    kb.append([InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_ADD_NEW"), callback_data=f"p:lw:{chat_id}:add")])
    kb.append(_back_row(chat_id, lang, to="mo"))
    return InlineKeyboardMarkup(inline_keyboard=kb)


@router.callback_query(F.data.startswith("p:lw:"))
async def on_linkwhitelist_menu(callback: CallbackQuery, bot: Bot, state: FSMContext) -> None:
    parts = callback.data.split(":", maxsplit=4)
    chat_id = int(parts[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return
    lang = await get_lang(chat_id)

    if not await db.is_chat_premium(chat_id):
        await callback.answer()
        await callback.message.edit_text(
            tr_sync(lang, "LINKWHITELIST_REQUIRES_PREMIUM"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[_back_row(chat_id, lang, to="mo")]),
        )
        return

    action = parts[3] if len(parts) > 3 else None
    if action == "add":
        await state.set_state(PanelFSM.waiting_text)
        await state.update_data(chat_id=chat_id, kind="linkwhitelist_add")
        await callback.answer()
        await callback.message.edit_text(tr_sync(lang, "PANEL_ASK_LINKWHITELIST"))
        return
    if action == "rm" and len(parts) > 4:
        await db.remove_whitelisted_domain(chat_id, parts[4])
        await callback.answer(tr_sync(lang, "PANEL_REMOVED_OK"))

    domains = await db.list_whitelisted_domains(chat_id)
    if action is None:
        await callback.answer()
    await callback.message.edit_text(
        tr_sync(lang, "PANEL_LINKWHITELIST_HEADER") if domains else tr_sync(lang, "PANEL_LINKWHITELIST_EMPTY"),
        reply_markup=_linkwhitelist_keyboard(chat_id, domains, lang),
    )


# ------------------------------------------------------------------
# Ogohlantirish muddati (premium)
# ------------------------------------------------------------------


@router.callback_query(F.data.startswith("p:we:"))
async def on_warnexpiry_menu(callback: CallbackQuery, bot: Bot, state: FSMContext) -> None:
    parts = callback.data.split(":")
    chat_id = int(parts[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return
    lang = await get_lang(chat_id)

    if not await db.is_chat_premium(chat_id):
        await callback.answer()
        await callback.message.edit_text(
            tr_sync(lang, "WARNEXPIRY_REQUIRES_PREMIUM"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[_back_row(chat_id, lang, to="mo")]),
        )
        return

    if len(parts) > 3 and parts[3] == "set":
        await state.set_state(PanelFSM.waiting_text)
        await state.update_data(chat_id=chat_id, kind="warnexpiry_set")
        await callback.answer()
        await callback.message.edit_text(tr_sync(lang, "PANEL_ASK_WARNEXPIRY"))
        return

    row = await db.get_chat_settings(chat_id)
    days = row["warn_expiry_days"] if row else 0
    status = f"{days} kun" if days else _on_off(lang, False)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_ADD_NEW"), callback_data=f"p:we:{chat_id}:set")],
            _back_row(chat_id, lang, to="mo"),
        ]
    )
    await callback.answer()
    await callback.message.edit_text(tr_sync(lang, "PANEL_WARNEXPIRY_HEADER", status=status), reply_markup=kb)


# ------------------------------------------------------------------
# Matn-captcha (premium)
# ------------------------------------------------------------------


@router.callback_query(F.data.startswith("p:tc:"))
async def on_textcaptcha_menu(callback: CallbackQuery, bot: Bot, state: FSMContext) -> None:
    parts = callback.data.split(":")
    chat_id = int(parts[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return
    lang = await get_lang(chat_id)

    if not await db.is_chat_premium(chat_id):
        await callback.answer()
        await callback.message.edit_text(
            tr_sync(lang, "TEXTCAPTCHA_REQUIRES_PREMIUM"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[_back_row(chat_id, lang, to="mo")]),
        )
        return

    if len(parts) > 3 and parts[3] == "set":
        await state.set_state(PanelFSM.waiting_text)
        await state.update_data(chat_id=chat_id, kind="textcaptcha_set")
        await callback.answer()
        await callback.message.edit_text(tr_sync(lang, "PANEL_ASK_TEXTCAPTCHA"))
        return

    row = await db.get_chat_settings(chat_id)
    status = row["text_captcha_question"] if row and row["text_captcha_question"] else _on_off(lang, False)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_ADD_NEW"), callback_data=f"p:tc:{chat_id}:set")],
            _back_row(chat_id, lang, to="mo"),
        ]
    )
    await callback.answer()
    await callback.message.edit_text(tr_sync(lang, "PANEL_TEXTCAPTCHA_HEADER", status=status), reply_markup=kb)


# ------------------------------------------------------------------
# Salomlashish / Captcha / Autoapprove / Clean-service / Welcome / Goodbye
# ------------------------------------------------------------------


def _greetings_keyboard(chat_id: int, row, lang: str) -> InlineKeyboardMarkup:
    captcha_on = bool(row and row["captcha_enabled"])
    aa_on = bool(row and row["auto_approve_join"])
    cs_on = bool(row and row["clean_service"])

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_SET_WELCOME"), callback_data=f"p:gr:{chat_id}:sw")],
            [InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_SET_GOODBYE"), callback_data=f"p:gr:{chat_id}:sg")],
            [
                InlineKeyboardButton(
                    text=f"{_mark(captcha_on)}{tr_sync(lang, 'PANEL_BTN_CAPTCHA')}",
                    callback_data=f"p:gr:{chat_id}:cap",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"{_mark(aa_on)}{tr_sync(lang, 'PANEL_BTN_AUTOAPPROVE')}",
                    callback_data=f"p:gr:{chat_id}:aa",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"{_mark(cs_on)}{tr_sync(lang, 'PANEL_BTN_CLEANSERVICE')}",
                    callback_data=f"p:gr:{chat_id}:cs",
                )
            ],
            _back_row(chat_id, lang, to="se"),
        ]
    )


@router.callback_query(F.data.startswith("p:gr:"))
async def on_greetings_menu(callback: CallbackQuery, bot: Bot, state: FSMContext) -> None:
    parts = callback.data.split(":")
    chat_id = int(parts[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return
    lang = await get_lang(chat_id)

    action = parts[3] if len(parts) > 3 else None

    if action == "sw":
        await state.set_state(PanelFSM.waiting_text)
        await state.update_data(chat_id=chat_id, kind="welcome")
        await callback.answer()
        await callback.message.edit_text(tr_sync(lang, "PANEL_ASK_WELCOME_TEXT"))
        return
    if action == "sg":
        await state.set_state(PanelFSM.waiting_text)
        await state.update_data(chat_id=chat_id, kind="goodbye")
        await callback.answer()
        await callback.message.edit_text(tr_sync(lang, "PANEL_ASK_GOODBYE_TEXT"))
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
        tr_sync(lang, "PANEL_GREETINGS_HEADER"), reply_markup=_greetings_keyboard(chat_id, row, lang)
    )


# ------------------------------------------------------------------
# Avto-pin / Silent rejim (premium)
# ------------------------------------------------------------------


@router.callback_query(F.data.startswith("p:ap:"))
async def on_autopin_menu(callback: CallbackQuery, bot: Bot) -> None:
    chat_id = int(callback.data.split(":")[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return
    lang = await get_lang(chat_id)

    if not await db.is_chat_premium(chat_id):
        await callback.answer()
        await callback.message.edit_text(
            tr_sync(lang, "AUTOPIN_REQUIRES_PREMIUM"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[_back_row(chat_id, lang, to="se")]),
        )
        return

    row = await db.get_chat_settings(chat_id)
    new_val = 0 if (row and row["auto_pin_welcome"]) else 1
    await db.ensure_chat(chat_id, None)
    await db.update_chat_setting(chat_id, auto_pin_welcome=new_val)
    await callback.answer(tr_sync(lang, "AUTOPIN_ON" if new_val else "AUTOPIN_OFF"))
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{_mark(bool(new_val))}Avto pin", callback_data=f"p:ap:{chat_id}"
                )
            ],
            _back_row(chat_id, lang, to="se"),
        ]
    )
    await callback.message.edit_text("Avto pin", reply_markup=kb)


@router.callback_query(F.data.startswith("p:sl:"))
async def on_silentmode_menu(callback: CallbackQuery, bot: Bot) -> None:
    chat_id = int(callback.data.split(":")[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return
    lang = await get_lang(chat_id)

    if not await db.is_chat_premium(chat_id):
        await callback.answer()
        await callback.message.edit_text(
            tr_sync(lang, "SILENTMODE_REQUIRES_PREMIUM"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[_back_row(chat_id, lang, to="se")]),
        )
        return

    row = await db.get_chat_settings(chat_id)
    new_val = 0 if (row and row["silent_admin_actions"]) else 1
    await db.ensure_chat(chat_id, None)
    await db.update_chat_setting(chat_id, silent_admin_actions=new_val)
    await callback.answer(tr_sync(lang, "SILENTMODE_ON" if new_val else "SILENTMODE_OFF"))
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{_mark(bool(new_val))}Silent rejim", callback_data=f"p:sl:{chat_id}"
                )
            ],
            _back_row(chat_id, lang, to="se"),
        ]
    )
    await callback.message.edit_text("Silent rejim", reply_markup=kb)


# ------------------------------------------------------------------
# Filtrlar
# ------------------------------------------------------------------


def _filters_keyboard(chat_id: int, rows: list, lang: str) -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text=f"- {r['trigger']}", callback_data=f"p:ft:{chat_id}:rm:{r['trigger']}")]
        for r in rows
    ]
    kb.append([InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_ADD_NEW"), callback_data=f"p:ft:{chat_id}:add")])
    kb.append(_back_row(chat_id, lang, to="co"))
    return InlineKeyboardMarkup(inline_keyboard=kb)


@router.callback_query(F.data.startswith("p:ft:"))
async def on_filters_menu(callback: CallbackQuery, bot: Bot, state: FSMContext) -> None:
    parts = callback.data.split(":", maxsplit=4)
    chat_id = int(parts[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return
    lang = await get_lang(chat_id)

    action = parts[3] if len(parts) > 3 else None
    if action == "add":
        await state.set_state(PanelFSM.waiting_text)
        await state.update_data(chat_id=chat_id, kind="filter_add")
        await callback.answer()
        await callback.message.edit_text(tr_sync(lang, "PANEL_ASK_FILTER"))
        return
    if action == "rm" and len(parts) > 4:
        await db.remove_filter(chat_id, parts[4])
        await callback.answer(tr_sync(lang, "PANEL_REMOVED_OK"))

    rows = await db.list_filters(chat_id)
    if action is None:
        await callback.answer()
    await callback.message.edit_text(
        tr_sync(lang, "PANEL_FILTERS_HEADER") if rows else tr_sync(lang, "PANEL_FILTERS_EMPTY"),
        reply_markup=_filters_keyboard(chat_id, rows, lang),
    )


# ------------------------------------------------------------------
# Eslatmalar (Notes)
# ------------------------------------------------------------------


def _notes_keyboard(chat_id: int, rows: list, lang: str) -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text=f"#{r['name']}", callback_data=f"p:nt:{chat_id}:rm:{r['name']}")]
        for r in rows
    ]
    kb.append([InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_ADD_NEW"), callback_data=f"p:nt:{chat_id}:add")])
    kb.append(_back_row(chat_id, lang, to="co"))
    return InlineKeyboardMarkup(inline_keyboard=kb)


@router.callback_query(F.data.startswith("p:nt:"))
async def on_notes_menu(callback: CallbackQuery, bot: Bot, state: FSMContext) -> None:
    parts = callback.data.split(":", maxsplit=4)
    chat_id = int(parts[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return
    lang = await get_lang(chat_id)

    action = parts[3] if len(parts) > 3 else None
    if action == "add":
        await state.set_state(PanelFSM.waiting_text)
        await state.update_data(chat_id=chat_id, kind="note_add")
        await callback.answer()
        await callback.message.edit_text(tr_sync(lang, "PANEL_ASK_NOTE"))
        return
    if action == "rm" and len(parts) > 4:
        await db.remove_note(chat_id, parts[4])
        await callback.answer(tr_sync(lang, "PANEL_REMOVED_OK"))

    rows = await db.list_notes(chat_id)
    if action is None:
        await callback.answer()
    await callback.message.edit_text(
        tr_sync(lang, "PANEL_NOTES_HEADER") if rows else tr_sync(lang, "PANEL_NOTES_EMPTY"),
        reply_markup=_notes_keyboard(chat_id, rows, lang),
    )


# ------------------------------------------------------------------
# Personal (custom buyruqlar)
# ------------------------------------------------------------------


def _personal_keyboard(chat_id: int, rows: list, lang: str) -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text=f"/{r['name']}", callback_data=f"p:ps:{chat_id}:rm:{r['name']}")]
        for r in rows
    ]
    kb.append([InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_ADD_NEW"), callback_data=f"p:ps:{chat_id}:add")])
    kb.append(_back_row(chat_id, lang, to="co"))
    return InlineKeyboardMarkup(inline_keyboard=kb)


@router.callback_query(F.data.startswith("p:ps:"))
async def on_personal_menu(callback: CallbackQuery, bot: Bot, state: FSMContext) -> None:
    parts = callback.data.split(":", maxsplit=4)
    chat_id = int(parts[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return
    lang = await get_lang(chat_id)

    action = parts[3] if len(parts) > 3 else None
    if action == "add":
        await state.set_state(PanelFSM.waiting_text)
        await state.update_data(chat_id=chat_id, kind="personal_add")
        await callback.answer()
        await callback.message.edit_text(tr_sync(lang, "PANEL_ASK_PERSONAL"))
        return
    if action == "rm" and len(parts) > 4:
        await db.remove_custom_command(chat_id, parts[4])
        await callback.answer(tr_sync(lang, "PANEL_REMOVED_OK"))

    rows = await db.list_custom_commands(chat_id)
    if action is None:
        await callback.answer()
    await callback.message.edit_text(
        tr_sync(lang, "PANEL_PERSONAL_HEADER") if rows else tr_sync(lang, "PANEL_PERSONAL_EMPTY"),
        reply_markup=_personal_keyboard(chat_id, rows, lang),
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
    lang = await get_lang(chat_id)

    if len(parts) > 3 and parts[3] == "set":
        await state.set_state(PanelFSM.waiting_text)
        await state.update_data(chat_id=chat_id, kind="rules")
        await callback.answer()
        await callback.message.edit_text(tr_sync(lang, "PANEL_ASK_RULES"))
        return

    row = await db.get_chat_settings(chat_id)
    rules_text = row["rules_text"] if row and row["rules_text"] else tr_sync(lang, "RULES_EMPTY")
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_EDIT_RULES"), callback_data=f"p:rl:{chat_id}:set")],
            _back_row(chat_id, lang, to="se"),
        ]
    )
    await callback.answer()
    await callback.message.edit_text(f"{tr_sync(lang, 'RULES_HEADER')}{rules_text}", reply_markup=kb)


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
    lang = await get_lang(chat_id)

    action = parts[3] if len(parts) > 3 else None
    if action in ("30d", "life"):
        await callback.answer()
        plan = "lifetime" if action == "life" else "30d"
        await _send_invoice(bot, callback.from_user.id, plan, target_group_chat_id=chat_id)
        return

    row = await db.get_chat_settings(chat_id)
    now = time.time()
    if is_super_admin(callback.from_user.id):
        status = tr_sync(lang, "PREMIUM_STATUS_SUPERADMIN")
        already = True
    elif row and row["premium_lifetime"]:
        status = tr_sync(lang, "PREMIUM_STATUS_LIFETIME")
        already = True
    elif row and row["premium_until"] and row["premium_until"] > now:
        status = tr_sync(
            lang, "PREMIUM_STATUS_ACTIVE_UNTIL", date=format_timestamp(row["premium_until"], "%d.%m.%Y")
        )
        already = True
    else:
        status = tr_sync(lang, "PREMIUM_STATUS_NONE")
        already = False

    kb_rows = []
    if not already:
        kb_rows.append(
            [
                InlineKeyboardButton(
                    text=tr_sync(lang, "PREMIUM_BUTTON_30D", price=settings.premium_30d_price_stars),
                    callback_data=f"p:pr:{chat_id}:30d",
                )
            ]
        )
        kb_rows.append(
            [
                InlineKeyboardButton(
                    text=tr_sync(lang, "PREMIUM_BUTTON_LIFETIME", price=settings.premium_lifetime_price_stars),
                    callback_data=f"p:pr:{chat_id}:life",
                )
            ]
        )
    kb_rows.append(_back_row(chat_id, lang, to="pc"))

    await callback.answer()
    await callback.message.edit_text(
        tr_sync(lang, "PANEL_PREMIUM_HEADER", status=status),
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
    lang = await get_lang(chat_id)

    if not await db.is_chat_premium(chat_id):
        await callback.answer()
        await callback.message.edit_text(
            tr_sync(lang, "AI_MODERATION_REQUIRES_PREMIUM"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[_back_row(chat_id, lang, to="pc")]),
        )
        return

    row = await db.get_chat_settings(chat_id)
    new_val = 0 if (row and row["ai_moderation_enabled"]) else 1
    await db.ensure_chat(chat_id, None)
    await db.update_chat_setting(chat_id, ai_moderation_enabled=new_val)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{_mark(bool(new_val))}{tr_sync(lang, 'PANEL_BTN_AI_MOD')}",
                    callback_data=f"p:ai:{chat_id}",
                )
            ],
            _back_row(chat_id, lang, to="pc"),
        ]
    )
    await callback.answer(tr_sync(lang, "AI_MODERATION_ON" if new_val else "AI_MODERATION_OFF"))
    await callback.message.edit_text(tr_sync(lang, "PANEL_AI_MOD_HEADER"), reply_markup=kb)


# ------------------------------------------------------------------
# VIP
# ------------------------------------------------------------------


def _vip_keyboard(chat_id: int, rows: list, lang: str) -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text=f"- {r['user_id']}", callback_data=f"p:vip:{chat_id}:rm:{r['user_id']}")]
        for r in rows
    ]
    kb.append([InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_ADD_NEW"), callback_data=f"p:vip:{chat_id}:add")])
    kb.append(_back_row(chat_id, lang, to="pc"))
    return InlineKeyboardMarkup(inline_keyboard=kb)


@router.callback_query(F.data.startswith("p:vip:"))
async def on_vip_menu(callback: CallbackQuery, bot: Bot, state: FSMContext) -> None:
    parts = callback.data.split(":", maxsplit=4)
    chat_id = int(parts[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return
    lang = await get_lang(chat_id)

    if not await db.is_chat_premium(chat_id):
        await callback.answer()
        await callback.message.edit_text(
            tr_sync(lang, "VIP_REQUIRES_PREMIUM"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[_back_row(chat_id, lang, to="pc")]),
        )
        return

    action = parts[3] if len(parts) > 3 else None
    if action == "add":
        await state.set_state(PanelFSM.waiting_text)
        await state.update_data(chat_id=chat_id, kind="vip_add")
        await callback.answer()
        await callback.message.edit_text(tr_sync(lang, "PANEL_ASK_VIP"))
        return
    if action == "rm" and len(parts) > 4:
        await db.remove_vip(chat_id, int(parts[4]))
        await callback.answer(tr_sync(lang, "PANEL_REMOVED_OK"))

    rows = await db.list_vips(chat_id)
    if action is None:
        await callback.answer()
    await callback.message.edit_text(
        tr_sync(lang, "PANEL_VIP_HEADER") if rows else tr_sync(lang, "PANEL_VIP_EMPTY"),
        reply_markup=_vip_keyboard(chat_id, rows, lang),
    )


# ------------------------------------------------------------------
# Moderatorlar
# ------------------------------------------------------------------


def _moderators_keyboard(chat_id: int, rows: list, lang: str) -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text=f"- {r['user_id']}", callback_data=f"p:mod:{chat_id}:rm:{r['user_id']}")]
        for r in rows
    ]
    kb.append([InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_ADD_NEW"), callback_data=f"p:mod:{chat_id}:add")])
    kb.append(_back_row(chat_id, lang, to="pc"))
    return InlineKeyboardMarkup(inline_keyboard=kb)


@router.callback_query(F.data.startswith("p:mod:"))
async def on_moderators_menu(callback: CallbackQuery, bot: Bot, state: FSMContext) -> None:
    parts = callback.data.split(":", maxsplit=4)
    chat_id = int(parts[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return
    lang = await get_lang(chat_id)

    if not await db.is_chat_premium(chat_id):
        await callback.answer()
        await callback.message.edit_text(
            tr_sync(lang, "MODERATOR_REQUIRES_PREMIUM"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[_back_row(chat_id, lang, to="pc")]),
        )
        return

    action = parts[3] if len(parts) > 3 else None
    if action == "add":
        await state.set_state(PanelFSM.waiting_text)
        await state.update_data(chat_id=chat_id, kind="moderator_add")
        await callback.answer()
        await callback.message.edit_text(tr_sync(lang, "PANEL_ASK_MODERATOR"))
        return
    if action == "rm" and len(parts) > 4:
        await db.remove_moderator(chat_id, int(parts[4]))
        await callback.answer(tr_sync(lang, "PANEL_REMOVED_OK"))

    rows = await db.list_moderators(chat_id)
    if action is None:
        await callback.answer()
    await callback.message.edit_text(
        tr_sync(lang, "PANEL_MODERATORS_HEADER") if rows else tr_sync(lang, "PANEL_MODERATORS_EMPTY"),
        reply_markup=_moderators_keyboard(chat_id, rows, lang),
    )


# ------------------------------------------------------------------
# Rejalashtirilgan xabarlar
# ------------------------------------------------------------------


def _schedule_keyboard(chat_id: int, rows: list, lang: str) -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(
                text=f"{r['hour']:02d}:{r['minute']:02d} - {r['text'][:20]}",
                callback_data=f"p:sch:{chat_id}:rm:{r['id']}",
            )
        ]
        for r in rows
    ]
    kb.append([InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_ADD_NEW"), callback_data=f"p:sch:{chat_id}:add")])
    kb.append(_back_row(chat_id, lang, to="pc"))
    return InlineKeyboardMarkup(inline_keyboard=kb)


@router.callback_query(F.data.startswith("p:sch:"))
async def on_schedule_menu(callback: CallbackQuery, bot: Bot, state: FSMContext) -> None:
    parts = callback.data.split(":", maxsplit=4)
    chat_id = int(parts[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return
    lang = await get_lang(chat_id)

    if not await db.is_chat_premium(chat_id):
        await callback.answer()
        await callback.message.edit_text(
            tr_sync(lang, "SCHEDULE_REQUIRES_PREMIUM"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[_back_row(chat_id, lang, to="pc")]),
        )
        return

    action = parts[3] if len(parts) > 3 else None
    if action == "add":
        await state.set_state(PanelFSM.waiting_text)
        await state.update_data(chat_id=chat_id, kind="schedule_add")
        await callback.answer()
        await callback.message.edit_text(tr_sync(lang, "PANEL_ASK_SCHEDULE"))
        return
    if action == "rm" and len(parts) > 4:
        await db.remove_scheduled_message(int(parts[4]), chat_id)
        await callback.answer(tr_sync(lang, "PANEL_REMOVED_OK"))

    rows = await db.list_scheduled_messages(chat_id)
    if action is None:
        await callback.answer()
    await callback.message.edit_text(
        tr_sync(lang, "PANEL_SCHEDULE_HEADER") if rows else tr_sync(lang, "PANEL_SCHEDULE_EMPTY"),
        reply_markup=_schedule_keyboard(chat_id, rows, lang),
    )


# ------------------------------------------------------------------
# Avto-o'chirish (autodelete)
# ------------------------------------------------------------------


@router.callback_query(F.data.startswith("p:adt:"))
async def on_autodelete_menu(callback: CallbackQuery, bot: Bot, state: FSMContext) -> None:
    parts = callback.data.split(":")
    chat_id = int(parts[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return
    lang = await get_lang(chat_id)

    if not await db.is_chat_premium(chat_id):
        await callback.answer()
        await callback.message.edit_text(
            tr_sync(lang, "AUTODELETE_REQUIRES_PREMIUM"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[_back_row(chat_id, lang, to="pc")]),
        )
        return

    if len(parts) > 3 and parts[3] == "set":
        await state.set_state(PanelFSM.waiting_text)
        await state.update_data(chat_id=chat_id, kind="autodelete_set")
        await callback.answer()
        await callback.message.edit_text(tr_sync(lang, "PANEL_ASK_AUTODELETE"))
        return

    row = await db.get_chat_settings(chat_id)
    seconds = row["autodelete_seconds"] if row else 0
    status = f"{seconds}s" if seconds else _on_off(lang, False)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_ADD_NEW"), callback_data=f"p:adt:{chat_id}:set")],
            _back_row(chat_id, lang, to="pc"),
        ]
    )
    await callback.answer()
    await callback.message.edit_text(tr_sync(lang, "PANEL_AUTODELETE_HEADER", status=status), reply_markup=kb)


# ------------------------------------------------------------------
# Kunlik hisobot
# ------------------------------------------------------------------


@router.callback_query(F.data.startswith("p:dr:"))
async def on_dailyreport_menu(callback: CallbackQuery, bot: Bot, state: FSMContext) -> None:
    parts = callback.data.split(":")
    chat_id = int(parts[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return
    lang = await get_lang(chat_id)

    if not await db.is_chat_premium(chat_id):
        await callback.answer()
        await callback.message.edit_text(
            tr_sync(lang, "DAILYREPORT_REQUIRES_PREMIUM"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[_back_row(chat_id, lang, to="pc")]),
        )
        return

    if len(parts) > 3 and parts[3] == "set":
        await state.set_state(PanelFSM.waiting_text)
        await state.update_data(chat_id=chat_id, kind="dailyreport_set", admin_id=callback.from_user.id)
        await callback.answer()
        await callback.message.edit_text(tr_sync(lang, "PANEL_ASK_DAILYREPORT"))
        return

    row = await db.get_chat_settings(chat_id)
    status = f"{row['daily_report_hour']:02d}:00" if row and row["daily_report_enabled"] else _on_off(lang, False)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=tr_sync(lang, "PANEL_BTN_ADD_NEW"), callback_data=f"p:dr:{chat_id}:set")],
            _back_row(chat_id, lang, to="pc"),
        ]
    )
    await callback.answer()
    await callback.message.edit_text(tr_sync(lang, "PANEL_DAILYREPORT_HEADER", status=status), reply_markup=kb)


# ------------------------------------------------------------------
# Zaxira nusxa
# ------------------------------------------------------------------


@router.callback_query(F.data.startswith("p:bk:"))
async def on_backup_menu(callback: CallbackQuery, bot: Bot) -> None:
    chat_id = int(callback.data.split(":")[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return
    lang = await get_lang(chat_id)

    if not await db.is_chat_premium(chat_id):
        await callback.answer()
        await callback.message.edit_text(
            tr_sync(lang, "BACKUP_REQUIRES_PREMIUM"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[_back_row(chat_id, lang, to="pc")]),
        )
        return

    await callback.answer(tr_sync(lang, "BACKUP_GENERATING"))

    import json

    row = await db.get_chat_settings(chat_id)
    filters_rows = await db.all_filters(chat_id)
    notes_rows = await db.list_notes(chat_id)
    custom_commands_rows = await db.list_custom_commands(chat_id)
    data = {
        "chat_id": chat_id,
        "chat_title": row["chat_title"] if row else None,
        "settings": {k: row[k] for k in row.keys()} if row else {},
        "filters": [dict(r) for r in filters_rows],
        "notes": [r["name"] for r in notes_rows],
        "custom_commands": [r["name"] for r in custom_commands_rows],
    }
    from aiogram.types import BufferedInputFile

    payload = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
    filename = f"achi_backup_{chat_id}.json"
    await bot.send_document(
        callback.from_user.id,
        BufferedInputFile(payload, filename=filename),
        caption=tr_sync(lang, "BACKUP_CAPTION"),
    )


# ------------------------------------------------------------------
# Hisobotlar (Reports)
# ------------------------------------------------------------------


def _reports_keyboard(chat_id: int, lang: str) -> InlineKeyboardMarkup:
    rows = []
    for period_key, period_label in _PERIODS:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{tr_sync(lang, 'PANEL_BTN_REPORT_TEXT')} ({period_label})",
                    callback_data=f"p:rp:{chat_id}:txt:{period_key}",
                ),
                InlineKeyboardButton(
                    text=f"{tr_sync(lang, 'PANEL_BTN_REPORT_PDF')} ({period_label})",
                    callback_data=f"p:rp:{chat_id}:pdf:{period_key}",
                ),
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=tr_sync(lang, "PANEL_BTN_REPORT_CSV"), callback_data=f"p:rp:{chat_id}:csv:hafta"
            )
        ]
    )
    rows.append(_back_row(chat_id, lang, to="ot"))
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
    lang = await get_lang(chat_id)

    if len(parts) < 5:
        await callback.answer()
        await callback.message.edit_text(
            tr_sync(lang, "PANEL_REPORTS_HEADER"), reply_markup=_reports_keyboard(chat_id, lang)
        )
        return

    kind, period_key = parts[3], parts[4]
    bounds = _period_bounds(period_key) or (time.time() - 3600, "so'nggi 1 soat")
    since_ts, period_label = bounds
    row = await db.get_chat_settings(chat_id)
    chat_title = (row["chat_title"] if row else None) or f"ID: {chat_id}"
    dm_chat_id = callback.from_user.id

    await callback.answer(tr_sync(lang, "PANEL_REPORT_PREPARING"))

    if kind == "txt":
        actions = await db.get_actions_since(chat_id, since_ts)
        with_ai = await db.is_chat_premium(chat_id)
        chunks = await build_text_report_chunks(chat_title, actions, period_label, with_ai_summary=with_ai)
        for chunk in chunks:
            await bot.send_message(dm_chat_id, chunk)
    elif kind == "pdf":
        ok = await generate_and_send_pdf(
            bot, chat_id, chat_title, since_ts, period_label, send_to_chat_id=dm_chat_id
        )
        if not ok:
            await bot.send_message(dm_chat_id, tr_sync(lang, "REPORT_EMPTY_PERIOD"))
    elif kind == "csv":
        if not await db.is_chat_premium(chat_id):
            await bot.send_message(dm_chat_id, tr_sync(lang, "PREMIUM_REQUIRED_EXPORT"))
        else:
            ok = await generate_and_send_csv(
                bot, chat_id, chat_title, since_ts, period_label, send_to_chat_id=dm_chat_id
            )
            if not ok:
                await bot.send_message(dm_chat_id, tr_sync(lang, "REPORT_EMPTY_PERIOD"))


# ------------------------------------------------------------------
# Federatsiya
# ------------------------------------------------------------------


@router.callback_query(F.data.startswith("p:fd:"))
async def on_federation_menu(callback: CallbackQuery, bot: Bot) -> None:
    chat_id = int(callback.data.split(":")[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return
    lang = await get_lang(chat_id)

    fed_id = await db.get_chat_federation(chat_id)
    await callback.answer()
    if not fed_id:
        text = tr_sync(lang, "PANEL_FEDERATION_NONE")
    else:
        fed = await db.get_federation(fed_id)
        chats = await db.get_federation_chats(fed_id)
        bans_count = await db.count_fed_bans(fed_id)
        text = tr_sync(
            lang,
            "FED_INFO",
            name=fed["name"] if fed else "?",
            fed_id=fed_id,
            chats_count=len(chats),
            bans_count=bans_count,
        )
    await callback.message.edit_text(
        text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[_back_row(chat_id, lang, to="ot")])
    )


# ------------------------------------------------------------------
# Admin vositalari
# ------------------------------------------------------------------


@router.callback_query(F.data.startswith("p:ad:"))
async def on_admin_tools_menu(callback: CallbackQuery, bot: Bot) -> None:
    from aiogram.types import ChatMemberOwner

    from utils import mention_html

    chat_id = int(callback.data.split(":")[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return
    lang = await get_lang(chat_id)

    await callback.answer()
    try:
        admins = await bot.get_chat_administrators(chat_id)
    except TelegramAPIError:
        admins = []

    real_admins = [a for a in admins if not a.user.is_bot]
    if not real_admins:
        text = tr_sync(lang, "STAFF_EMPTY")
    else:
        lines = [tr_sync(lang, "PANEL_ADMIN_TOOLS_HEADER")]
        for a in real_admins:
            mention = mention_html(a.user.id, a.user.full_name)
            if isinstance(a, ChatMemberOwner):
                lines.append(tr_sync(lang, "STAFF_OWNER_LINE", mention=mention))
            else:
                lines.append(tr_sync(lang, "STAFF_ADMIN_LINE", mention=mention))
        text = "\n".join(lines)

    await callback.message.edit_text(
        text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[_back_row(chat_id, lang, to="ot")])
    )


# ------------------------------------------------------------------
# Statistika
# ------------------------------------------------------------------


@router.callback_query(F.data.startswith("p:st:"))
async def on_stats_menu(callback: CallbackQuery, bot: Bot) -> None:
    chat_id = int(callback.data.split(":")[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return
    lang = await get_lang(chat_id)

    since_week = time.time() - 7 * 86400
    counts = await db.count_actions_by_type_since(chat_id, since_week)
    members_count = await db.count_known_members(chat_id)
    await callback.answer()
    text = tr_sync(
        lang,
        "STATS_RESULT",
        members=members_count,
        ban=counts.get("ban", 0) + counts.get("tban", 0),
        mute=counts.get("mute", 0) + counts.get("tmute", 0),
        warn=counts.get("warn", 0),
        kick=counts.get("kick", 0),
    )
    await callback.message.edit_text(
        f"{tr_sync(lang, 'PANEL_STATS_HEADER')}\n\n{text}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[_back_row(chat_id, lang, to="ot")]),
    )


# ------------------------------------------------------------------
# Taklif havolasi
# ------------------------------------------------------------------


@router.callback_query(F.data.startswith("p:iv:"))
async def on_invite_menu(callback: CallbackQuery, bot: Bot) -> None:
    chat_id = int(callback.data.split(":")[2])
    if not callback.from_user or not await _verify_admin(bot, callback.from_user.id, chat_id):
        await callback.answer(texts.PANEL_NOT_ADMIN_OF_THAT_GROUP, show_alert=True)
        return
    lang = await get_lang(chat_id)

    try:
        chat = await bot.get_chat(chat_id)
        link = chat.invite_link
        if not link:
            link = await bot.export_chat_invite_link(chat_id)
    except TelegramAPIError:
        await callback.answer(texts.BOT_NOT_ADMIN, show_alert=True)
        return

    await callback.answer()
    await callback.message.edit_text(
        tr_sync(lang, "INVITE_RESULT", link=link),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[_back_row(chat_id, lang, to="ot")]),
    )


# ------------------------------------------------------------------
# FSM - matn kiritish (barcha "ask" oqimlari)
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

    lang = await get_lang(chat_id)
    text_value = (message.text or "").strip()
    if not text_value:
        await message.answer(tr_sync(lang, "PANEL_TEXT_EMPTY"))
        return

    await db.ensure_chat(chat_id, None)

    if kind == "welcome":
        await db.update_chat_setting(chat_id, welcome_text=text_value)
        await message.answer(tr_sync(lang, "WELCOME_SET"))
    elif kind == "goodbye":
        await db.update_chat_setting(chat_id, goodbye_text=text_value)
        await message.answer(tr_sync(lang, "GOODBYE_SET"))
    elif kind == "rules":
        await db.update_chat_setting(chat_id, rules_text=text_value)
        await message.answer(tr_sync(lang, "RULES_SET"))
    elif kind == "filter_add":
        if "|" not in text_value:
            await message.answer(tr_sync(lang, "FILTER_USAGE"))
            return
        trigger, reply = text_value.split("|", maxsplit=1)
        trigger, reply = trigger.strip(), reply.strip()
        if not trigger or not reply:
            await message.answer(tr_sync(lang, "FILTER_USAGE"))
            return
        # BUG TUZATILDI: avval bu yerda premium/limit tekshiruvi umuman
        # yo'q edi - guruh ichidagi /filter buyrug'i tekshirardi, DM
        # panel esa tekshirmasdi (bepul guruh cheksiz filtr qo'sha
        # olardi). Endi ikkisi bir xil ishlaydi.
        existing = await db.get_filter(chat_id, trigger)
        if existing is None:
            premium = await is_premium_or_free(chat_id, message.from_user.id)
            if not premium:
                count = await db.count_filters(chat_id)
                if count >= settings.free_filter_limit:
                    await message.answer(
                        tr_sync(lang, "PREMIUM_REQUIRED_FILTER_LIMIT", limit=settings.free_filter_limit)
                    )
                    return
        await db.set_filter(chat_id, trigger, reply)
        await message.answer(tr_sync(lang, "FILTER_SAVED", trigger=trigger))
    elif kind == "note_add":
        parts = text_value.split(maxsplit=1)
        if len(parts) < 2:
            await message.answer(tr_sync(lang, "NOTE_USAGE"))
            return
        existing = await db.get_note(chat_id, parts[0])
        if existing is None:
            premium = await is_premium_or_free(chat_id, message.from_user.id)
            if not premium:
                count = await db.count_notes(chat_id)
                if count >= settings.free_note_limit:
                    await message.answer(
                        tr_sync(lang, "PREMIUM_REQUIRED_NOTE_LIMIT", limit=settings.free_note_limit)
                    )
                    return
        await db.save_note(chat_id, parts[0], parts[1])
        await message.answer(tr_sync(lang, "NOTE_SAVED", name=parts[0]))
    elif kind == "personal_add":
        from handlers.content import RESERVED_COMMAND_NAMES

        parts = text_value.split(maxsplit=1)
        if len(parts) < 2:
            await message.answer(tr_sync(lang, "PERSONAL_USAGE"))
            return
        name = parts[0].lstrip("/").lower()
        if not name.isascii() or not name.replace("_", "").isalnum():
            await message.answer(tr_sync(lang, "PERSONAL_BAD_NAME"))
            return
        if name in RESERVED_COMMAND_NAMES:
            await message.answer(tr_sync(lang, "PERSONAL_NAME_RESERVED", name=name))
            return
        await db.add_custom_command(chat_id, name, parts[1], message.from_user.id)
        await message.answer(tr_sync(lang, "PERSONAL_ADDED", name=name))
    elif kind == "badword_add":
        word = text_value.lower()
        await db.add_bad_word(chat_id, word, message.from_user.id)
        await message.answer(tr_sync(lang, "BADWORD_ADDED", word=word))
    elif kind == "slowmode_set":
        if not text_value.isdigit():
            await message.answer(tr_sync(lang, "SLOWMODE_USAGE"))
            return
        seconds = int(text_value)
        await db.update_chat_setting(chat_id, slowmode_seconds=seconds)
        await message.answer(
            tr_sync(lang, "SLOWMODE_ON", seconds=seconds) if seconds else tr_sync(lang, "SLOWMODE_OFF")
        )
    elif kind == "floodlimit_set":
        if text_value.lower() == "off":
            await db.update_chat_setting(chat_id, flood_limit_override=None, flood_window_override=None)
            await message.answer(tr_sync(lang, "FLOODLIMIT_OFF"))
            return
        parts = text_value.split()
        if len(parts) != 2 or not all(p.isdigit() for p in parts):
            await message.answer(tr_sync(lang, "FLOODLIMIT_USAGE"))
            return
        limit, window = int(parts[0]), int(parts[1])
        await db.update_chat_setting(chat_id, flood_limit_override=limit, flood_window_override=window)
        await message.answer(tr_sync(lang, "FLOODLIMIT_SET", limit=limit, window=window))
    elif kind == "antiraid_set":
        if text_value.lower() == "off":
            await db.update_chat_setting(chat_id, anti_raid_enabled=0)
            await message.answer(tr_sync(lang, "ANTIRAID_OFF"))
            return
        parts = text_value.split()
        if len(parts) != 2 or not all(p.isdigit() for p in parts):
            await message.answer(tr_sync(lang, "ANTIRAID_USAGE"))
            return
        threshold, window = int(parts[0]), int(parts[1])
        await db.update_chat_setting(
            chat_id, anti_raid_enabled=1, anti_raid_threshold=threshold, anti_raid_window_sec=window
        )
        await message.answer(tr_sync(lang, "ANTIRAID_ON", threshold=threshold, window=window))
    elif kind == "nightmode_set":
        if text_value.lower() == "off":
            await db.update_chat_setting(chat_id, night_mode_enabled=0)
            await message.answer(tr_sync(lang, "NIGHTMODE_OFF"))
            return
        if "-" not in text_value:
            await message.answer(tr_sync(lang, "NIGHTMODE_USAGE"))
            return
        start_s, end_s = text_value.split("-", maxsplit=1)
        if not (start_s.isdigit() and end_s.isdigit()):
            await message.answer(tr_sync(lang, "NIGHTMODE_USAGE"))
            return
        start_h, end_h = int(start_s), int(end_s)
        if not (0 <= start_h <= 23 and 0 <= end_h <= 23):
            await message.answer(tr_sync(lang, "NIGHTMODE_USAGE"))
            return
        await db.update_chat_setting(
            chat_id, night_mode_enabled=1, night_start_hour=start_h, night_end_hour=end_h
        )
        await message.answer(tr_sync(lang, "NIGHTMODE_ON", start=start_h, end=end_h))
    elif kind == "linkwhitelist_add":
        domain = text_value.lower()
        await db.add_whitelisted_domain(chat_id, domain)
        await message.answer(tr_sync(lang, "LINKWHITELIST_ADDED", domain=domain))
    elif kind == "warnexpiry_set":
        if text_value == "0" or text_value.lower() == "off":
            await db.update_chat_setting(chat_id, warn_expiry_days=0)
            await message.answer(tr_sync(lang, "WARNEXPIRY_OFF"))
            return
        if not text_value.isdigit():
            await message.answer(tr_sync(lang, "WARNEXPIRY_USAGE"))
            return
        days = int(text_value)
        await db.update_chat_setting(chat_id, warn_expiry_days=days)
        await message.answer(tr_sync(lang, "WARNEXPIRY_SET", days=days))
    elif kind == "textcaptcha_set":
        if text_value.lower() == "off":
            await db.update_chat_setting(chat_id, text_captcha_question=None, text_captcha_answer=None)
            await message.answer(tr_sync(lang, "TEXTCAPTCHA_OFF"))
            return
        if "|" not in text_value:
            await message.answer(tr_sync(lang, "TEXTCAPTCHA_USAGE"))
            return
        question, answer = text_value.split("|", maxsplit=1)
        question, answer = question.strip(), answer.strip()
        if not question or not answer:
            await message.answer(tr_sync(lang, "TEXTCAPTCHA_USAGE"))
            return
        await db.update_chat_setting(chat_id, text_captcha_question=question, text_captcha_answer=answer)
        await message.answer(tr_sync(lang, "TEXTCAPTCHA_SET"))
    elif kind == "autodelete_set":
        if not text_value.isdigit():
            await message.answer(tr_sync(lang, "AUTODELETE_USAGE"))
            return
        seconds = int(text_value)
        await db.update_chat_setting(chat_id, autodelete_seconds=seconds)
        await message.answer(
            tr_sync(lang, "AUTODELETE_SET", seconds=seconds) if seconds else tr_sync(lang, "AUTODELETE_OFF")
        )
    elif kind == "vip_add":
        user_id = await _resolve_id_from_text(chat_id, text_value)
        if not user_id:
            await message.answer(tr_sync(lang, "VIP_USAGE"))
            return
        await db.add_vip(chat_id, user_id, message.from_user.id)
        await message.answer(tr_sync(lang, "VIP_ADDED", target=str(user_id)))
    elif kind == "moderator_add":
        user_id = await _resolve_id_from_text(chat_id, text_value)
        if not user_id:
            await message.answer(tr_sync(lang, "MODERATOR_USAGE"))
            return
        await db.add_moderator(chat_id, user_id, message.from_user.id)
        await message.answer(tr_sync(lang, "MODERATOR_ADDED", target=str(user_id)))
    elif kind == "schedule_add":
        parts = text_value.split(maxsplit=1)
        if len(parts) < 2 or ":" not in parts[0]:
            await message.answer(tr_sync(lang, "SCHEDULE_USAGE"))
            return
        hour_s, minute_s = parts[0].split(":", maxsplit=1)
        if not (hour_s.isdigit() and minute_s.isdigit()):
            await message.answer(tr_sync(lang, "SCHEDULE_USAGE"))
            return
        hour, minute = int(hour_s), int(minute_s)
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            await message.answer(tr_sync(lang, "SCHEDULE_USAGE"))
            return
        await db.add_scheduled_message(chat_id, parts[1], hour, minute, message.from_user.id)
        await message.answer(tr_sync(lang, "SCHEDULE_ADDED", time=f"{hour:02d}:{minute:02d}"))
    elif kind == "dailyreport_set":
        if text_value.lower() == "off":
            await db.update_chat_setting(chat_id, daily_report_enabled=0)
            await message.answer(tr_sync(lang, "DAILYREPORT_OFF"))
            return
        if not text_value.isdigit() or not (0 <= int(text_value) <= 23):
            await message.answer(tr_sync(lang, "DAILYREPORT_USAGE"))
            return
        hour = int(text_value)
        admin_id = data.get("admin_id", message.from_user.id)
        await db.update_chat_setting(
            chat_id, daily_report_enabled=1, daily_report_hour=hour, daily_report_admin_id=admin_id
        )
        await message.answer(tr_sync(lang, "DAILYREPORT_ON", hour=hour))


# ------------------------------------------------------------------
# Onboarding - bot guruhga admin qilib qo'shilganda
# ------------------------------------------------------------------


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
