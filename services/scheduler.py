import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime

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


@dataclass
class JobStatus:
    is_running: bool = False
    cancel_requested: bool = False
    phase: str = "idle"
    total: int = 0
    checked: int = 0
    alive_found: int = 0
    scraped: int = 0
    last_run: str = "никогда"
    last_duration: str = ""


job_status = JobStatus()


async def scrape_and_validate_job() -> None:
    if job_status.is_running:
        logger.warning("Job already running, skipping")
        return

    job_status.is_running = True
    job_status.cancel_requested = False
    job_status.checked = 0
    job_status.alive_found = 0
    job_status.scraped = 0
    job_status.total = 0
    start_time = datetime.now()

    try:
        # Phase 1: scrape
        job_status.phase = "scraping"
        logger.info("=== Scrape & validate job started ===")

        raw = await scrape_all()
        job_status.scraped = len(raw)
        if raw:
            inserted = await upsert_proxies(raw, source="auto")
            logger.info("Upserted %d proxies into DB", inserted)

        if job_status.cancel_requested:
            logger.info("Job cancelled after scraping")
            return

        # Phase 2: validate
        job_status.phase = "validating"
        to_check = await get_unchecked_proxies(limit=300)
        job_status.total = len(to_check)

        if to_check:
            results = await validate_proxies(to_check)
            for (ip, port), alive in results:
                if job_status.cancel_requested:
                    logger.info("Job cancelled during validation")
                    return
                await mark_alive(ip, port, alive)
                job_status.checked += 1
                if alive:
                    job_status.alive_found += 1

        # Phase 3: cleanup
        job_status.phase = "cleanup"
        deleted = await delete_stale()
        if deleted:
            logger.info("Deleted %d stale proxies", deleted)

        logger.info("=== Scrape & validate job finished ===")
    finally:
        elapsed = datetime.now() - start_time
        minutes = int(elapsed.total_seconds() // 60)
        seconds = int(elapsed.total_seconds() % 60)
        job_status.last_duration = f"{minutes}м {seconds}с"
        job_status.last_run = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        job_status.phase = "idle"
        job_status.is_running = False
        job_status.cancel_requested = False


def cancel_job() -> bool:
    if not job_status.is_running:
        return False
    job_status.cancel_requested = True
    return True


def get_next_run() -> str:
    job = scheduler.get_job("scrape_validate")
    if job and job.next_run_time:
        return job.next_run_time.strftime("%d.%m.%Y %H:%M:%S")
    return "неизвестно"


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
