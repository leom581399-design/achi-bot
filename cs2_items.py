"""
ACHI BOT - CS2 buyum nomlari bazasi va "aqlli" (fuzzy) qidiruv.

Foydalanuvchi ".skin ak47" kabi qisqa/to'liqsiz nom yozganda ham, bot
Steam Market'dagi TO'LIQ va TO'G'RI nomni (market_hash_name) topib
bera olishi uchun, loyihaga CS2'ning barcha buyumlari ro'yxati
`data_cs2_items.json.gz` fayli sifatida qo'shilgan (ByMykel/CSGO-API
ochiq loyihasidan olingan, MIT litsenziya, ~20 ming nom, siqilgan holda
~85KB).

Qidiruv strategiyasi (tezlik uchun ketma-ket, birinchi mos kelgani
qaytariladi):
1. To'liq mos kelish (katta-kichik harfsiz)
2. Normallashtirilgan matn ichida qidiruv (bo'sh joy/belgilar olib
   tashlangan holda)
3. "Compact" qidiruv (bo'sh joysiz, "ak47redline" kabi)
4. difflib orqali yaqin mos kelishlarni topish (agar yuqoridagilar
   natija bermasa)
"""
from __future__ import annotations

import difflib
import gzip
import json
import os
import re
from functools import lru_cache

_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_cs2_items.json.gz")
_META_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_cs2_meta.json.gz")

_STRIP_RE = re.compile(r"[^a-z0-9]+")
_SPECIAL_CHARS_RE = re.compile(r"[★™]")
_WEAR_SUFFIX_RE = re.compile(
    r"\s*\((Factory New|Minimal Wear|Field-Tested|Well-Worn|Battle-Scarred)\)\s*$"
)
_VARIANT_PREFIX_RE = re.compile(r"^(★ )?(StatTrak™ |Souvenir )")


def _normalize(text: str) -> str:
    text = text.lower()
    text = _SPECIAL_CHARS_RE.sub("", text)
    text = _STRIP_RE.sub(" ", text)
    return text.strip()


def _compact(text: str) -> str:
    return _normalize(text).replace(" ", "")


@lru_cache(maxsize=1)
def _load_index() -> tuple[list[str], dict[str, str], dict[str, str]]:
    """
    Bazani bir marta yuklab, xotirada saqlaydi (lru_cache orqali - jarayon
    davomida faqat bitta marta o'qiladi).

    :return: (original nomlar ro'yxati, normalized->original lug'at,
              compact->original lug'at)
    """
    if not os.path.exists(_DATA_PATH):
        return [], {}, {}

    with gzip.open(_DATA_PATH, "rt", encoding="utf-8") as f:
        names: list[str] = json.load(f)

    norm_map: dict[str, str] = {}
    compact_map: dict[str, str] = {}
    for name in names:
        norm_map[_normalize(name)] = name
        compact_map[_compact(name)] = name

    return names, norm_map, compact_map


def _rarity_rank(name: str) -> int:
    """
    "Souvenir" va "StatTrak" variantlari odatdagi (oddiy) skinlarga
    solishtirganda ancha kamroq sotiladi va ko'pincha narx manbalarida
    (Skinport/Steam) ma'lumot topilmaydi. Foydalanuvchi ".skin ak47
    redline" kabi oddiy so'rov yozganda, aynan shu kamdan-kam
    variantlarni birinchi o'ringa chiqarib, chalkashtirib qo'ymaslik
    uchun - oddiy variantlarga eng kichik (ustunlik yuqori) reyting
    beriladi.
    """
    lowered = name.lower()
    if "souvenir" in lowered:
        return 2
    if "stattrak" in lowered or "stat trak" in lowered:
        return 1
    return 0


def search(query: str, limit: int = 5) -> list[str]:
    """
    Berilgan so'rov bo'yicha eng mos keladigan buyum nomlarini (Steam
    market_hash_name shaklida) qaytaradi. Natija bo'lmasa bo'sh ro'yxat.

    Natijalar avval "oddiy" (Souvenir/StatTrak bo'lmagan) variantlar,
    keyin StatTrak, keyin Souvenir tartibida saralanadi - chunki
    foydalanuvchi odatda oddiy variantni so'raydi, va kamdan-kam
    variantlarda narx topilmaslik ehtimoli yuqori.
    """
    names, norm_map, compact_map = _load_index()
    if not names:
        return []

    nq = _normalize(query)
    cq = _compact(query)
    if not nq:
        return []

    # 1) To'liq mos kelish
    if nq in norm_map:
        return [norm_map[nq]]

    # 2) Normallashtirilgan matn ichida qidiruv (masalan "ak47 redline")
    substr_matches = [norm_map[k] for k in norm_map if nq in k]
    if substr_matches:
        return _rank_and_dedupe(substr_matches)[:limit]

    # 3) Compact qidiruv (masalan "ak47redline" - bo'sh joysiz)
    compact_matches = [compact_map[k] for k in compact_map if cq in k]
    if compact_matches:
        return _rank_and_dedupe(compact_matches)[:limit]

    # 4) Yaqin mos kelishlarni difflib bilan qidirish (xato yozilgan
    # so'zlar uchun, masalan "redlien" -> "redline")
    close = difflib.get_close_matches(nq, list(norm_map.keys()), n=limit, cutoff=0.5)
    return _rank_and_dedupe([norm_map[c] for c in close])[:limit]


def _rank_and_dedupe(items: list[str]) -> list[str]:
    deduped = _dedupe(items)
    deduped.sort(key=_rarity_rank)
    return deduped


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def is_available() -> bool:
    """Ma'lumotlar bazasi fayli mavjud va yuklanganligini tekshiradi."""
    names, _, _ = _load_index()
    return bool(names)


# ------------------------------------------------------------------
# Buyum metadatasi (rasm, qaysi keys/to'plamdan tushishi) -
# ByMykel/CSGO-API ochiq loyihasidan olingan, base (Wear/StatTrak/
# Souvenir'siz) nom bo'yicha kalitlangan (data_cs2_meta.json.gz).
# ------------------------------------------------------------------


@lru_cache(maxsize=1)
def _load_meta() -> dict[str, dict]:
    if not os.path.exists(_META_PATH):
        return {}
    with gzip.open(_META_PATH, "rt", encoding="utf-8") as f:
        return json.load(f)


def base_name(name: str) -> str:
    """
    To'liq nomdan (masalan "StatTrak™ AK-47 | Redline (Field-Tested)")
    metadata bazasida kalit sifatida ishlatiladigan asosiy nomni
    ("AK-47 | Redline") ajratib oladi - ya'ni Wear qavsini va
    StatTrak/Souvenir prefiksini olib tashlaydi (★ prefiksi qoldiriladi,
    chunki pichoq/qo'lqop nomlari metadata bazasida ham ★ bilan
    saqlangan).
    """
    stripped = _WEAR_SUFFIX_RE.sub("", name)
    stripped = _VARIANT_PREFIX_RE.sub(r"\1", stripped)
    return stripped.strip()


def get_meta(name: str) -> dict | None:
    """
    Berilgan (to'liq yoki asosiy) buyum nomi uchun metadata qaytaradi:
    {"image": <url yoki None>, "source": <keys/to'plam nomi yoki None>,
    "rarity": <nodirlik nomi yoki None>}. Topilmasa None.
    """
    meta = _load_meta()
    if not meta:
        return None
    return meta.get(base_name(name)) or meta.get(name)
