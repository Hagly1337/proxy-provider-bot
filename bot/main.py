import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import BOT_TOKEN
from bot.handlers import admin, user
from db.database import init_db
from services.scheduler import scrape_and_validate_job, start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot) -> None:
    logger.info("Initializing database…")
    await init_db()

    logger.info("Starting scheduler…")
    start_scheduler()

    logger.info("Running initial scrape & validate…")
    asyncio.create_task(scrape_and_validate_job())

    me = await bot.get_me()
    logger.info("Bot started: @%s", me.username)


async def main() -> None:
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is not set! Create .env file from .env.example")
        sys.exit(1)

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(user.router)
    dp.include_router(admin.router)

    dp.startup.register(on_startup)

    logger.info("Starting polling…")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
