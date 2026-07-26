"""
ACHI BOT - qo'shimcha PREMIUM funksiyalar.

Bu modulda 17 ta PREMIUM (guruh /premium sotib olgandan keyin ochiladigan)
funksiya joylashgan:

1. /setwarnaction - warn limitiga yetganda ban o'rniga mute qilish
2. /nightmode - tungi rejim (belgilangan soatlarda avtomatik yopilish)
3. /floodlimit - moslashtiriladigan flood chegarasi
4. /warnexpiry - ogohlantirishlar muddati
5. /textcaptcha - matn-savol captcha (oddiy tugma o'rniga)
6. /autodelete - filtr/eslatma javoblarini avtomatik o'chirish
7. /silentmode - admin buyruqlarining o'zini ham o'chirish
8. /autopin - xush kelibsiz xabarini avtomatik pin qilish
9. /antiraid - qisqa vaqtda ko'p qo'shilish (reyd) himoyasi
10. /vip, /unvip, /viplist - VIP a'zolar (cheklovlardan ozod)
11. /addmod, /removemod, /modlist - kichik-adminlar (moderator)
12. /schedule, /schedulelist, /unschedule - rejalashtirilgan kunlik xabarlar
13. /allowlink, /unallowlink, /allowlinks - havola oq ro'yxati
14. /dailyreport - har kunlik avtomatik hisobot (admin DM'iga)
15. /backup - guruh sozlamalarining JSON zaxira nusxasi

Har bir funksiya boshida `_require_premium()` orqali premium tekshiradi -
bu MUHIM, chunki avvalgi bug xuddi shu tekshiruv yo'qligidan kelib
chiqqan edi (DM panelda filtr/eslatma qo'shishda unutilgan edi).
"""
from __future__ import annotations

import json
import time

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.types import BufferedInputFile, Message
from aiogram.filters import Command, CommandObject

import texts
from database import db
from handlers.premium import is_premium_or_free
from utils import is_chat_admin, mention_html, resolve_target, user_display_name

router = Router(name="premium_extras")


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


async def _require_premium(message: Message, denial_text: str) -> bool:
    ok = await is_premium_or_free(message.chat.id, message.from_user.id)
    if not ok:
        await message.reply(denial_text)
        return False
    return True


# ------------------------------------------------------------------
# 1. /setwarnaction
# ------------------------------------------------------------------


@router.message(Command("setwarnaction"))
async def cmd_setwarnaction(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return
    if not await _require_premium(message, texts.WARNACTION_REQUIRES_PREMIUM):
        return
    arg = (command.args or "").strip().lower()
    if arg not in ("ban", "mute"):
        await message.reply(texts.WARNACTION_USAGE)
        return
    await db.ensure_chat(message.chat.id, message.chat.title)
    await db.update_chat_setting(message.chat.id, warn_action=arg)
    await message.reply(texts.WARNACTION_SET.format(action=arg))


# ------------------------------------------------------------------
# 2. /nightmode
# ------------------------------------------------------------------


@router.message(Command("nightmode"))
async def cmd_nightmode(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return
    if not await _require_premium(message, texts.NIGHTMODE_REQUIRES_PREMIUM):
        return
    arg = (command.args or "").strip().lower()
    if arg == "off":
        await db.ensure_chat(message.chat.id, message.chat.title)
        await db.update_chat_setting(message.chat.id, night_mode_enabled=0)
        await message.reply(texts.NIGHTMODE_OFF)
        return
    if "-" not in arg:
        await message.reply(texts.NIGHTMODE_USAGE)
        return
    start_s, end_s = arg.split("-", maxsplit=1)
    if not start_s.isdigit() or not end_s.isdigit():
        await message.reply(texts.NIGHTMODE_USAGE)
        return
    start_h, end_h = int(start_s), int(end_s)
    if not (0 <= start_h <= 23 and 0 <= end_h <= 23):
        await message.reply(texts.NIGHTMODE_USAGE)
        return
    await db.ensure_chat(message.chat.id, message.chat.title)
    await db.update_chat_setting(
        message.chat.id, night_mode_enabled=1, night_start_hour=start_h, night_end_hour=end_h
    )
    await message.reply(texts.NIGHTMODE_ON.format(start=start_h, end=end_h))


def is_night_mode_active(row, now_hour: int) -> bool:
    """Tungi rejim faol vaqtni tekshiradi - kecha yarmidan o'tuvchi
    oraliqlarni ham to'g'ri hisoblaydi (masalan 23-7)."""
    if not row or not row["night_mode_enabled"]:
        return False
    start_h, end_h = row["night_start_hour"], row["night_end_hour"]
    if start_h == end_h:
        return False
    if start_h < end_h:
        return start_h <= now_hour < end_h
    return now_hour >= start_h or now_hour < end_h


# ------------------------------------------------------------------
# 3. /floodlimit
# ------------------------------------------------------------------


@router.message(Command("floodlimit"))
async def cmd_floodlimit(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return
    if not await _require_premium(message, texts.FLOODLIMIT_REQUIRES_PREMIUM):
        return
    arg = (command.args or "").strip().lower()
    if arg == "off":
        await db.ensure_chat(message.chat.id, message.chat.title)
        await db.update_chat_setting(
            message.chat.id, flood_limit_override=None, flood_window_override=None
        )
        await message.reply(texts.FLOODLIMIT_OFF)
        return
    parts = arg.split()
    if len(parts) != 2 or not all(p.isdigit() for p in parts):
        await message.reply(texts.FLOODLIMIT_USAGE)
        return
    limit, window = int(parts[0]), int(parts[1])
    await db.ensure_chat(message.chat.id, message.chat.title)
    await db.update_chat_setting(
        message.chat.id, flood_limit_override=limit, flood_window_override=window
    )
    await message.reply(texts.FLOODLIMIT_SET.format(limit=limit, window=window))


# ------------------------------------------------------------------
# 4. /warnexpiry
# ------------------------------------------------------------------


@router.message(Command("warnexpiry"))
async def cmd_warnexpiry(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return
    if not await _require_premium(message, texts.WARNEXPIRY_REQUIRES_PREMIUM):
        return
    arg = (command.args or "").strip().lower()
    if arg == "off":
        await db.ensure_chat(message.chat.id, message.chat.title)
        await db.update_chat_setting(message.chat.id, warn_expiry_days=0)
        await message.reply(texts.WARNEXPIRY_OFF)
        return
    if not arg.isdigit() or int(arg) <= 0:
        await message.reply(texts.WARNEXPIRY_USAGE)
        return
    days = int(arg)
    await db.ensure_chat(message.chat.id, message.chat.title)
    await db.update_chat_setting(message.chat.id, warn_expiry_days=days)
    await message.reply(texts.WARNEXPIRY_SET.format(days=days))


# ------------------------------------------------------------------
# 5. /textcaptcha
# ------------------------------------------------------------------


@router.message(Command("textcaptcha"))
async def cmd_textcaptcha(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return
    if not await _require_premium(message, texts.TEXTCAPTCHA_REQUIRES_PREMIUM):
        return
    raw = (command.args or "").strip()
    if raw.lower() == "off":
        await db.ensure_chat(message.chat.id, message.chat.title)
        await db.update_chat_setting(
            message.chat.id, text_captcha_question=None, text_captcha_answer=None
        )
        await message.reply(texts.TEXTCAPTCHA_OFF)
        return
    if "|" not in raw:
        await message.reply(texts.TEXTCAPTCHA_USAGE)
        return
    question, answer = raw.split("|", maxsplit=1)
    question, answer = question.strip(), answer.strip()
    if not question or not answer:
        await message.reply(texts.TEXTCAPTCHA_USAGE)
        return
    await db.ensure_chat(message.chat.id, message.chat.title)
    await db.update_chat_setting(
        message.chat.id, text_captcha_question=question, text_captcha_answer=answer
    )
    await message.reply(texts.TEXTCAPTCHA_SET)


# ------------------------------------------------------------------
# 6. /autodelete
# ------------------------------------------------------------------


@router.message(Command("autodelete"))
async def cmd_autodelete(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return
    if not await _require_premium(message, texts.AUTODELETE_REQUIRES_PREMIUM):
        return
    arg = (command.args or "").strip().lower()
    if arg == "off":
        await db.ensure_chat(message.chat.id, message.chat.title)
        await db.update_chat_setting(message.chat.id, autodelete_seconds=0)
        await message.reply(texts.AUTODELETE_OFF)
        return
    if not arg.isdigit() or int(arg) <= 0:
        await message.reply(texts.AUTODELETE_USAGE)
        return
    seconds = int(arg)
    await db.ensure_chat(message.chat.id, message.chat.title)
    await db.update_chat_setting(message.chat.id, autodelete_seconds=seconds)
    await message.reply(texts.AUTODELETE_SET.format(seconds=seconds))


# ------------------------------------------------------------------
# 7. /silentmode
# ------------------------------------------------------------------


@router.message(Command("silentmode"))
async def cmd_silentmode(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return
    if not await _require_premium(message, texts.SILENTMODE_REQUIRES_PREMIUM):
        return
    arg = (command.args or "").strip().lower()
    if arg not in ("on", "off"):
        await message.reply(texts.AUTOAPPROVE_USAGE)
        return
    await db.ensure_chat(message.chat.id, message.chat.title)
    await db.update_chat_setting(message.chat.id, silent_admin_actions=1 if arg == "on" else 0)
    await message.reply(texts.SILENTMODE_ON if arg == "on" else texts.SILENTMODE_OFF)


# ------------------------------------------------------------------
# 8. /autopin
# ------------------------------------------------------------------


@router.message(Command("autopin"))
async def cmd_autopin(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return
    if not await _require_premium(message, texts.AUTOPIN_REQUIRES_PREMIUM):
        return
    arg = (command.args or "").strip().lower()
    if arg not in ("on", "off"):
        await message.reply(texts.AUTOAPPROVE_USAGE)
        return
    await db.ensure_chat(message.chat.id, message.chat.title)
    await db.update_chat_setting(message.chat.id, auto_pin_welcome=1 if arg == "on" else 0)
    await message.reply(texts.AUTOPIN_ON if arg == "on" else texts.AUTOPIN_OFF)


# ------------------------------------------------------------------
# 9. /antiraid
# ------------------------------------------------------------------


@router.message(Command("antiraid"))
async def cmd_antiraid(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return
    if not await _require_premium(message, texts.ANTIRAID_REQUIRES_PREMIUM):
        return
    arg = (command.args or "").strip().lower()
    if arg == "off":
        await db.ensure_chat(message.chat.id, message.chat.title)
        await db.update_chat_setting(message.chat.id, anti_raid_enabled=0)
        await message.reply(texts.ANTIRAID_OFF)
        return
    parts = arg.split()
    if len(parts) != 2 or not all(p.isdigit() for p in parts):
        await message.reply(texts.ANTIRAID_USAGE)
        return
    threshold, window = int(parts[0]), int(parts[1])
    await db.ensure_chat(message.chat.id, message.chat.title)
    await db.update_chat_setting(
        message.chat.id, anti_raid_enabled=1, anti_raid_threshold=threshold, anti_raid_window_sec=window
    )
    await message.reply(texts.ANTIRAID_ON.format(threshold=threshold, window=window))


_join_timestamps: dict[int, list[float]] = {}


async def check_anti_raid(chat_id: int, bot: Bot) -> bool:
    """
    Yangi a'zo qo'shilganda (handlers/greetings.py'dan chaqiriladi)
    chaqiriladi. Agar chegaradan tez ko'p odam qo'shilsa, guruhni
    avtomatik "hammasi taqiqlangan" holatga o'tkazadi va True qaytaradi
    (chaqiruvchi kod shunga qarab ogohlantirish yuborishi mumkin).
    """
    row = await db.get_chat_settings(chat_id)
    if not row or not row["anti_raid_enabled"]:
        return False

    now = time.time()
    window = row["anti_raid_window_sec"]
    threshold = row["anti_raid_threshold"]
    timestamps = _join_timestamps.setdefault(chat_id, [])
    timestamps.append(now)
    _join_timestamps[chat_id] = [t for t in timestamps if now - t <= window]

    if len(_join_timestamps[chat_id]) >= threshold:
        await db.set_lock(chat_id, "all")
        _join_timestamps[chat_id] = []
        try:
            await bot.send_message(chat_id, texts.ANTIRAID_TRIGGERED)
        except TelegramAPIError:
            pass
        return True
    return False


# ------------------------------------------------------------------
# 10. VIP
# ------------------------------------------------------------------


@router.message(Command("vip"))
async def cmd_vip(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return
    if not await _require_premium(message, texts.VIP_REQUIRES_PREMIUM):
        return
    target, _ = await resolve_target(message, bot, command.args)
    if not target:
        await message.reply(texts.VIP_USAGE)
        return
    await db.add_vip(message.chat.id, target.id, message.from_user.id)
    await message.reply(texts.VIP_ADDED.format(target=mention_html(target.id, target.full_name)))


@router.message(Command("unvip"))
async def cmd_unvip(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return
    target, _ = await resolve_target(message, bot, command.args)
    if not target:
        await message.reply(texts.VIP_USAGE)
        return
    await db.remove_vip(message.chat.id, target.id)
    await message.reply(texts.VIP_REMOVED.format(target=mention_html(target.id, target.full_name)))


@router.message(Command("viplist"))
async def cmd_viplist(message: Message) -> None:
    if message.chat.type not in ("group", "supergroup"):
        await message.reply(texts.ONLY_IN_GROUP)
        return
    rows = await db.list_vips(message.chat.id)
    if not rows:
        await message.reply(texts.VIP_LIST_EMPTY)
        return
    lines = [texts.VIP_LIST_HEADER] + [f"- {r['user_id']}" for r in rows]
    await message.reply("\n".join(lines))


# ------------------------------------------------------------------
# 11. Moderators
# ------------------------------------------------------------------


@router.message(Command("addmod"))
async def cmd_addmod(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return
    if not await _require_premium(message, texts.MODERATOR_REQUIRES_PREMIUM):
        return
    target, _ = await resolve_target(message, bot, command.args)
    if not target:
        await message.reply(texts.MODERATOR_USAGE)
        return
    await db.add_moderator(message.chat.id, target.id, message.from_user.id)
    await message.reply(
        texts.MODERATOR_ADDED.format(target=mention_html(target.id, target.full_name))
    )


@router.message(Command("removemod"))
async def cmd_removemod(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return
    target, _ = await resolve_target(message, bot, command.args)
    if not target:
        await message.reply(texts.MODERATOR_USAGE)
        return
    await db.remove_moderator(message.chat.id, target.id)
    await message.reply(
        texts.MODERATOR_REMOVED.format(target=mention_html(target.id, target.full_name))
    )


@router.message(Command("modlist"))
async def cmd_modlist(message: Message) -> None:
    if message.chat.type not in ("group", "supergroup"):
        await message.reply(texts.ONLY_IN_GROUP)
        return
    rows = await db.list_moderators(message.chat.id)
    if not rows:
        await message.reply(texts.MODERATOR_LIST_EMPTY)
        return
    lines = [texts.MODERATOR_LIST_HEADER] + [f"- {r['user_id']}" for r in rows]
    await message.reply("\n".join(lines))


# ------------------------------------------------------------------
# 12. Scheduled messages
# ------------------------------------------------------------------


@router.message(Command("schedule"))
async def cmd_schedule(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return
    if not await _require_premium(message, texts.SCHEDULE_REQUIRES_PREMIUM):
        return
    raw = (command.args or "").strip()
    parts = raw.split(maxsplit=1)
    if len(parts) < 2 or ":" not in parts[0]:
        await message.reply(texts.SCHEDULE_USAGE)
        return
    time_part, text_part = parts[0], parts[1]
    hour_s, minute_s = time_part.split(":", maxsplit=1)
    if not (hour_s.isdigit() and minute_s.isdigit()):
        await message.reply(texts.SCHEDULE_USAGE)
        return
    hour, minute = int(hour_s), int(minute_s)
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        await message.reply(texts.SCHEDULE_USAGE)
        return
    await db.add_scheduled_message(message.chat.id, text_part, hour, minute, message.from_user.id)
    await message.reply(texts.SCHEDULE_ADDED.format(time=f"{hour:02d}:{minute:02d}"))


@router.message(Command("schedulelist"))
async def cmd_schedulelist(message: Message) -> None:
    if message.chat.type not in ("group", "supergroup"):
        await message.reply(texts.ONLY_IN_GROUP)
        return
    rows = await db.list_scheduled_messages(message.chat.id)
    if not rows:
        await message.reply(texts.SCHEDULE_LIST_EMPTY)
        return
    lines = [texts.SCHEDULE_LIST_HEADER]
    for r in rows:
        lines.append(f"#{r['id']} {r['hour']:02d}:{r['minute']:02d} — {r['text'][:40]}")
    await message.reply("\n".join(lines))


@router.message(Command("unschedule"))
async def cmd_unschedule(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return
    arg = (command.args or "").strip().lstrip("#")
    if not arg.isdigit():
        await message.reply(texts.SCHEDULE_NOT_FOUND)
        return
    removed = await db.remove_scheduled_message(int(arg), message.chat.id)
    await message.reply(texts.SCHEDULE_REMOVED if removed else texts.SCHEDULE_NOT_FOUND)


async def run_scheduled_messages(bot: Bot) -> None:
    """APScheduler orqali har daqiqada chaqiriladi (main.py'da)."""
    from utils import now_tashkent

    now = now_tashkent()
    all_messages = await db.get_all_scheduled_messages()
    today_str = now.strftime("%Y-%m-%d")
    for row in all_messages:
        if row["hour"] == now.hour and row["minute"] == now.minute and row["last_sent_date"] != today_str:
            try:
                await bot.send_message(row["chat_id"], row["text"])
            except TelegramAPIError:
                pass
            await db.mark_scheduled_message_sent(row["id"], today_str)


# ------------------------------------------------------------------
# 13. Link whitelist
# ------------------------------------------------------------------


@router.message(Command("allowlink"))
async def cmd_allowlink(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return
    if not await _require_premium(message, texts.LINKWHITELIST_REQUIRES_PREMIUM):
        return
    domain = (command.args or "").strip().lower()
    if not domain:
        await message.reply(texts.LINKWHITELIST_USAGE)
        return
    await db.add_whitelisted_domain(message.chat.id, domain)
    await message.reply(texts.LINKWHITELIST_ADDED.format(domain=domain))


@router.message(Command("unallowlink"))
async def cmd_unallowlink(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return
    domain = (command.args or "").strip().lower()
    removed = await db.remove_whitelisted_domain(message.chat.id, domain)
    await message.reply(
        texts.LINKWHITELIST_REMOVED.format(domain=domain) if removed else texts.LINKWHITELIST_EMPTY
    )


@router.message(Command("allowlinks"))
async def cmd_allowlinks(message: Message) -> None:
    if message.chat.type not in ("group", "supergroup"):
        await message.reply(texts.ONLY_IN_GROUP)
        return
    domains = await db.list_whitelisted_domains(message.chat.id)
    if not domains:
        await message.reply(texts.LINKWHITELIST_EMPTY)
        return
    await message.reply(f"{texts.LINKWHITELIST_HEADER}\n" + "\n".join(f"- {d}" for d in domains))


# ------------------------------------------------------------------
# 14. /dailyreport
# ------------------------------------------------------------------


@router.message(Command("dailyreport"))
async def cmd_dailyreport(message: Message, command: CommandObject, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return
    if not await _require_premium(message, texts.DAILYREPORT_REQUIRES_PREMIUM):
        return
    arg = (command.args or "").strip().lower()
    if arg == "off":
        await db.ensure_chat(message.chat.id, message.chat.title)
        await db.update_chat_setting(message.chat.id, daily_report_enabled=0)
        await message.reply(texts.DAILYREPORT_OFF)
        return
    if not arg.isdigit() or not (0 <= int(arg) <= 23):
        await message.reply(texts.DAILYREPORT_USAGE)
        return
    hour = int(arg)
    await db.ensure_chat(message.chat.id, message.chat.title)
    await db.update_chat_setting(
        message.chat.id,
        daily_report_enabled=1,
        daily_report_hour=hour,
        daily_report_admin_id=message.from_user.id,
    )
    await message.reply(texts.DAILYREPORT_ON.format(hour=hour))


async def run_daily_reports(bot: Bot) -> None:
    """APScheduler orqali har daqiqada chaqiriladi - soat mos kelgan
    guruhlarga kunlik hisobotni admin DM'iga yuboradi."""
    from handlers.report import generate_and_send_pdf
    from utils import now_tashkent

    now = now_tashkent()
    today_str = now.strftime("%Y-%m-%d")
    chats = await db.list_daily_report_chats()
    for row in chats:
        if row["daily_report_hour"] != now.hour or row["daily_report_last_date"] == today_str:
            continue
        if not row["daily_report_admin_id"]:
            continue
        since_ts = time.time() - 86400
        try:
            await generate_and_send_pdf(
                bot,
                row["chat_id"],
                row["chat_title"] or str(row["chat_id"]),
                since_ts,
                "so'nggi 24 soat",
                send_to_chat_id=row["daily_report_admin_id"],
            )
        except TelegramAPIError:
            pass
        await db.mark_daily_report_sent(row["chat_id"], today_str)


# ------------------------------------------------------------------
# 15. /backup
# ------------------------------------------------------------------


@router.message(Command("backup"))
async def cmd_backup(message: Message, bot: Bot) -> None:
    if not await _guard_admin(message, bot):
        return
    if not await _require_premium(message, texts.BACKUP_REQUIRES_PREMIUM):
        return
    await message.reply(texts.BACKUP_GENERATING)

    row = await db.get_chat_settings(message.chat.id)
    filters_rows = await db.all_filters(message.chat.id)
    notes_rows = await db.list_notes(message.chat.id)
    custom_commands_rows = await db.list_custom_commands(message.chat.id)

    data = {
        "chat_id": message.chat.id,
        "chat_title": message.chat.title,
        "settings": {k: row[k] for k in row.keys()} if row else {},
        "filters": [dict(r) for r in filters_rows],
        "notes": [r["name"] for r in notes_rows],
        "custom_commands": [r["name"] for r in custom_commands_rows],
    }
    payload = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
    filename = f"achi_backup_{message.chat.id}.json"
    await bot.send_document(
        message.chat.id, BufferedInputFile(payload, filename=filename), caption=texts.BACKUP_CAPTION
    )
