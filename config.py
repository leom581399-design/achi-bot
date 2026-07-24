"""
ACHI BOT - konfiguratsiya modul.

Sozlamalar .env faylidan o'qiladi (agar mavjud bo'lsa). BOT_TOKEN uchun
foydalanuvchining aniq so'roviga ko'ra, kodda standart (fallback) qiymat
sifatida haqiqiy token qo'yilgan - shu sabab .env yaratmasangiz ham,
Railway'da alohida environment variable sozlamasangiz ham bot ishlайdi.

Xohlasangiz, .env faylida yoki Railway "Variables" bo'limida BOT_TOKEN
qiymatini qo'yib, shu standart qiymatni istagan vaqtda ustidan yozishingiz
mumkin (masalan tokenni almashtirishga to'g'ri kelsa).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()

# Foydalanuvchi so'roviga ko'ra to'g'ridan-to'g'ri kodga joylashtirilgan
# standart bot tokeni (BotFather orqali olingan). .env/Railway Variables
# orqali BOT_TOKEN o'zgaruvchisi berilsa, o'sha ustunlik qiladi.
_DEFAULT_BOT_TOKEN = "8790777860:AAFt0Jv3x-01y6h7Z2rVKKDuHSOQ2mQy-UY"


def _parse_int_list(raw: str | None) -> list[int]:
    if not raw:
        return []
    result: list[int] = []
    for piece in raw.split(","):
        piece = piece.strip()
        if piece:
            try:
                result.append(int(piece))
            except ValueError:
                continue
    return result


@dataclass(frozen=True)
class Settings:
    bot_token: str = field(
        default_factory=lambda: os.getenv("BOT_TOKEN", "").strip() or _DEFAULT_BOT_TOKEN
    )
    super_admins: list[int] = field(
        default_factory=lambda: _parse_int_list(os.getenv("SUPER_ADMINS"))
    )
    report_chat_id: int | None = field(
        default_factory=lambda: (
            int(os.getenv("REPORT_CHAT_ID"))
            if os.getenv("REPORT_CHAT_ID", "").strip()
            else None
        )
    )
    db_path: str = field(default_factory=lambda: os.getenv("DB_PATH", "achi_bot.db"))
    reports_dir: str = field(
        default_factory=lambda: os.getenv("REPORTS_DIR", "reports")
    )

    # Standart cheklovlar
    max_warns: int = 3
    flood_message_limit: int = 6  # shu miqdordan ko'p xabar
    flood_time_window_sec: int = 8  # shu vaqt ichida yozilsa flood hisoblanadi
    hourly_report_interval_hours: int = 1

    # ------------------------------------------------------------------
    # Premium (Telegram Stars) sozlamalari
    # ------------------------------------------------------------------
    # Bepul guruhlarda filter/eslatma sonining chegarasi (premiumda cheksiz)
    free_filter_limit: int = 5
    free_note_limit: int = 5

    # Narxlar Telegram Stars (⭐) da. Bu yerdan xohlagancha o'zgartirishingiz
    # mumkin - Telegram Stars'da butun son ishlatiladi (tiyin/sent yo'q).
    premium_30d_price_stars: int = 150
    premium_lifetime_price_stars: int = 500
    premium_30d_days: int = 30


settings = Settings()


def is_super_admin(user_id: int) -> bool:
    """
    Bot egasi/super-adminlari - ular uchun barcha premium funksiyalar
    har doim va har qanday guruhda tekin ishlaydi (guruh premium
    xarid qilmagan bo'lsa ham).
    """
    return user_id in settings.super_admins
