"""
ACHI BOT - hisobot buyruqlari: /r (matnli tezkor hisobot) va /report
(chiroyli PDF hisobot, profil rasmlari bilan). Har soatlik avtomatik PDF
uchun `run_hourly_reports` funksiyasi main.py'dan APScheduler orqali
chaqiriladi.
"""
from __future__ import annotations

import csv
import io
import os
import time
import uuid
from datetime import datetime

from aiogram import Bot, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import BufferedInputFile, FSInputFile, Message

import texts
from config import settings
from database import db
from handlers.premium import is_premium_or_free
from pdf_report import build_pdf, build_report_rows, summarize
from utils import is_chat_admin, mention_html, user_display_name

router = Router(name="report")

_ACTION_ICON = {
    "ban": "🚫",
    "tban": "🚫",
    "unban": "✅",
    "mute": "🔇",
    "tmute": "🔇",
    "unmute": "🔊",
    "kick": "👋",
    "warn": "⚠️",
    "unwarn": "↩️",
    "promote": "⭐",
    "demote": "🔻",
}

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
        start_of_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
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


async def _send_text_report(message: Message, actions, period_label: str) -> None:
    if not actions:
        await message.reply(texts.REPORT_EMPTY_PERIOD)
        return

    lines = [texts.R_TEXT_HEADER.format(period=period_label, chat_title=message.chat.title or "")]
    for i, a in enumerate(actions, start=1):
        icon = _ACTION_ICON.get(a["action"], "•")
        title = _ACTION_TITLE.get(a["action"], a["action"])
        target = a["target_username"] and f"@{a['target_username']}" or a["target_name"] or str(a["target_id"])
        date = datetime.fromtimestamp(a["created_at"]).strftime("%d.%m.%Y %H:%M")
        line = texts.R_TEXT_ITEM.format(
            num=i,
            icon=icon,
            action=title,
            target=target,
            reason=a["reason"] or "ko'rsatilmagan",
            admin=a["admin_name"] or "-",
            date=date,
        )
        lines.append(line)

        # Telegram xabar uzunligi cheklangan (4096), shu uchun bo'lib yuboramiz
        if sum(len(l) for l in lines) > 3500:
            await message.answer("\n".join(lines))
            lines = []

    if lines:
        await message.answer("\n".join(lines))


@router.message(Command("report"))
async def cmd_report(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return

    arg = (command.args or "soat").strip().lower()
    bounds = _period_bounds(arg) or (time.time() - 3600, "so'nggi 1 soat")
    since_ts, period_label = bounds

    await message.reply(texts.REPORT_GENERATING)
    await _generate_and_send_pdf(bot, message.chat.id, message.chat.title or "Guruh", since_ts, period_label, message)


async def _generate_and_send_pdf(
    bot: Bot,
    chat_id: int,
    chat_title: str,
    since_ts: float,
    period_label: str,
    reply_target: Message | None = None,
) -> None:
    actions = await db.get_actions_since(chat_id, since_ts)
    if not actions:
        if reply_target:
            await reply_target.answer(texts.REPORT_EMPTY_PERIOD)
        return

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
    await bot.send_document(chat_id, FSInputFile(pdf_path), caption=caption)


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

    actions = await db.get_actions_since(message.chat.id, since_ts)
    if not actions:
        await message.reply(texts.REPORT_EMPTY_PERIOD)
        return

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
        date_str = datetime.fromtimestamp(a["created_at"]).strftime("%d.%m.%Y %H:%M:%S")
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
        message.chat.id,
        BufferedInputFile(csv_bytes, filename=filename),
        caption=texts.EXPORT_CAPTION.format(
            period=period_label, chat_title=message.chat.title or ""
        ),
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
