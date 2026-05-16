import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))

DB_PATH: str = str(BASE_DIR / "data" / "proxies.db")

SCRAPE_INTERVAL_MINUTES: int = 15
VALIDATE_TIMEOUT: int = 10
PROXY_BATCH_SIZE: int = 10
MAX_FAIL_COUNT: int = 3
