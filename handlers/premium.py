"""
ACHI BOT - Premium (Telegram Stars orqali to'lov).

Muhim biznes qoidasi (foydalanuvchi so'roviga ko'ra):
- SUPER_ADMINS ro'yxatidagi odamlar (bot egasi) uchun premium funksiyalar
  QAYERDA BO'LMASIN tekin ishlaydi - hech qanday to'lov talab qilinmaydi.
- Boshqa har qanday guruh premium funksiyalardan foydalanish uchun shu
  guruhga Telegram Stars orqali premium sotib olishi kerak.

Telegram Stars - Telegramning o'z ichki valyutasi, tashqi bank/karta
integratsiyasi shart emas: `bot.send_invoice(..., currency="XTR", ...)`
orqali hisob-varaqa yuboriladi, foydalanuvchi Telegram ichida to'laydi,
bot `successful_payment` update'ini oladi.
"""
from __future__ import annotations

import asyncio
import time

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)

import texts
from config import is_super_admin, settings
from database import db
from utils import format_timestamp, is_chat_admin, user_display_name

router = Router(name="premium")

_PLAN_30D = "30d"
_PLAN_LIFETIME = "lifetime"


async def is_premium_or_free(chat_id: int, requester_id: int | None = None) -> bool:
    """
    Guruh premium funksiyadan foydalanishga haqli-yo'qligini tekshiradi:
    - agar buyruqni bot egasi (super-admin) yozgan bo'lsa -> har doim True
    - aks holda guruhning o'zida premium yoqilgan-yo'qligiga qaraladi
    """
    if requester_id is not None and is_super_admin(requester_id):
        return True
    return await db.is_chat_premium(chat_id)


def _premium_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=texts.PREMIUM_BUTTON_30D.format(
                        price=settings.premium_30d_price_stars
                    ),
                    callback_data="premium_buy:30d",
                )
            ],
            [
                InlineKeyboardButton(
                    text=texts.PREMIUM_BUTTON_LIFETIME.format(
                        price=settings.premium_lifetime_price_stars
                    ),
                    callback_data="premium_buy:lifetime",
                )
            ],
        ]
    )


@router.message(Command("premium"))
async def cmd_premium(message: Message, bot: Bot) -> None:
    if message.chat.type not in ("group", "supergroup"):
        await message.reply(texts.PREMIUM_ONLY_IN_GROUP)
        return

    is_superadmin_caller = bool(message.from_user and is_super_admin(message.from_user.id))
    row = await db.get_chat_settings(message.chat.id)

    already_active = False
    if is_superadmin_caller:
        status = texts.PREMIUM_STATUS_SUPERADMIN
        already_active = True
    elif row and row["premium_lifetime"]:
        status = texts.PREMIUM_STATUS_LIFETIME
        already_active = True
    elif row and row["premium_until"] and row["premium_until"] > time.time():
        date_str = format_timestamp(row["premium_until"], "%d.%m.%Y")
        status = texts.PREMIUM_STATUS_ACTIVE_UNTIL.format(date=date_str)
        already_active = True
    else:
        status = texts.PREMIUM_STATUS_NONE

    # Guruhda premium ALLAQACHON faol bo'lsa, narx/tarif tugmalarini
    # qayta ko'rsatmaymiz - bu adminni "yana sotib olishim kerakmi"
    # degan chalkashlikka solgan bug edi. Faqat holatni ko'rsatib,
    # premium imkoniyatlar ro'yxatini eslatib qo'yamiz, xolos.
    if already_active:
        await message.reply(texts.PREMIUM_ALREADY_ACTIVE.format(status=status))
        return

    text = texts.PREMIUM_INFO.format(
        free_filter_limit=settings.free_filter_limit,
        price_30d=settings.premium_30d_price_stars,
        price_lifetime=settings.premium_lifetime_price_stars,
        status=status,
    )
    await message.reply(text, reply_markup=_premium_keyboard())


@router.callback_query(F.data.startswith("premium_buy:"))
async def on_premium_buy_button(callback: CallbackQuery, bot: Bot) -> None:
    if not callback.message:
        await callback.answer()
        return

    chat_id = callback.message.chat.id
    user_id = callback.from_user.id

    if not await is_chat_admin(bot, chat_id, user_id):
        await callback.answer(texts.PREMIUM_ONLY_ADMIN_CAN_BUY, show_alert=True)
        return

    _, plan = callback.data.split(":", maxsplit=1)
    await callback.answer()
    await _send_invoice(bot, chat_id, plan)


async def _send_invoice(bot: Bot, chat_id: int, plan: str) -> None:
    if plan == _PLAN_LIFETIME:
        title = texts.INVOICE_TITLE_LIFETIME
        description = texts.INVOICE_DESC_LIFETIME
        price = settings.premium_lifetime_price_stars
        payload = f"premium:{_PLAN_LIFETIME}:{chat_id}"
    else:
        plan = _PLAN_30D
        title = texts.INVOICE_TITLE_30D
        description = texts.INVOICE_DESC_30D
        price = settings.premium_30d_price_stars
        payload = f"premium:{_PLAN_30D}:{chat_id}"

    # Telegram Stars uchun currency doim "XTR", provider_token bo'sh
    # bo'lishi kerak (Stars uchun tashqi to'lov provideri kerak emas).
    await bot.send_invoice(
        chat_id=chat_id,
        title=title,
        description=description,
        payload=payload,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=title, amount=price)],
    )


@router.pre_checkout_query()
async def on_pre_checkout(pre_checkout_query: PreCheckoutQuery, bot: Bot) -> None:
    # Hozircha maxsus tekshiruv shart emas - hammasini tasdiqlaymiz.
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@router.message(F.successful_payment)
async def on_successful_payment(message: Message) -> None:
    payment = message.successful_payment
    payload = payment.invoice_payload or ""
    parts = payload.split(":")
    if len(parts) != 3 or parts[0] != "premium":
        return

    _, plan, chat_id_str = parts
    try:
        chat_id = int(chat_id_str)
    except ValueError:
        chat_id = message.chat.id

    lifetime = plan == _PLAN_LIFETIME
    await db.grant_premium(chat_id, lifetime=lifetime, days=settings.premium_30d_days)

    admin_name = user_display_name(message.from_user) if message.from_user else "?"
    await db.record_payment(
        chat_id=chat_id,
        user_id=message.from_user.id if message.from_user else 0,
        user_name=admin_name,
        plan=plan,
        amount_stars=payment.total_amount,
        telegram_charge_id=payment.telegram_payment_charge_id,
    )

    plan_label = "Umrbod" if lifetime else f"{settings.premium_30d_days} kunlik"
    await message.answer(texts.PAYMENT_SUCCESS.format(plan=plan_label))


# ------------------------------------------------------------------
# /grantpremium - bot egasi (super-admin) tomonidan qo'lda premium berish
# (tezkor, matn-buyruq orqali - guruh ichida yoki chat_id bilan istalgan
# joydan ishlaydi). Pastroqda "/premiumber" ham bor - u esa faqat DM'da,
# tugmali (chat tanlash -> reja tanlash) qulayroq interfeys beradi.
# Ikkisi ham qolsin - vaziyatga qarab foydalanuvchi qay birini
# ishlatishni o'zi tanlaydi.
# ------------------------------------------------------------------


@router.message(Command("grantpremium"))
async def cmd_grantpremium(message: Message, command: CommandObject, bot: Bot) -> None:
    """
    Faqat bot egasi (SUPER_ADMINS) ishlatishi mumkin. Ikki xil ishlatish
    tartibi bor:

    1. Guruh ICHIDA yozilsa: "/grantpremium 30d" yoki "/grantpremium lifetime"
       - shu joriy guruhga premium beriladi.
    2. Istalgan joyda (masalan bot egasining shaxsiy chatida) yozilsa:
       "/grantpremium <chat_id> 30d" yoki "/grantpremium <chat_id> lifetime"
       - berilgan chat_id'ga premium beriladi (guruhda turib yozish shart
       emas).
    """
    if not message.from_user or not is_super_admin(message.from_user.id):
        await message.reply(texts.GRANTPREMIUM_ONLY_SUPERADMIN)
        return

    args = (command.args or "").strip().split()
    if not args:
        await message.reply(texts.GRANTPREMIUM_USAGE)
        return

    target_chat_id: int | None = None
    plan_token: str

    if len(args) == 1:
        # Faqat reja ko'rsatilgan - joriy chatga beramiz (guruh bo'lishi kerak).
        plan_token = args[0].lower()
        if message.chat.type not in ("group", "supergroup"):
            await message.reply(texts.GRANTPREMIUM_USAGE)
            return
        target_chat_id = message.chat.id
    else:
        # Birinchi argument chat_id bo'lishi kerak.
        chat_id_raw = args[0].lstrip("-")
        if not chat_id_raw.isdigit():
            await message.reply(texts.GRANTPREMIUM_BAD_CHAT_ID)
            return
        target_chat_id = int(args[0])
        plan_token = args[1].lower()

    if plan_token not in ("30d", "lifetime"):
        await message.reply(texts.GRANTPREMIUM_USAGE)
        return

    lifetime = plan_token == "lifetime"
    await db.grant_premium(target_chat_id, lifetime=lifetime, days=settings.premium_30d_days)

    plan_label = "Umrbod" if lifetime else f"{settings.premium_30d_days} kunlik"

    row = await db.get_chat_settings(target_chat_id)
    chat_title = row["chat_title"] if row and row["chat_title"] else str(target_chat_id)

    await message.reply(texts.GRANTPREMIUM_DONE.format(chat_title=chat_title, plan_label=plan_label))

    # Guruhning o'ziga ham "premium yoqildi" deb alohida xabar yuboramiz -
    # aynan shu narsa yo'qligi ("admin kimdur premium ochsa, premium
    # ochildi deb aytmaydi") foydalanuvchi shikoyati edi.
    if target_chat_id != message.chat.id:
        try:
            await bot.send_message(
                target_chat_id, texts.GRANTPREMIUM_ANNOUNCE.format(plan_label=plan_label)
            )
        except TelegramAPIError:
            pass


# ------------------------------------------------------------------
# /broadcast - bot egasi (super-admin) barcha guruhlarga xabar yuborish
# ------------------------------------------------------------------


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, command: CommandObject, bot: Bot) -> None:
    """
    Faqat bot egasi (SUPER_ADMINS) ishlatishi mumkin - bot ishlab turgan
    BARCHA guruhlarga bir vaqtning o'zida xabar yuboradi. Bu "premium"
    darajadagi (bot egasiga tegishli) vosita, chunki oddiy admin faqat
    o'z guruhiga yozadi, bu esa butun tarmoqqa ta'sir qiladi.
    """
    if not message.from_user or not is_super_admin(message.from_user.id):
        await message.reply(texts.BROADCAST_ONLY_SUPERADMIN)
        return

    text = (command.args or "").strip()
    if not text:
        await message.reply(texts.BROADCAST_USAGE)
        return

    chats = await db.list_all_chats()
    if not chats:
        await message.reply(texts.BROADCAST_NO_CHATS)
        return

    await message.reply(texts.BROADCAST_STARTED.format(count=len(chats)))

    broadcast_text = texts.BROADCAST_MESSAGE_PREFIX + text
    success = 0
    failed = 0
    for row in chats:
        try:
            await bot.send_message(row["chat_id"], broadcast_text)
            success += 1
        except TelegramAPIError:
            failed += 1
        await asyncio.sleep(settings.broadcast_delay_sec)

    await message.answer(texts.BROADCAST_DONE.format(success=success, failed=failed))


# ------------------------------------------------------------------
# /premiumber - BOT EGASI (super-admin) uchun, FAQAT DM'da: xohlagan
# guruhga to'lovsiz (bepul) premium berish yoki bekor qilish. Tugmalar
# orqali guruh, keyin reja tanlanadi - hech qanday to'lov so'ralmaydi.
# ------------------------------------------------------------------


def _premiumber_chats_keyboard(chats: list) -> InlineKeyboardMarkup:
    now = time.time()
    rows: list[list[InlineKeyboardButton]] = []
    for row in chats:
        is_premium = bool(row["premium_lifetime"]) or (
            row["premium_until"] and row["premium_until"] > now
        )
        mark = "⭐ " if is_premium else ""
        title = row["chat_title"] or f"ID: {row['chat_id']}"
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{mark}{title}"[:64],
                    callback_data=f"premberish_chat:{row['chat_id']}",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _premiumber_plan_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=texts.PREMIUMBER_BTN_30D,
                    callback_data=f"premberish_plan:{chat_id}:30d",
                )
            ],
            [
                InlineKeyboardButton(
                    text=texts.PREMIUMBER_BTN_LIFETIME,
                    callback_data=f"premberish_plan:{chat_id}:lifetime",
                )
            ],
            [
                InlineKeyboardButton(
                    text=texts.PREMIUMBER_BTN_REVOKE,
                    callback_data=f"premberish_plan:{chat_id}:revoke",
                )
            ],
            [
                InlineKeyboardButton(
                    text=texts.PREMIUMBER_BTN_BACK,
                    callback_data="premberish_back",
                )
            ],
        ]
    )


async def _chat_status_label(row) -> str:
    now = time.time()
    if row["premium_lifetime"]:
        return "✅ Umrbod premium yoqilgan"
    if row["premium_until"] and row["premium_until"] > now:
        # MUHIM: `datetime.fromtimestamp()` to'g'ridan-to'g'ri ishlatilsa,
        # server (Railway) UTC vaqt zonasida ishlagani uchun sana noto'g'ri
        # chiqadi ("soat hato" bugi - shu sabab bu yerda ham loyihaning
        # yagona to'g'ri vositasi `format_timestamp()` (Toshkent, UTC+5)
        # ishlatiladi, xuddi boshqa hamma joyda bo'lgani kabi.
        date_str = format_timestamp(row["premium_until"], "%d.%m.%Y")
        return f"✅ Premium yoqilgan, {date_str} gacha"
    return "❌ Premium yo'q"


@router.message(Command("premiumber"))
async def cmd_premiumber(message: Message, bot: Bot) -> None:
    if not message.from_user or not is_super_admin(message.from_user.id):
        # Bot egasi bo'lmaganlarga bu ichki vositaning borligini ham
        # bildirmaymiz.
        return

    if message.chat.type != "private":
        me = await bot.get_me()
        await message.reply(
            texts.PREMIUMBER_ONLY_DM.format(bot_username=f"@{me.username}")
        )
        return

    chats = await db.list_all_chats()
    if not chats:
        await message.answer(texts.PREMIUMBER_NO_CHATS)
        return

    await message.answer(
        texts.PREMIUMBER_PICK_CHAT_HEADER,
        reply_markup=_premiumber_chats_keyboard(chats),
    )


@router.callback_query(F.data == "premberish_back")
async def on_premiumber_back(callback: CallbackQuery) -> None:
    if (
        not callback.message
        or not callback.from_user
        or not is_super_admin(callback.from_user.id)
        or callback.message.chat.type != "private"
    ):
        await callback.answer()
        return

    chats = await db.list_all_chats()
    await callback.answer()
    if not chats:
        await callback.message.edit_text(texts.PREMIUMBER_NO_CHATS)
        return
    await callback.message.edit_text(
        texts.PREMIUMBER_PICK_CHAT_HEADER,
        reply_markup=_premiumber_chats_keyboard(chats),
    )


@router.callback_query(F.data.startswith("premberish_chat:"))
async def on_premiumber_pick_chat(callback: CallbackQuery) -> None:
    if (
        not callback.message
        or not callback.from_user
        or not is_super_admin(callback.from_user.id)
        or callback.message.chat.type != "private"
    ):
        await callback.answer()
        return

    _, chat_id_str = callback.data.split(":", maxsplit=1)
    chat_id = int(chat_id_str)

    row = await db.get_chat_settings(chat_id)
    chat_title = (row["chat_title"] if row else None) or f"ID: {chat_id}"
    status = await _chat_status_label(row) if row else "❌ Premium yo'q"

    await callback.answer()
    await callback.message.edit_text(
        texts.PREMIUMBER_PICK_PLAN_HEADER.format(chat_title=chat_title, status=status),
        reply_markup=_premiumber_plan_keyboard(chat_id),
    )


@router.callback_query(F.data.startswith("premberish_plan:"))
async def on_premiumber_pick_plan(callback: CallbackQuery, bot: Bot) -> None:
    if (
        not callback.message
        or not callback.from_user
        or not is_super_admin(callback.from_user.id)
        or callback.message.chat.type != "private"
    ):
        await callback.answer()
        return

    _, chat_id_str, plan = callback.data.split(":", maxsplit=2)
    chat_id = int(chat_id_str)

    row = await db.get_chat_settings(chat_id)
    chat_title = (row["chat_title"] if row else None) or f"ID: {chat_id}"

    if plan == _PLAN_LIFETIME:
        await db.grant_premium(chat_id, lifetime=True)
        result_text = texts.PREMIUMBER_GRANTED_LIFETIME.format(chat_title=chat_title)
    elif plan == "revoke":
        await db.revoke_premium(chat_id)
        result_text = texts.PREMIUMBER_REVOKED.format(chat_title=chat_title)
    else:
        await db.grant_premium(
            chat_id, lifetime=False, days=settings.premium_30d_days
        )
        result_text = texts.PREMIUMBER_GRANTED_30D.format(chat_title=chat_title)

    await callback.answer("✅")
    await callback.message.edit_text(result_text)
