"""
ACHI BOT - kirish nuqtasi.

Ishga tushirish: `python main.py` (avval .env faylini to'ldirib oling,
qarang: .env.example).
"""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import texts
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from config import settings
from database import db
from handlers import (
    admin_tools,
    content,
    cs2_market,
    extras,
    federation,
    greetings,
    moderation,
    panel,
    premium,
    premium_extras,
    report,
)
from middlewares import EnsureChatMiddleware, FloodMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("achi_bot")


async def cmd_help(message: Message) -> None:
    await message.answer(texts.HELP)


def register_basic_handlers(dp: Dispatcher) -> None:
    # /start endi handlers/panel.py'da - chunki u deep-link payload
    # ("panel_<chat_id>") orqali to'g'ridan-to'g'ri guruh menyusiga
    # o'tkazib yuborishi kerak (bot guruhga qo'shilgach yuboriladigan
    # onboarding tugmasi shu payload'ni ishlatadi).
    dp.message.register(panel.cmd_start, CommandStart(deep_link=True))
    dp.message.register(panel.cmd_start, Command("start"))
    dp.message.register(panel.cmd_panel, Command("panel"))
    dp.message.register(cmd_help, Command("help"))


async def on_startup(bot: Bot) -> None:
    await db.connect()
    logger.info("ACHI BOT ishga tushdi, DB ulandi: %s", settings.db_path)


async def on_shutdown(bot: Bot) -> None:
    await db.close()
    logger.info("ACHI BOT to'xtatildi, DB yopildi.")


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    async def _hourly_job() -> None:
        try:
            from handlers.report import run_hourly_reports

            await run_hourly_reports(bot)
        except Exception:
            logger.exception("Har soatlik hisobotni yuborishda xatolik")

    async def _captcha_sweep_job() -> None:
        try:
            from handlers.greetings import sweep_expired_captchas

            await sweep_expired_captchas(bot)
        except Exception:
            logger.exception("Captcha tozalashda xatolik")

    async def _scheduled_messages_job() -> None:
        try:
            from handlers.premium_extras import run_scheduled_messages

            await run_scheduled_messages(bot)
        except Exception:
            logger.exception("Rejalashtirilgan xabarlarni yuborishda xatolik")

    async def _daily_reports_job() -> None:
        try:
            from handlers.premium_extras import run_daily_reports

            await run_daily_reports(bot)
        except Exception:
            logger.exception("Kunlik hisobotlarni yuborishda xatolik")

    async def _night_mode_job() -> None:
        try:
            from handlers.night_mode import sweep_night_mode

            await sweep_night_mode(bot)
        except Exception:
            logger.exception("Tungi rejimni tekshirishda xatolik")

    scheduler.add_job(
        _hourly_job,
        trigger="interval",
        hours=settings.hourly_report_interval_hours,
        id="hourly_report",
        # APScheduler avtomatik ravishda birinchi ishga tushishni
        # "hozir + interval" qilib belgilaydi, ya'ni har soat oxirida ishlaydi.
    )
    scheduler.add_job(
        _captcha_sweep_job,
        trigger="interval",
        seconds=20,
        id="captcha_sweep",
    )
    # Rejalashtirilgan xabarlar, kunlik hisobotlar va tungi rejim daqiqa
    # aniqligida ishlashi kerak (masalan "09:00"da) - shu sabab har
    # daqiqada tekshiramiz.
    scheduler.add_job(
        _scheduled_messages_job, trigger="interval", minutes=1, id="scheduled_messages"
    )
    scheduler.add_job(_daily_reports_job, trigger="interval", minutes=1, id="daily_reports")
    scheduler.add_job(_night_mode_job, trigger="interval", minutes=1, id="night_mode")
    return scheduler


async def main() -> None:
    if not settings.bot_token:
        raise RuntimeError(
            "BOT_TOKEN topilmadi. .env faylini yarating (.env.example'dan nusxa oling) "
            "va BotFather'dan olingan tokenni qo'ying."
        )

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.outer_middleware(EnsureChatMiddleware())
    dp.message.middleware(FloodMiddleware())

    register_basic_handlers(dp)

    # Tartib muhim: avval moderatsiya (buyruqlar + qulflar), keyin
    # greetings/content. enforce_locks endi faqat haqiqiy qulflangan
    # tarkib uchun ishga tushadi, shu sabab boshqa routerlarni to'smaydi.
    # premium/federation buyruq-asosli bo'lgani uchun tartib muhim emas.
    # admin_tools va cs2_market content.router'dan OLDIN turishi shart -
    # chunki ular @admin/@admins va ".skin"/".oruzhiya" bilan boshlangan
    # matnlarni ushlab qolishi kerak, aks holda content.router'dagi
    # filter/eslatma catch-all handleri ularni "yutib qo'yishi" mumkin edi.
    dp.include_router(panel.router)
    dp.include_router(moderation.router)
    dp.include_router(premium.router)
    dp.include_router(premium_extras.router)
    dp.include_router(extras.router)
    dp.include_router(federation.router)
    dp.include_router(admin_tools.router)
    dp.include_router(cs2_market.router)
    dp.include_router(greetings.router)
    dp.include_router(content.router)
    dp.include_router(report.router)
    # content.fallback_router ENG OXIRIDA turishi SHART: u "personal"
    # (/xxx) custom buyruqlarni ushlaydi, lekin faqat yuqoridagi hech
    # qanaqa haqiqiy buyruq/handler ushlab olmagan xabarlar uchun -
    # aks holda haqiqiy buyruqlarni (/ban, /premium va h.k.) "yutib
    # qo'yishi" mumkin edi.
    dp.include_router(content.fallback_router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    scheduler = setup_scheduler(bot)
    scheduler.start()

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    asyncio.run(main())
