"""
ACHI BOT - CS2 (Counter-Strike 2) narx qidiruvi.

Guruh a'zosi ".skin <nom>" yoki ".oruzhiya <nom>" deb yozganda:

1. Avval `cs2_items.search()` orqali yozilgan qisqa/to'liqsiz nomni
   (masalan "ak47 redline") Steam'dagi TO'LIQ market_hash_name shakliga
   ("AK-47 | Redline (Field-Tested)") aylantiramiz - fuzzy qidiruv.
2. Agar bir nechta mos nom topilsa, foydalanuvchiga tanlash uchun
   tugmalar chiqaramiz.
3. Narxni **Skinport.com**'dan olamiz - bu CS2 skinlar uchun ochiq
   (avtorizatsiyasiz) va RASMIY hujjatlashtirilgan REST API
   (https://docs.skinport.com/items). Agar u javob bermasa/topilmasa,
   Steam Community Market'ga (zaxira manba) o'tamiz.
4. Natijani dollar va so'mda, qaysi manbadan olinganini ko'rsatib beramiz.

Eslatma: avvalgi versiyada LIS-SKINS.COM ishlatilgan edi, lekin uning
ochiq narx endpointi rasmiy tasdiqlanmagan (faqat avtorizatsiya talab
qiladigan API topildi). Skinport'ning ochiq API'si esa rasmiy
hujjatlashtirilgan va sinovdan o'tgan (barnumbirr/skinport ochiq kodli
Python wrapper orqali tasdiqlangan), shu sabab asosiy manba shu bo'ldi.
"""
from __future__ import annotations

import logging
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
logger = logging.getLogger("achi_bot.cs2_market")

_STEAM_PRICEOVERVIEW_URL = "https://steamcommunity.com/market/priceoverview/"
# Steam ba'zan User-Agent'siz so'rovlarni rad etadi/bloklaydi (ayniqsa
# server/datacenter IP manzillaridan kelganda) - shu sabab oddiy brauzer
# so'rovi kabi ko'rinish uchun sarlavha qo'shamiz.
_REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

# Har foydalanuvchi uchun oxirgi so'rov vaqti (spam va manbani haddan
# tashqari ko'p so'rov bilan bloklatib qo'ymaslik uchun).
_last_lookup: dict[tuple[int, int], float] = {}

# Skinport narxlarini xotirada keshlash - har safar minglab buyumlik
# javobni qayta yuklab olmaslik va rate-limitga tushmaslik uchun.
_skinport_cache: dict[str, float] = {"loaded_at": 0.0}
_skinport_prices: dict[str, dict] = {}

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
# SKINPORT.COM (asosiy manba) - rasmiy, ochiq, avtorizatsiyasiz API
# https://docs.skinport.com/items
# ------------------------------------------------------------------

_SKINPORT_ITEMS_URL = "https://api.skinport.com/v1/items"


async def _load_skinport_prices() -> dict[str, dict]:
    """
    Skinport'ning /v1/items endpointidan BARCHA CS2 buyumlarining
    narxini bir martada yuklab, {market_hash_name: {...}} lug'atiga
    aylantiradi. Xotirada `lis_skins_cache_ttl_sec` davomida saqlanadi
    (bir necha ming buyumni har so'rovda qayta yuklab olmaslik uchun).

    Skinport'ning rate-limiti 5 daqiqada 8 so'rov (endpoint guruhi
    bo'yicha) - shu sabab keshlash MUHIM, aks holda tez orada
    429 (Too Many Requests) xatosiga uchraymiz.
    """
    now = time.time()
    if (
        _skinport_prices
        and now - _skinport_cache["loaded_at"] < settings.lis_skins_cache_ttl_sec
    ):
        return _skinport_prices

    timeout = aiohttp.ClientTimeout(total=settings.cs2_market_timeout_sec)
    params = {
        "app_id": str(settings.cs2_app_id),
        "currency": "USD",
        "tradable": "false",  # tradable=false -> narxi bor barcha buyumlar
    }

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                _SKINPORT_ITEMS_URL, params=params, headers=_REQUEST_HEADERS
            ) as resp:
                if resp.status != 200:
                    logger.warning(
                        "Skinport /v1/items status=%s qaytardi (rate-limit "
                        "bo'lsa 429 bo'ladi)",
                        resp.status,
                    )
                    return {}
                data = await resp.json(content_type=None)
    except Exception as exc:
        logger.warning("Skinport /v1/items so'rovida xatolik: %r", exc)
        return {}

    parsed = _parse_skinport_payload(data)
    if parsed:
        _skinport_prices.clear()
        _skinport_prices.update(parsed)
        _skinport_cache["loaded_at"] = now
        logger.info("Skinport narxlari yuklandi: %d buyum", len(parsed))
    else:
        logger.warning(
            "Skinport javob berdi, lekin 0 buyum ajratildi (format o'zgargan "
            "bo'lishi mumkin) - javob turi: %s",
            type(data).__name__,
        )
    return _skinport_prices


def _parse_skinport_payload(data) -> dict[str, dict]:
    """
    Skinport /v1/items javobi - to'g'ridan-to'g'ri item dict'lari ro'yxati:
    [{"market_hash_name": "...", "min_price": 1.23, "suggested_price": 1.30,
      "quantity": 16, ...}, ...]
    (docs.skinport.com/items rasmiy misoliga asoslangan).
    """
    result: dict[str, dict] = {}
    if not isinstance(data, list):
        return result

    for item in data:
        if not isinstance(item, dict):
            continue
        name = item.get("market_hash_name")
        # min_price bo'lmasa (masalan hozir sotuvda yo'q), suggested_price
        # (tavsiya etilgan narx) ni zaxira sifatida ishlatamiz.
        price = item.get("min_price")
        if price is None:
            price = item.get("suggested_price")
        if name and price is not None:
            result[name] = {"price": price, "count": item.get("quantity")}

    return result


async def _fetch_from_skinport(item_name: str) -> tuple[float, int | None] | None:
    prices = await _load_skinport_prices()
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
            async with session.get(url, headers=_REQUEST_HEADERS) as resp:
                if resp.status != 200:
                    logger.warning(
                        "Steam priceoverview \"%s\" uchun status=%s qaytardi",
                        item_name,
                        resp.status,
                    )
                    return None
                data = await resp.json(content_type=None)
    except Exception as exc:
        logger.warning("Steam priceoverview so'rovida xatolik (%s): %r", item_name, exc)
        return None

    if not data or not data.get("success"):
        logger.info("Steam \"%s\" uchun narx topmadi (success=false yoki bo'sh javob)", item_name)
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


_RARE_PREFIXES = ("Souvenir ", "StatTrak™ ")


async def _fetch_price_for_name(item_name: str) -> tuple[float, int | None, str] | None:
    """Avval Skinport, topilmasa Steam'dan narxni oladi (bitta nom uchun)."""
    skinport_result = await _fetch_from_skinport(item_name)
    if skinport_result is not None:
        price, count = skinport_result
        return price, count, texts.CS2_MARKET_SOURCE_LISSKINS

    steam_result = await _fetch_from_steam(item_name)
    if steam_result is not None:
        price, volume = steam_result
        return price, volume, texts.CS2_MARKET_SOURCE_STEAM

    return None


async def _fetch_price_with_fallback(
    item_name: str,
) -> tuple[float, int | None, str, str] | None:
    """
    Narxni topishga harakat qiladi. Agar bu "Souvenir" yoki "StatTrak™"
    variant bo'lsa va narx topilmasa (bu variantlar kamdan-kam sotiladi,
    ko'pincha narx manbalarida umuman yo'q), oddiy (asosiy) variantni
    ham sinab ko'radi - shu bilan foydalanuvchi hech bo'lmasa taxminiy
    narxni bilib oladi, "topilmadi" deb qolmaydi.

    :return: (narx, hajm/soni, manba, haqiqatda topilgan nom) yoki None
    """
    result = await _fetch_price_for_name(item_name)
    if result is not None:
        price, count, source = result
        return price, count, source, item_name

    for prefix in _RARE_PREFIXES:
        if item_name.startswith(prefix):
            base_name = item_name[len(prefix):]
            base_result = await _fetch_price_for_name(base_name)
            if base_result is not None:
                price, count, source = base_result
                logger.info(
                    "\"%s\" uchun narx topilmadi, oddiy variant \"%s\" narxi "
                    "ko'rsatildi",
                    item_name,
                    base_name,
                )
                return price, count, source, base_name

    return None


async def _send_price_result(message: Message, item_name: str) -> None:
    result = await _fetch_price_with_fallback(item_name)
    if result is None:
        logger.warning(
            "\"%s\" uchun narx TOPILMADI - Skinport ham, Steam ham javob "
            "bermadi. Sabablarini yuqoridagi WARNING loglarida ko'ring "
            "(masalan Steam 429/403 bergan bo'lishi mumkin - bulut IP "
            "manzillari ko'pincha Steam tomonidan bloklanadi; yoki bu "
            "kamdan-kam sotiladigan buyum bo'lib, narx manbalarida "
            "umuman yo'q bo'lishi mumkin).",
            item_name,
        )
        await message.answer(texts.CS2_MARKET_NOT_FOUND)
        return

    usd_price, volume, source, resolved_name = result
    is_fallback_name = resolved_name != item_name

    uzs_price = usd_price * settings.usd_to_uzs_rate
    usd_str = f"{usd_price:.2f}"
    uzs_str = f"{uzs_price:,.0f}".replace(",", " ")

    # Agar aynan so'ralgan (masalan Souvenir) variant narxi topilmay,
    # oddiy variant narxi ko'rsatilayotgan bo'lsa, buni chiqarilgan
    # nomning o'zida ko'rsatamiz - shu bilan foydalanuvchi bu taxminiy
    # ekanini bilib oladi (aynan Souvenir/StatTrak narxi emas).
    if is_fallback_name:
        display_name = texts.CS2_MARKET_FALLBACK_NAME.format(
            requested=item_name, resolved=resolved_name
        )
    else:
        display_name = resolved_name

    if volume:
        text = texts.CS2_MARKET_RESULT_WITH_VOLUME.format(
            name=display_name, usd=usd_str, uzs=uzs_str, volume=volume, source=source
        )
    else:
        text = texts.CS2_MARKET_RESULT.format(
            name=display_name, usd=usd_str, uzs=uzs_str, source=source
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
