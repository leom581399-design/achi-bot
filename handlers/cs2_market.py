"""
ACHI BOT - CS2 (Counter-Strike 2) Steam Market narx qidiruvi.

Guruh a'zosi ".skin <nom>" yoki ".oruzhiya <nom>" deb yozganda, bot
Steam Community Market'ning (hujjatlashtirilmagan, lekin keng
ishlatiladigan) `priceoverview` endpointiga so'rov yuborib, buyumning
eng arzon narxini oladi va foydalanuvchiga dollar + so'mda ko'rsatadi.

Eslatma: bu Steam'ning rasmiy/kafolatlangan API'si emas, shu sabab
formatida o'zgarish bo'lishi mumkin. Xatolik bo'lsa, bot buni chiroyli
xabar bilan bildiradi (aiohttp so'rovi try/except bilan o'ralgan).
"""
from __future__ import annotations

import time
import urllib.parse

import aiohttp
from aiogram import F, Router
from aiogram.types import Message

import texts
from config import settings
from database import db

router = Router(name="cs2_market")

_STEAM_PRICEOVERVIEW_URL = "https://steamcommunity.com/market/priceoverview/"

# Har foydalanuvchi uchun oxirgi so'rov vaqti (spam va Steam'ni haddan
# tashqari ko'p so'rov bilan bloklatib qo'ymaslik uchun).
_last_lookup: dict[tuple[int, int], float] = {}


def _extract_item_name(text: str) -> str | None:
    """
    ".skin AK-47 | Redline" yoki ".oruzhiya AK-47 | Redline" matnidan
    buyum nomini ajratib oladi.
    """
    stripped = text.strip()
    for prefix in (".skin", ".oruzhiya", ".oruzhya", ".weapon"):
        if stripped.lower().startswith(prefix):
            name = stripped[len(prefix):].strip()
            return name or None
    return None


async def _fetch_price(item_name: str) -> dict | None:
    params = {
        "appid": str(settings.cs2_app_id),
        "currency": "1",  # 1 = USD
        "market_hash_name": item_name,
    }
    url = f"{_STEAM_PRICEOVERVIEW_URL}?{urllib.parse.urlencode(params)}"

    timeout = aiohttp.ClientTimeout(total=settings.cs2_market_timeout_sec)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json(content_type=None)
    except Exception:
        return None

    if not data or not data.get("success"):
        return None
    return data


def _parse_usd(price_str: str | None) -> float | None:
    """
    Steam'dan keladigan USD narx matnini songa aylantiradi.

    Biz har doim currency=1 (USD) so'raymiz, shu sabab format har doim
    bitta xil bo'ladi: "$1.23" (kichik summa) yoki "$1,234.56" (1000
    dollardan katta summalarda vergul mingliklar ajratkichi sifatida
    ishlatiladi, nuqta esa kasr qismi). Shu sabab avval vergulni butunlay
    olib tashlaymiz (mingliklar ajratkichi), keyin faqat raqam va
    nuqtani qoldiramiz.
    """
    if not price_str:
        return None
    cleaned = price_str.replace("$", "").replace(",", "").strip()
    digits = "".join(ch for ch in cleaned if ch.isdigit() or ch == ".")
    try:
        return float(digits)
    except ValueError:
        return None


@router.message(
    F.chat.type.in_({"group", "supergroup"}),
    F.text.regexp(r"(?i)^\.(skin|oruzhiya|oruzhya|weapon)\b"),
)
async def on_skin_lookup(message: Message) -> None:
    if not settings.cs2_market_enabled:
        return
    if not message.text or not message.from_user:
        return

    chat_settings = await db.get_chat_settings(message.chat.id)
    # cs2_market guruh darajasida o'chirilishi mumkin (kelajakda
    # /cs2market on|off qo'shilsa shu yerga ulanadi); hozircha global
    # sozlama (config.cs2_market_enabled) yetarli.

    item_name = _extract_item_name(message.text)
    if not item_name:
        await message.reply(texts.CS2_MARKET_USAGE)
        return

    key = (message.chat.id, message.from_user.id)
    now = time.time()
    last = _last_lookup.get(key)
    if last and now - last < settings.cs2_market_cooldown_sec:
        remaining = int(settings.cs2_market_cooldown_sec - (now - last))
        await message.reply(texts.CS2_MARKET_COOLDOWN.format(seconds=remaining))
        return
    _last_lookup[key] = now

    searching_msg = await message.reply(
        texts.CS2_MARKET_SEARCHING.format(name=item_name)
    )

    data = await _fetch_price(item_name)
    if data is None:
        await searching_msg.edit_text(texts.CS2_MARKET_NOT_FOUND)
        return

    usd_price = _parse_usd(data.get("lowest_price") or data.get("median_price"))
    if usd_price is None:
        await searching_msg.edit_text(texts.CS2_MARKET_NOT_FOUND)
        return

    uzs_price = usd_price * settings.usd_to_uzs_rate
    usd_str = f"{usd_price:.2f}"
    uzs_str = f"{uzs_price:,.0f}".replace(",", " ")

    volume = data.get("volume")
    if volume:
        text = texts.CS2_MARKET_RESULT_WITH_VOLUME.format(
            name=item_name, usd=usd_str, uzs=uzs_str, volume=volume
        )
    else:
        text = texts.CS2_MARKET_RESULT.format(name=item_name, usd=usd_str, uzs=uzs_str)

    try:
        await searching_msg.edit_text(text)
    except Exception:
        await message.reply(text)
