"""
ACHI BOT - AI-yordamchi funksiyalar uchun umumiy qatlam.

Ikki premium funksiya shu modulga tayanadi:
1. Aqlli moderatsiya (moderation.py / middlewares orqali chaqiriladi) -
   matnli xabarni "spam/haqorat/reklama" ekanligini baholaydi.
2. Aqlli hisobot xulosasi (report.py orqali chaqiriladi) - ban/mute/warn
   tarixini o'qib, qisqa inson-tilida xulosa yozadi.

MUHIM: bu sandbox/ishlab chiqish muhitida haqiqiy AI API'ga ulanish
tekshirilmagan (internet yo'q). Shu sabab ikkala funksiya ham AI_API_KEY
sozlanmagan yoki so'rov muvaffaqiyatsiz bo'lgan taqdirda ODDIY qoida-
asosli (heuristic) zaxira mantiqqa avtomatik o'tadi - bot hech qachon
AI xatosi tufayli ishlamay qolmaydi.
"""
from __future__ import annotations

import json
import logging
import re

import aiohttp

from config import settings

logger = logging.getLogger("achi_bot.ai")

# Zaxira (kalitsiz) spam/haqorat tekshiruvi uchun oddiy so'zlar ro'yxati -
# AI ishlamasa ham guruhda kamida asosiy holatlar ushlanib qolsin.
_HEURISTIC_SPAM_MARKERS = (
    "http://", "https://", "t.me/", "@", "bit.ly", "заработ", "подпи",
    "投资", "crypto airdrop", "click here", "free money",
)
_HEURISTIC_TOXIC_MARKERS = (
    "хуй", "бляд", "сука", "пидор", "ебан", "гандон",
)


async def _call_chat_completion(system_prompt: str, user_content: str) -> str | None:
    """
    OpenAI-mos Chat Completions endpointiga so'rov yuboradi. AI
    sozlanmagan (kalit yo'q) yoki so'rov muvaffaqiyatsiz bo'lsa None
    qaytaradi - chaqiruvchi kod buni zaxira mantiqqa o'tish signali
    sifatida ishlatishi kerak.
    """
    if not settings.ai_enabled:
        return None

    payload = {
        "model": settings.ai_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.3,
        "max_tokens": 400,
    }
    headers = {
        "Authorization": f"Bearer {settings.ai_api_key}",
        "Content-Type": "application/json",
    }
    try:
        timeout = aiohttp.ClientTimeout(total=settings.ai_timeout_sec)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                settings.ai_api_url, json=payload, headers=headers
            ) as resp:
                if resp.status != 200:
                    logger.warning("AI so'rovi %s status bilan qaytdi", resp.status)
                    return None
                data = await resp.json()
                return data["choices"][0]["message"]["content"].strip()
    except Exception:
        logger.exception("AI so'rovida xatolik")
        return None


def _heuristic_is_bad_message(text: str) -> tuple[bool, str] | None:
    """Kalitsiz (AI yo'q) holatda ishlaydigan oddiy qoida-asosli tekshiruv."""
    lowered = text.lower()
    for marker in _HEURISTIC_TOXIC_MARKERS:
        if marker in lowered:
            return True, "haqoratli so'z"
    link_markers = sum(1 for m in _HEURISTIC_SPAM_MARKERS if m in lowered)
    # Bir nechta reklama-belgisi + qisqa matn = ehtimol spam
    if link_markers >= 1 and len(text) < 200 and re.search(r"(https?://|t\.me/)", lowered):
        return True, "reklama/spam havolasi"
    return None


async def classify_message(text: str) -> tuple[bool, str] | None:
    """
    Xabar matnini baholaydi. Natija:
    - None -> muammo yo'q, xabar toza
    - (True, sabab) -> spam/haqorat, o'chirilishi tavsiya etiladi

    AI mavjud bo'lsa AI orqali, bo'lmasa heuristic orqali ishlaydi.
    """
    if not text or len(text.strip()) < 2:
        return None

    if settings.ai_enabled:
        system_prompt = (
            "You moderate messages in an Uzbek/Russian Telegram group chat. "
            "Classify the user message as SPAM, TOXIC, or OK. "
            "Respond with strict JSON: "
            '{"verdict": "SPAM_OR_TOXIC_OR_OK", "reason": "short reason in Uzbek"}. '
            "Be conservative - only flag clear spam/advertising or clear insults/harassment. "
            "Normal conversation, jokes, and disagreements are OK."
        )
        raw = await _call_chat_completion(system_prompt, text[:2000])
        if raw:
            try:
                # Ba'zi modellar ```json bilan o'rab yuborishi mumkin - tozalaymiz.
                cleaned = raw.strip().strip("`")
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:].strip()
                parsed = json.loads(cleaned)
                verdict = str(parsed.get("verdict", "OK")).upper()
                if verdict in ("SPAM", "TOXIC"):
                    reason = str(parsed.get("reason") or "AI aniqladi").strip()
                    return True, reason
                return None
            except Exception:
                logger.warning("AI javobini JSON qilib o'qib bo'lmadi: %r", raw)
                # AI javob berdi, lekin formatga tushmadi - heuristic'ga tushamiz.

    return _heuristic_is_bad_message(text)


async def summarize_report(period_label: str, chat_title: str, action_lines: list[str]) -> str | None:
    """
    Ban/mute/warn tarixi asosida qisqa, inson-tilida xulosa yozadi
    (masalan: "Bu davrda asosan spam uchun ban berilgan, X admin eng
    faol bo'lgan"). AI yo'q bo'lsa None qaytaradi (chaqiruvchi kod
    xulosa bo'limini shunchaki o'tkazib yuboradi).
    """
    if not settings.ai_enabled or not action_lines:
        return None

    system_prompt = (
        "You are an assistant summarizing Telegram group moderation logs for "
        "a group admin. Write a SHORT (2-4 sentences) summary in Tashkent-dialect "
        "Uzbek, casual and friendly tone. Mention notable patterns (e.g. most "
        "common reason, most active admin, any spike). Do not use markdown, "
        "do not repeat every line - just the key insight."
    )
    joined = "\n".join(action_lines[:200])
    user_content = f"Guruh: {chat_title}\nDavr: {period_label}\n\nAmallar:\n{joined}"
    return await _call_chat_completion(system_prompt, user_content)
