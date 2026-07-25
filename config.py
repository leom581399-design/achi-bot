"""
ACHI BOT - konfiguratsiya modul.

Sozlamalar .env faylidan (yoki Railway/Fly "Variables"dan) o'qiladi.

MUHIM: BOT_TOKEN va shunga o'xshash MAXFIY qiymatlar hech qachon shu
faylga to'g'ridan-to'g'ri yozilmaydi - faqat environment variable orqali
beriladi. Aks holda token kod bilan birga ochiq GitHub repoga tushib
qoladi va uni har kim ko'rib, botni to'liq boshqarib olishi mumkin
(bu holat avval yuz bergan va tuzatilgan edi - qayta takrorlanmasin).
BOT_TOKEN sozlanmagan bo'lsa, bot main.py'da aniq xato bilan to'xtaydi
(pastga qarang - jim ishlab, keyin tushunarsiz xato berish o'rniga).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()

# Bot egasi (super-admin) uchun standart zaxira ID - agar Railway/Fly
# "Variables"da SUPER_ADMINS umuman sozlanmagan bo'lsa ishlatiladi.
# Bu MAXFIY qiymat EMAS (shunchaki Telegram user ID, token/parol emas),
# shu sabab kodda turishi xavfsiz - lekin SUPER_ADMINS environment
# variable sozlansa, u har doim ustunlik qiladi (pastdagi _parse_int_list
# chaqiruviga qarang).
_DEFAULT_SUPER_ADMINS = "8539436212"


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
        default_factory=lambda: os.getenv("BOT_TOKEN", "").strip()
    )
    super_admins: list[int] = field(
        default_factory=lambda: _parse_int_list(
            os.getenv("SUPER_ADMINS") or _DEFAULT_SUPER_ADMINS
        )
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

    # /broadcast - har guruhga xabar yuborish orasidagi kutish vaqti
    # (Telegram'ning "bir botdan ko'p guruhga tez-tez xabar yuborish"
    # flood-limitiga tushib qolmaslik uchun).
    broadcast_delay_sec: float = 0.05

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

    # LIS-SKINS.COM API kaliti (asosiy narx manbasi). Hisobingizda:
    # https://lis-skins.com -> Steam orqali kiring -> profil sozlamalari
    # ichidan "API" bo'limini toping -> kalitni generatsiya qiling.
    # BU YERGA TO'G'RIDAN-TO'G'RI YOZMANG - faqat .env yoki Railway/Fly
    # "Variables" orqali LIS_SKINS_API_KEY sifatida bering (xavfsizlik
    # uchun, xuddi BOT_TOKEN kabi). Agar bo'sh bo'lsa, LIS-SKINS manbasi
    # avtomatik o'tkazib yuboriladi va bot Skinport/Steam'ga o'tadi.
    lis_skins_api_key: str = field(
        default_factory=lambda: os.getenv("LIS_SKINS_API_KEY", "").strip()
    )

    # ------------------------------------------------------------------
    # AI-yordamchi funksiyalar (premium) - AQLLI moderatsiya va AQLLI
    # hisobot xulosasi
    # ------------------------------------------------------------------
    # OpenAI-mos (Chat Completions) API. Agar AI_API_KEY bo'sh bo'lsa,
    # bu ikki funksiya ODDIY (kalitsiz) qoida-asosli zaxira mantiqqa
    # o'tadi - bot baribir ishlayveradi, faqat "aqli" kamroq bo'ladi.
    # BU YERGA TO'G'RIDAN-TO'G'RI KALIT YOZMANG - faqat .env/Railway/Fly
    # "Variables" orqali beriladi (xuddi BOT_TOKEN kabi).
    ai_api_key: str = field(default_factory=lambda: os.getenv("AI_API_KEY", "").strip())
    ai_api_url: str = field(
        default_factory=lambda: os.getenv(
            "AI_API_URL", "https://api.openai.com/v1/chat/completions"
        ).strip()
    )
    ai_model: str = field(default_factory=lambda: os.getenv("AI_MODEL", "gpt-4o-mini").strip())
    ai_timeout_sec: float = 12.0

    @property
    def ai_enabled(self) -> bool:
        return bool(self.ai_api_key)


settings = Settings()


def is_super_admin(user_id: int) -> bool:
    """
    Bot egasi/super-adminlari - ular uchun barcha premium funksiyalar
    har doim va har qanday guruhda tekin ishlaydi (guruh premium
    xarid qilmagan bo'lsa ham).
    """
    return user_id in settings.super_admins
