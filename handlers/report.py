"""
ACHI BOT - hisobot buyruqlari: /r (matnli tezkor hisobot) va /report
(chiroyli PDF hisobot, profil rasmlari bilan). Har soatlik avtomatik PDF
uchun `run_hourly_reports` funksiyasi main.py'dan APScheduler orqali
chaqiriladi.
"""
from __future__ import annotations

import csv
import io
import logging
import os
import time
import uuid

from aiogram import Bot, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import BufferedInputFile, FSInputFile, Message

import texts
from config import settings
from database import db
from handlers.premium import is_premium_or_free
from pdf_report import build_pdf, build_report_rows, summarize
from utils import format_timestamp, is_chat_admin, mention_html, now_tashkent, user_display_name

router = Router(name="report")
logger = logging.getLogger("achi_bot.report")

_ACTION_TITLE = {
    "ban": "Ban",
    "tban": "Vaqtincha ban",
    "unban": "Unban",
    "mute": "Mute",
    "tmute": "Vaqtincha mute",
    "unmute": "Unmute",
    "kick": "Kick",
    "warn": "Ogohlantirish",
    "unwarn": "Ogohlantirish olindi",
    "promote": "Admin qilindi",
    "demote": "Adminlikdan olindi",
}


async def _guard_admin(message: Message, bot: Bot) -> bool:
    if message.chat.type not in ("group", "supergroup"):
        await message.reply(texts.ONLY_IN_GROUP)
        return False
    if not message.from_user or not await is_chat_admin(
        bot, message.chat.id, message.from_user.id
    ):
        await message.reply(texts.NOT_ADMIN)
        return False
    return True


def _period_bounds(arg: str) -> tuple[float, str] | None:
    now = time.time()
    if arg in ("soat", "hour", "1h"):
        return now - 3600, "so'nggi 1 soat"
    if arg in ("kun", "day", "bugun"):
        # Toshkent vaqti bo'yicha "bugun soat 00:00" - server UTC vaqtida
        # ishlagani uchun datetime.now() ishlatilsa, "bugun" tushunchasi
        # noto'g'ri (masalan UTC kechqurun bo'lganda Toshkentda ertasi
        # kun bo'lib qolardi).
        start_of_day = now_tashkent().replace(hour=0, minute=0, second=0, microsecond=0)
        return start_of_day.timestamp(), "bugungi kun"
    if arg in ("hafta", "week"):
        return now - 7 * 86400, "so'nggi 7 kun"
    return None


@router.message(Command("r"))
async def cmd_r(message: Message, command: CommandObject, bot: Bot) -> None:
    """
    /r soat - so'nggi 1 soatlik amallar
    /r kun - bugungi amallar
    /r @username yoki reply - shu odamning tarixi (butun vaqt bo'yicha)
    """
    if not await _guard_admin(message, bot):
        return

    arg = (command.args or "").strip()

    # Reply orqali muayyan odamning tarixini so'rash
    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user
        actions = await db.get_actions_since(message.chat.id, 0, target_id=target.id)
        period_label = f"{user_display_name(target)}ning butun tarixi"
        await _send_text_report(message, actions, period_label)
        return

    if not arg:
        await message.reply(texts.R_COMMAND_USAGE)
        return

    if arg.startswith("@"):
        # Username orqali qidirish - actions jadvalida saqlangan username bo'yicha
        username = arg.lstrip("@").lower()
        cursor = await db.conn.execute(
            "SELECT * FROM actions WHERE chat_id = ? AND LOWER(target_username) = ? ORDER BY created_at ASC",
            (message.chat.id, username),
        )
        actions = await cursor.fetchall()
        await _send_text_report(message, actions, f"@{username} tarixi")
        return

    bounds = _period_bounds(arg.lower())
    if not bounds:
        await message.reply(texts.R_COMMAND_USAGE)
        return
    since_ts, period_label = bounds
    actions = await db.get_actions_since(message.chat.id, since_ts)
    await _send_text_report(message, actions, period_label)


def _format_action_line(i: int, a) -> str:
    title = _ACTION_TITLE.get(a["action"], a["action"])
    target = a["target_username"] and f"@{a['target_username']}" or a["target_name"] or str(a["target_id"])
    date = format_timestamp(a["created_at"])
    return texts.R_TEXT_ITEM.format(
        num=i,
        action=title,
        target=target,
        reason=a["reason"] or "ko'rsatilmagan",
        admin=a["admin_name"] or "-",
        date=date,
    )


async def build_text_report_chunks(
    chat_title: str, actions, period_label: str, *, with_ai_summary: bool = False
) -> list[str]:
    """
    `/r` matnli hisobotini tayyorlaydi va Telegram xabar uzunligi
    chegarasiga (4096) mos qilib bo'laklarga (chunk) bo'ladi.

    MUHIM: bu funksiya `Message`ga bog'liq EMAS - faqat oddiy ma'lumot
    qabul qilib, matn qaytaradi. Shu sabab uni ham guruh ichidagi /r
    buyrug'idan, ham DM boshqarish panelidan (handlers/panel.py) bab-
    baravar chaqirish mumkin - avvalgi versiyada bu funksiya to'g'ridan-
    to'g'ri `message.answer()` chaqirardi, shu sabab faqat guruh ichida
    ishlay olardi.
    """
    if not actions:
        return [texts.REPORT_EMPTY_PERIOD]

    chunks: list[str] = []
    lines = [texts.R_TEXT_HEADER.format(period=period_label, chat_title=chat_title or "")]
    for i, a in enumerate(actions, start=1):
        lines.append(_format_action_line(i, a))
        if sum(len(l) for l in lines) > 3500:
            chunks.append("\n".join(lines))
            lines = []
    if lines:
        chunks.append("\n".join(lines))

    # AI-yordamchi xulosa (premium funksiya) - agar AI sozlangan bo'lsa,
    # hisobot oxiriga qisqa inson-tilidagi xulosa qo'shiladi. AI
    # sozlanmagan/ishlamagan bo'lsa `summarize_report` None qaytaradi va
    # hisobot odatdagidek (xulosasiz) ko'rsatiladi - hech qanday xato
    # bermaydi.
    if with_ai_summary:
        try:
            from handlers.ai import summarize_report

            action_lines = [_format_action_line(i, a) for i, a in enumerate(actions, start=1)]
            summary_text = await summarize_report(period_label, chat_title, action_lines)
            if summary_text:
                chunks.append(texts.R_AI_SUMMARY.format(summary=summary_text))
        except Exception:
            logger.exception("AI xulosasini tayyorlashda xatolik")

    return chunks


async def _send_text_report(message: Message, actions, period_label: str) -> None:
    # AI xulosa - PREMIUM funksiya (bepul guruhlarda oddiy ro'yxat
    # ko'rsatiladi, xulosasiz).
    with_ai = await is_premium_or_free(message.chat.id, message.from_user.id if message.from_user else None)
    chunks = await build_text_report_chunks(
        message.chat.title or "", actions, period_label, with_ai_summary=with_ai
    )
    for chunk in chunks:
        await message.answer(chunk)


@router.message(Command("report"))
async def cmd_report(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return

    arg = (command.args or "soat").strip().lower()
    bounds = _period_bounds(arg) or (time.time() - 3600, "so'nggi 1 soat")
    since_ts, period_label = bounds

    await message.reply(texts.REPORT_GENERATING)
    await generate_and_send_pdf(
        bot, message.chat.id, message.chat.title or "Guruh", since_ts, period_label,
        reply_target=message,
    )


async def generate_and_send_pdf(
    bot: Bot,
    source_chat_id: int,
    chat_title: str,
    since_ts: float,
    period_label: str,
    *,
    send_to_chat_id: int | None = None,
    reply_target: Message | None = None,
) -> bool:
    """
    Berilgan guruh (`source_chat_id`) uchun PDF hisobot tayyorlab,
    `send_to_chat_id`ga (agar berilmasa, `source_chat_id`ning o'ziga)
    yuboradi.

    MUHIM: `send_to_chat_id` ajratilgani DM boshqarish panelidan
    chaqirish uchun kerak - masalan admin DM'dan "Hisobot" tugmasini
    bossa, hisobot GURUH tarixidan (`source_chat_id`) olinadi, lekin
    fayl ADMINning shaxsiy chatiga (`send_to_chat_id` = admin DM'i)
    yuboriladi. Guruh ichidagi /report esa ikkisini bir xil qilib
    chaqiradi (o'z-o'ziga yuboradi).

    :return: True agar hisobot (hech bo'lmasa bo'sh-emas holatda)
        muvaffaqiyatli yuborilgan bo'lsa, aks holda False.
    """
    target_chat_id = send_to_chat_id if send_to_chat_id is not None else source_chat_id

    actions = await db.get_actions_since(source_chat_id, since_ts)
    if not actions:
        if reply_target:
            await reply_target.answer(texts.REPORT_EMPTY_PERIOD)
        return False

    rows = await build_report_rows(bot, actions, avatar_cache_dir=f"{settings.reports_dir}/avatars")
    summary = summarize(actions)
    pdf_path = build_pdf(
        chat_title=chat_title, period_label=period_label, rows=rows, summary=summary
    )

    caption = texts.REPORT_CAPTION.format(
        period=period_label,
        chat_title=chat_title,
        total=summary.get("total", 0),
        ban_count=summary.get("ban", 0) + summary.get("tban", 0),
        mute_count=summary.get("mute", 0) + summary.get("tmute", 0),
        warn_count=summary.get("warn", 0),
        kick_count=summary.get("kick", 0),
    )
    await bot.send_document(target_chat_id, FSInputFile(pdf_path), caption=caption)
    return True


async def generate_and_send_csv(
    bot: Bot,
    source_chat_id: int,
    chat_title: str,
    since_ts: float,
    period_label: str,
    *,
    send_to_chat_id: int | None = None,
    reply_target: Message | None = None,
) -> bool:
    """CSV eksport mantiqi - guruh ichidagi /exportcsv va DM panelidan
    ikkisi ham shu funksiyani chaqiradi (qarang: generate_and_send_pdf
    yuqorida, xuddi shu naqsh bilan)."""
    target_chat_id = send_to_chat_id if send_to_chat_id is not None else source_chat_id

    actions = await db.get_actions_since(source_chat_id, since_ts)
    if not actions:
        if reply_target:
            await reply_target.answer(texts.REPORT_EMPTY_PERIOD)
        return False

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "Sana",
            "Amal",
            "Nishon ismi",
            "Nishon username",
            "Nishon ID",
            "Sabab",
            "Muddat",
            "Admin",
            "Admin ID",
        ]
    )
    for a in actions:
        date_str = format_timestamp(a["created_at"], "%d.%m.%Y %H:%M:%S")
        writer.writerow(
            [
                date_str,
                _ACTION_TITLE.get(a["action"], a["action"]),
                a["target_name"] or "",
                a["target_username"] or "",
                a["target_id"],
                a["reason"] or "",
                a["duration"] or "",
                a["admin_name"] or "",
                a["admin_id"],
            ]
        )

    # Excel'da o'zbek/kirill harflari to'g'ri ochilishi uchun UTF-8 BOM
    # bilan kodlaymiz (BOM bo'lmasa Excel ba'zan lotin-1 deb noto'g'ri o'qiydi).
    csv_bytes = ("\ufeff" + buffer.getvalue()).encode("utf-8")
    filename = f"achi_export_{uuid.uuid4().hex[:8]}.csv"

    await bot.send_document(
        target_chat_id,
        BufferedInputFile(csv_bytes, filename=filename),
        caption=texts.EXPORT_CAPTION.format(period=period_label, chat_title=chat_title or ""),
    )
    return True


@router.message(Command("exportcsv"))
async def cmd_exportcsv(message: Message, command: CommandObject, bot: Bot) -> None:
    """
    /exportcsv [soat|kun|hafta] - premium funksiya. Hisobotni Excel'da
    ochish uchun CSV faylga aylantirib beradi.
    """
    if not await _guard_admin(message, bot):
        return

    if not await is_premium_or_free(message.chat.id, message.from_user.id):
        await message.reply(texts.PREMIUM_REQUIRED_EXPORT)
        return

    arg = (command.args or "hafta").strip().lower()
    bounds = _period_bounds(arg) or (time.time() - 7 * 86400, "so'nggi 7 kun")
    since_ts, period_label = bounds

    await message.reply(texts.EXPORT_GENERATING)
    await generate_and_send_csv(
        bot, message.chat.id, message.chat.title or "", since_ts, period_label,
        reply_target=message,
    )


async def run_hourly_reports(bot: Bot) -> None:
    """
    APScheduler tomonidan har soatda chaqiriladi. `report_enabled` yoqilgan
    barcha guruhlarga (agar shu soat davomida amal bo'lgan bo'lsa) PDF
    hisobot yuboradi.
    """
    chats = await db.get_all_active_report_chats()
    since_ts = time.time() - settings.hourly_report_interval_hours * 3600
    for chat in chats:
        actions = await db.get_actions_since(chat["chat_id"], since_ts)
        if not actions:
            continue
        rows = await build_report_rows(
            bot, actions, avatar_cache_dir=f"{settings.reports_dir}/avatars"
        )
        summary = summarize(actions)
        pdf_path = build_pdf(
            chat_title=chat["chat_title"] or "Guruh",
            period_label="so'nggi 1 soat",
            rows=rows,
            summary=summary,
        )
        caption = texts.REPORT_CAPTION.format(
            period="so'nggi 1 soat",
            chat_title=chat["chat_title"] or "Guruh",
            total=summary.get("total", 0),
            ban_count=summary.get("ban", 0) + summary.get("tban", 0),
            mute_count=summary.get("mute", 0) + summary.get("tmute", 0),
            warn_count=summary.get("warn", 0),
            kick_count=summary.get("kick", 0),
        )
        try:
            await bot.send_document(chat["chat_id"], FSInputFile(pdf_path), caption=caption)
        except Exception:
            pass
        # Alohida report_chat_id sozlangan bo'lsa, u yerga ham yuboramiz
        if settings.report_chat_id:
            try:
                await bot.send_document(
                    settings.report_chat_id, FSInputFile(pdf_path), caption=caption
                )
            except Exception:
                pass
