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

    # ------------------------------------------------------------------
    # @admin/@admins ping va /tag sozlamalari
    # ------------------------------------------------------------------
    # @admin yozilganda adminlarni qayta-qayta chaqirib "spam" bo'lib
    # qolmasligi uchun, bir foydalanuvchi shu vaqt ichida faqat bir marta
    # admin(lar)ni chaqira oladi (soniyada).
    admin_ping_cooldown_sec: int = 30

    # /tag bilan bir vaqtda nechta a'zoni chaqirish (bitta xabarda) va
    # xabarlar orasidagi kutish vaqti (Telegram flood-limitiga tushmaslik
    # uchun).
    tag_batch_size: int = 5
    tag_batch_delay_sec: float = 1.5

    # ------------------------------------------------------------------
    # CS2 (Counter-Strike 2) narx qidiruvi - SKINPORT.COM
    # ------------------------------------------------------------------
    # ".skin <nom>" yoki ".oruzhiya <nom>" yozilganda Skinport.com
    # bozoridan (birinchi navbatda) shu buyum narxini olib, dollar va
    # so'mda ko'rsatadi. Skinport'ning /v1/items endpointi RASMIY
    # hujjatlashtirilgan va avtorizatsiyasiz ishlaydi
    # (https://docs.skinport.com/items). Agar u javob bermasa/topilmasa,
    # Steam Community Market'ga (zaxira manba) avtomatik o'tadi.
    cs2_market_enabled: bool = field(
        default_factory=lambda: os.getenv("CS2_MARKET_ENABLED", "true").strip().lower()
        not in ("0", "false", "off", "no")
    )
    # CS2 (Counter-Strike 2) ning Steam/Skinport'dagi ilova ID'si.
    cs2_app_id: int = 730
    # 1 AQSH dollari nechchi O'zbek so'miga teng ekanligi. Bu qiymatni
    # kerak bo'lganda `.env`/Railway Variables orqali (USD_TO_UZS_RATE)
    # yangilab turishingiz mumkin - haqiqiy vaqtdagi kursni tekshirish
    # uchun tashqi valyuta-API ishlatilmagan (qo'shimcha tashqi
    # bog'liqlik/nosozlik nuqtasi bo'lmasin degan maqsadda).
    usd_to_uzs_rate: float = field(
        default_factory=lambda: float(os.getenv("USD_TO_UZS_RATE", "12500"))
    )
    # Narx manbasiga so'roviga javob kutish vaqti (soniya).
    cs2_market_timeout_sec: float = 8.0
    # Bir foydalanuvchi qanchа tez-tez narx so'rashi mumkin (spam/manbani
    # haddan tashqari ko'p so'rov bilan bloklatib qo'ymaslik uchun).
    cs2_market_cooldown_sec: int = 5
    # Skinport narxlar javobini xotirada qanchа vaqt saqlash (soniya) -
    # Skinport'ning rate-limiti 5 daqiqada 8 so'rov, shu sabab keshlash
    # shart (aks holda tez orada 429 xatosiga uchraymiz).
    lis_skins_cache_ttl_sec: int = 10 * 60


settings = Settings()


def is_super_admin(user_id: int) -> bool:
    """
    Bot egasi/super-adminlari - ular uchun barcha premium funksiyalar
    har doim va har qanday guruhda tekin ishlaydi (guruh premium
    xarid qilmagan bo'lsa ham).
    """
    return user_id in settings.super_admins
