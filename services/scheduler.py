import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.config import SCRAPE_INTERVAL_MINUTES
from db.database import (
    delete_duplicate_ips,
    delete_stale,
    get_proxies_without_country,
    get_unchecked_proxies,
    mark_alive,
    update_country,
    upsert_proxies,
)
from services.geoip import ensure_geoip_db, lookup_country
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

PHASE_NAMES = {
    "idle": "✅ Ожидание",
    "scraping": "🔍 Сбор прокси",
    "validating": "🧪 Проверка",
    "geoip": "🌍 Определение стран",
    "cleanup": "🧹 Очистка мёртвых",
}


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
        to_check = await get_unchecked_proxies(limit=7000)
        job_status.total = len(to_check)

        def _on_result(ip: str, port: int, alive: bool) -> None:
            job_status.checked += 1
            if alive:
                job_status.alive_found += 1

        if to_check:
            results = await validate_proxies(to_check, on_result=_on_result)
            for (ip, port), alive in results:
                if job_status.cancel_requested:
                    logger.info("Job cancelled during DB update")
                    return
                await mark_alive(ip, port, alive)

        # Phase 3: GeoIP enrichment
        job_status.phase = "geoip"
        await ensure_geoip_db()
        no_country = await get_proxies_without_country(limit=2000)
        geo_count = 0
        for ip, port in no_country:
            if job_status.cancel_requested:
                break
            country = lookup_country(ip)
            if country:
                await update_country(ip, port, country)
                geo_count += 1
        if geo_count:
            logger.info("GeoIP enriched %d proxies", geo_count)

        # Phase 4: cleanup
        job_status.phase = "cleanup"
        dupes = await delete_duplicate_ips()
        if dupes:
            logger.info("Deleted %d duplicate IP entries", dupes)
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
