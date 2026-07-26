"""
ACHI BOT - tungi rejim (premium) kuzatuvchisi.

Har daqiqada (main.py'dagi scheduler orqali) chaqiriladi: tungi rejim
yoqilgan barcha guruhlarni tekshirib, hozirgi soat oralig'ga to'g'ri
kelsa "all" qulfini yoqadi, to'g'ri kelmasa (va avval yoqilgan bo'lsa)
o'chiradi. Shu bilan guruh administratori hech narsa qilmasdan, bot
avtomatik ravishda kechasi guruhni yopib-ochib turadi.
"""
from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from database import db
from handlers.premium_extras import is_night_mode_active
from utils import now_tashkent

logger = logging.getLogger("achi_bot.night_mode")

# Har guruh uchun "hozir tunmi" holatini eslab turamiz - shundagina
# faqat HOLAT O'ZGARGANDA (kun->tun yoki tun->kun) qulfni
# yoqamiz/o'chiramiz, har daqiqada qayta-qayta emas.
_last_state: dict[int, bool] = {}


async def sweep_night_mode(bot: Bot) -> None:
    chats = await db.list_all_chats()
    now_hour = now_tashkent().hour

    for chat_row in chats:
        chat_id = chat_row["chat_id"]
        row = await db.get_chat_settings(chat_id)
        if not row or not row["night_mode_enabled"]:
            continue

        is_night = is_night_mode_active(row, now_hour)
        was_night = _last_state.get(chat_id, False)

        if is_night and not was_night:
            await db.set_lock(chat_id, "all")
            _last_state[chat_id] = True
            try:
                import texts

                await bot.send_message(chat_id, texts.NIGHTMODE_ACTIVE_NOTICE.format(end=row["night_end_hour"]))
            except TelegramAPIError:
                pass
        elif not is_night and was_night:
            await db.unset_lock(chat_id, "all")
            _last_state[chat_id] = False
