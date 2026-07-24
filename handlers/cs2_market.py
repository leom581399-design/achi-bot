"""
ACHI BOT - CS2 (Counter-Strike 2) narx qidiruvi.

Guruh a'zosi ".skin <nom>" yoki ".oruzhiya <nom>" deb yozganda:

1. Avval `cs2_items.search()` orqali yozilgan qisqa/to'liqsiz nomni
   (masalan "ak47 redline") Steam'dagi TO'LIQ market_hash_name shakliga
   ("AK-47 | Redline (Field-Tested)") aylantiramiz - fuzzy qidiruv.
2. Agar bir nechta mos nom topilsa, foydalanuvchiga tanlash uchun
   tugmalar chiqaramiz.
3. Narxni birinchi navbatda LIS-SKINS.COM'dan olishga harakat qilamiz
   (asosiy manba, foydalanuvchi so'roviga ko'ra). Agar u javob
   bermasa/topilmasa, Steam Community Market'ga (zaxira manba) o'tamiz.
4. Natijani dollar va so'mda, qaysi manbadan olinganini ko'rsatib beramiz.

MUHIM ESLATMA: LIS-SKINS.COM'ning ochiq (avtorizatsiyasiz) narx eksport
manzili rasmiy hujjatlashtirilmagan - bu manzil (`config.lis_skins_export_url`)
shu turdagi bozorlarda (market.csgo.com va h.k.) keng tarqalgan
konventsiyaga asoslangan taxmin. Agar u ishlamasa, bot avtomatik Steam'ga
o'tadi, shu sabab foydalanuvchi baribir narxni oladi.
"""
from __future__ import annotations

import re
import time
import urllib.parse

import aiohttp
from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import cs2_items
import texts
from config import settings

router = Router(name="cs2_market")

_STEAM_PRICEOVERVIEW_URL = "https://steamcommunity.com/market/priceoverview/"

# Har foydalanuvchi uchun oxirgi so'rov vaqti (spam va manbani haddan
# tashqari ko'p so'rov bilan bloklatib qo'ymaslik uchun).
_last_lookup: dict[tuple[int, int], float] = {}

# LIS-SKINS export faylini xotirada keshlash - har safar 20K+ buyumlik
# faylni qayta yuklab olmaslik uchun.
_lis_skins_cache: dict[str, float] = {"loaded_at": 0.0}
_lis_skins_prices: dict[str, dict] = {}

# Bir nechta mos natija chiqganda, foydalanuvchi tugma bosganda qaysi
# nomni tanlaganini bilish uchun (callback_data qisqa bo'lishi kerak,
# shu sabab to'liq nomni emas, indeksni saqlaymiz).
_pending_choices: dict[str, list[str]] = {}
_PENDING_CHOICE_TTL_SEC = 5 * 60


def _cleanup_pending_choices(now: float) -> None:
    """
    Eski (5 daqiqadan ortiq) tanlov yozuvlarini xotiradan tozalaydi -
    aks holda vaqt o'tishi bilan xotira sizib chiqishi (memory leak)
    mumkin edi, chunki har bir ko'p-natijali qidiruv yangi yozuv
    qo'shardi va hech qachon o'chirilmasdi.
    """
    if len(_pending_choices) < 50:
        return
    expired = [
        key
        for key in _pending_choices
        if now - float(key.rsplit(":", maxsplit=1)[-1]) > _PENDING_CHOICE_TTL_SEC
    ]
    for key in expired:
        _pending_choices.pop(key, None)


def _extract_item_query(text: str) -> str | None:
    """
    ".skin AK-47 Redline" yoki ".oruzhiya ak47 redline" matnidan
    qidiruv so'zini ajratib oladi (to'liq Steam nomi shart emas).
    """
    stripped = text.strip()
    for prefix in (".skin", ".oruzhiya", ".oruzhya", ".weapon"):
        if stripped.lower().startswith(prefix):
            query = stripped[len(prefix):].strip()
            return query or None
    return None


# ------------------------------------------------------------------
# LIS-SKINS.COM (asosiy manba)
# ------------------------------------------------------------------


async def _load_lis_skins_prices() -> dict[str, dict]:
    """
    LIS-SKINS export faylini yuklab, {market_hash_name: {...}} lug'atiga
    aylantiradi. Xotirada `lis_skins_cache_ttl_sec` davomida saqlanadi.
    Xatolik bo'lsa (manzil ishlamasa, format o'zgargan bo'lsa) bo'sh
    lug'at qaytaradi - bu holatda chaqiruvchi Steam'ga o'tadi.
    """
    now = time.time()
    if (
        _lis_skins_prices
        and now - _lis_skins_cache["loaded_at"] < settings.lis_skins_cache_ttl_sec
    ):
        return _lis_skins_prices

    timeout = aiohttp.ClientTimeout(total=settings.cs2_market_timeout_sec)
    headers = {}
    if settings.lis_skins_api_key:
        headers["Authorization"] = f"Bearer {settings.lis_skins_api_key}"

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                settings.lis_skins_export_url, headers=headers
            ) as resp:
                if resp.status != 200:
                    return {}
                data = await resp.json(content_type=None)
    except Exception:
        return {}

    parsed = _parse_lis_skins_payload(data)
    if parsed:
        _lis_skins_prices.clear()
        _lis_skins_prices.update(parsed)
        _lis_skins_cache["loaded_at"] = now
    return _lis_skins_prices


def _parse_lis_skins_payload(data) -> dict[str, dict]:
    """
    LIS-SKINS'ning export formatini {market_hash_name: {price, count}}
    ko'rinishiga o'tkazadi. Bir nechta ehtimoliy formatni qo'llab-quvvatlaydi
    (ro'yxat yoki lug'at, chunki eksport manzilining aniq strukturasi
    tasdiqlanmagan).
    """
    result: dict[str, dict] = {}
    if isinstance(data, dict) and "items" in data:
        data = data["items"]

    if isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                continue
            name = item.get("market_hash_name") or item.get("name")
            price = item.get("price") or item.get("min_price") or item.get("price_min")
            if name and price is not None:
                result[name] = {"price": price, "count": item.get("count") or item.get("quantity")}
    elif isinstance(data, dict):
        for name, value in data.items():
            if isinstance(value, dict):
                price = value.get("price") or value.get("min_price")
                count = value.get("count") or value.get("quantity")
            else:
                price = value
                count = None
            if price is not None:
                result[name] = {"price": price, "count": count}

    return result


async def _fetch_from_lis_skins(item_name: str) -> tuple[float, int | None] | None:
    prices = await _load_lis_skins_prices()
    if not prices:
        return None

    entry = prices.get(item_name)
    if entry is None:
        return None

    try:
        price = float(entry["price"])
    except (TypeError, ValueError):
        return None

    count = entry.get("count")
    try:
        count = int(count) if count is not None else None
    except (TypeError, ValueError):
        count = None

    return price, count


# ------------------------------------------------------------------
# Steam Community Market (zaxira manba)
# ------------------------------------------------------------------


async def _fetch_from_steam(item_name: str) -> tuple[float, int | None] | None:
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

    price = _parse_usd(data.get("lowest_price") or data.get("median_price"))
    if price is None:
        return None

    volume = data.get("volume")
    try:
        volume = int(str(volume).replace(",", "")) if volume else None
    except (TypeError, ValueError):
        volume = None

    return price, volume


def _parse_usd(price_str: str | None) -> float | None:
    """
    Steam'dan keladigan USD narx matnini songa aylantiradi. Har doim
    currency=1 (USD) so'raymiz, shu sabab format bitta xil: "$1.23"
    (kichik summa) yoki "$1,234.56" (1000 dollardan katta summalarda
    vergul mingliklar ajratkichi). Shu sabab avval vergulni butunlay
    olib tashlaymiz, keyin faqat raqam va nuqtani qoldiramiz.
    """
    if not price_str:
        return None
    cleaned = price_str.replace("$", "").replace(",", "").strip()
    digits = "".join(ch for ch in cleaned if ch.isdigit() or ch == ".")
    try:
        return float(digits)
    except ValueError:
        return None


async def _fetch_price_with_fallback(
    item_name: str,
) -> tuple[float, int | None, str] | None:
    """Avval LIS-SKINS, topilmasa Steam'dan narxni oladi."""
    lis_result = await _fetch_from_lis_skins(item_name)
    if lis_result is not None:
        price, count = lis_result
        return price, count, texts.CS2_MARKET_SOURCE_LISSKINS

    steam_result = await _fetch_from_steam(item_name)
    if steam_result is not None:
        price, volume = steam_result
        return price, volume, texts.CS2_MARKET_SOURCE_STEAM

    return None


async def _send_price_result(message: Message, item_name: str) -> None:
    result = await _fetch_price_with_fallback(item_name)
    if result is None:
        await message.answer(texts.CS2_MARKET_NOT_FOUND)
        return

    usd_price, volume, source = result
    uzs_price = usd_price * settings.usd_to_uzs_rate
    usd_str = f"{usd_price:.2f}"
    uzs_str = f"{uzs_price:,.0f}".replace(",", " ")

    if volume:
        text = texts.CS2_MARKET_RESULT_WITH_VOLUME.format(
            name=item_name, usd=usd_str, uzs=uzs_str, volume=volume, source=source
        )
    else:
        text = texts.CS2_MARKET_RESULT.format(
            name=item_name, usd=usd_str, uzs=uzs_str, source=source
        )

    await message.answer(text)


# ------------------------------------------------------------------
# Handler: ".skin <nom>" / ".oruzhiya <nom>"
# ------------------------------------------------------------------

_CS2_PREFIX_RE = re.compile(r"(?i)^\.(skin|oruzhiya|oruzhya|weapon)\b")


def _is_cs2_lookup_text(message: Message) -> bool:
    """
    Oddiy Python funksiyasi orqali tekshiruv - magic_filter'ning
    `F.text.regexp(...)` operatsiyasidan farqli o'laroq (u ham himoyalangan
    bo'lsa ham), aniq va tushunarli bo'lishi uchun oddiy funksiya
    ishlatilgan: `message.text is None` bo'lgan xabarlarda (rasm, stiker
    va h.k.) xech qanday muammo tug'dirmaydi.
    """
    return bool(message.text) and bool(_CS2_PREFIX_RE.search(message.text))


@router.message(
    F.chat.type.in_({"group", "supergroup"}),
    _is_cs2_lookup_text,
)
async def on_skin_lookup(message: Message) -> None:
    if not settings.cs2_market_enabled:
        return
    if not message.text or not message.from_user:
        return

    query = _extract_item_query(message.text)
    if not query:
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

    matches = cs2_items.search(query, limit=6)

    if not matches:
        # Ma'lumotlar bazasida topilmasa, foydalanuvchi yozgan nomni
        # to'g'ridan-to'g'ri narx manbalariga yuboramiz (balki u to'liq
        # va to'g'ri Steam nomi bo'lishi mumkin).
        searching_msg = await message.reply(
            texts.CS2_MARKET_SEARCHING.format(name=query)
        )
        try:
            await _send_price_result(searching_msg, query)
            await searching_msg.delete()
        except Exception:
            pass
        return

    if len(matches) == 1:
        searching_msg = await message.reply(
            texts.CS2_MARKET_SEARCHING.format(name=matches[0])
        )
        try:
            await _send_price_result(searching_msg, matches[0])
            await searching_msg.delete()
        except Exception:
            pass
        return

    # Bir nechta mos nom topilsa - tanlash tugmalari
    _cleanup_pending_choices(now)
    choice_key = f"{message.chat.id}:{message.from_user.id}:{int(now)}"
    _pending_choices[choice_key] = matches

    buttons = [
        [InlineKeyboardButton(text=name, callback_data=f"cs2pick:{choice_key}:{i}")]
        for i, name in enumerate(matches)
    ]
    await message.reply(
        texts.CS2_MULTI_RESULTS_HEADER.format(query=query),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data.startswith("cs2pick:"))
async def on_cs2_pick(callback: CallbackQuery) -> None:
    if not callback.data or not callback.message:
        await callback.answer()
        return

    # MUHIM: choice_key'ning o'zi ichida ":" belgilari bor
    # (chat_id:user_id:timestamp), shu sabab callback_data'ni
    # split(":", maxsplit=2) bilan ajratish XATO edi - bu choice_key'ni
    # noto'liq kesib, index_str'ga "789:1784931297:2" kabi qiymat
    # qoldirardi, va int(index_str) har doim ValueError berardi (shu
    # sabab tugma bosilganda hech narsa bo'lmasdi). To'g'ri yechim:
    # indeksni OXIRIDAN ajratib olish (u har doim oddiy son bo'ladi),
    # qolgan hammasi choice_key.
    parts = callback.data.split(":")
    if len(parts) < 3:
        await callback.answer()
        return
    index_str = parts[-1]
    choice_key = ":".join(parts[1:-1])
    try:
        index = int(index_str)
    except ValueError:
        await callback.answer()
        return

    matches = _pending_choices.get(choice_key)
    if not matches or index >= len(matches):
        await callback.answer(texts.CS2_MULTI_RESULTS_EXPIRED, show_alert=True)
        return

    item_name = matches[index]
    # Eslatma: ro'yxatni bu yerda pop qilmaymiz - chunki guruh xabari
    # bo'lgani uchun, boshqa odam ham (yoki shu odam) boshqa tugmani
    # (masalan "Field-Tested" o'rniga "Battle-Scarred") bosishni
    # xohlashi mumkin. Yozuv faqat vaqt bo'yicha (_cleanup_pending_choices
    # orqali, 5 daqiqadan keyin) tozalanadi.

    await callback.answer()
    try:
        await callback.message.edit_text(
            texts.CS2_MARKET_SEARCHING.format(name=item_name)
        )
    except Exception:
        pass

    await _send_price_result(callback.message, item_name)
