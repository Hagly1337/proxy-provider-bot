import logging
import os
import tarfile
from pathlib import Path

import aiohttp
import geoip2.database

from bot.config import BASE_DIR

logger = logging.getLogger(__name__)

GEOIP_DIR = BASE_DIR / "data"
DB_FILE = GEOIP_DIR / "GeoLite2-Country.mmdb"
DOWNLOAD_URL = "https://raw.githubusercontent.com/P3TERX/GeoLite.mmdb/download/GeoLite2-Country.mmdb"

_reader = None


async def ensure_geoip_db() -> bool:
    if DB_FILE.exists():
        return True
    logger.info("Downloading GeoLite2-Country.mmdb...")
    os.makedirs(GEOIP_DIR, exist_ok=True)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(DOWNLOAD_URL, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status != 200:
                    logger.error("Failed to download GeoIP DB: status %d", resp.status)
                    return False
                data = await resp.read()
                DB_FILE.write_bytes(data)
                logger.info("GeoIP DB downloaded: %.1f MB", len(data) / 1024 / 1024)
                return True
    except Exception as e:
        logger.error("Failed to download GeoIP DB: %s", e)
        return False


def get_reader():
    global _reader
    if _reader is None and DB_FILE.exists():
        _reader = geoip2.database.Reader(str(DB_FILE))
    return _reader


def lookup_country(ip: str) -> str:
    reader = get_reader()
    if not reader:
        return ""
    try:
        response = reader.country(ip)
        return response.country.iso_code or ""
    except Exception:
        return ""
