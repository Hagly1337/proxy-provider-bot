import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.config import SCRAPE_INTERVAL_MINUTES
from db.database import (
    delete_stale,
    get_unchecked_proxies,
    mark_alive,
    upsert_proxies,
)
from services.proxy_scraper import scrape_all
from services.proxy_validator import validate_proxies

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def scrape_and_validate_job() -> None:
    logger.info("=== Scrape & validate job started ===")

    raw = await scrape_all()
    if raw:
        inserted = await upsert_proxies(raw, source="auto")
        logger.info("Upserted %d proxies into DB", inserted)

    to_check = await get_unchecked_proxies(limit=300)
    if to_check:
        results = await validate_proxies(to_check)
        for (ip, port), alive in results:
            await mark_alive(ip, port, alive)

    deleted = await delete_stale()
    if deleted:
        logger.info("Deleted %d stale proxies", deleted)

    logger.info("=== Scrape & validate job finished ===")


def start_scheduler() -> None:
    scheduler.add_job(
        scrape_and_validate_job,
        "interval",
        minutes=SCRAPE_INTERVAL_MINUTES,
        id="scrape_validate",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started (every %d min)", SCRAPE_INTERVAL_MINUTES)
