#!/usr/bin/env python3
"""
Proxy Provider Bot — Worker Node
Connects to master server, fetches batches of proxies,
validates them, and sends results back.

Usage:
  python worker.py --master http://MASTER_IP:8080 --secret YOUR_API_SECRET
"""
import argparse
import asyncio
import logging
import sys

import aiohttp
from aiohttp_socks import ProxyConnector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("worker")

CHECK_URL = "http://httpbin.org/ip"
VALIDATE_TIMEOUT = 10
CONCURRENCY = 200
BATCH_SIZE = 1000
SLEEP_BETWEEN_BATCHES = 5


async def check_one(
    ip: str, port: int, semaphore: asyncio.Semaphore
) -> dict:
    async with semaphore:
        proxy_url = f"socks5://{ip}:{port}"
        alive = False
        try:
            connector = ProxyConnector.from_url(proxy_url)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(
                    CHECK_URL,
                    timeout=aiohttp.ClientTimeout(total=VALIDATE_TIMEOUT),
                ) as resp:
                    if resp.status == 200:
                        alive = True
        except Exception:
            pass
        return {"ip": ip, "port": port, "alive": alive}


async def fetch_batch(
    session: aiohttp.ClientSession, master_url: str, secret: str
) -> list:
    url = f"{master_url}/api/batch?limit={BATCH_SIZE}"
    headers = {"Authorization": f"Bearer {secret}"}
    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status == 401:
                logger.error("Auth failed! Check --secret")
                return []
            data = await resp.json()
            return data.get("proxies", [])
    except Exception as e:
        logger.error("Failed to fetch batch: %s", e)
        return []


async def submit_results(
    session: aiohttp.ClientSession, master_url: str, secret: str, results: list
) -> bool:
    url = f"{master_url}/api/results"
    headers = {"Authorization": f"Bearer {secret}"}
    try:
        async with session.post(url, json={"results": results}, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            data = await resp.json()
            logger.info("Submitted %d results → updated: %d", len(results), data.get("updated", 0))
            return True
    except Exception as e:
        logger.error("Failed to submit results: %s", e)
        return False


async def run_worker(master_url: str, secret: str) -> None:
    logger.info("Worker starting, master: %s", master_url)

    async with aiohttp.ClientSession() as session:
        # Health check
        try:
            async with session.get(f"{master_url}/health", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status != 200:
                    logger.error("Master health check failed!")
                    return
                logger.info("Master is healthy ✓")
        except Exception as e:
            logger.error("Cannot reach master at %s: %s", master_url, e)
            return

        cycle = 0
        while True:
            cycle += 1
            logger.info("--- Cycle %d ---", cycle)

            batch = await fetch_batch(session, master_url, secret)
            if not batch:
                logger.info("No proxies to check, sleeping 30s...")
                await asyncio.sleep(30)
                continue

            logger.info("Got %d proxies to validate", len(batch))
            semaphore = asyncio.Semaphore(CONCURRENCY)
            tasks = [
                check_one(p["ip"], p["port"], semaphore) for p in batch
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            valid_results = [r for r in results if isinstance(r, dict)]
            alive_count = sum(1 for r in valid_results if r["alive"])
            logger.info("Checked %d, alive: %d", len(valid_results), alive_count)

            await submit_results(session, master_url, secret, valid_results)

            logger.info("Sleeping %ds before next batch...", SLEEP_BETWEEN_BATCHES)
            await asyncio.sleep(SLEEP_BETWEEN_BATCHES)


def main():
    global CONCURRENCY, BATCH_SIZE

    parser = argparse.ArgumentParser(description="Proxy Provider Worker")
    parser.add_argument(
        "--master", required=True,
        help="Master server URL, e.g. http://123.45.67.89:8080"
    )
    parser.add_argument(
        "--secret", required=True,
        help="API secret (must match API_SECRET on master)"
    )
    parser.add_argument(
        "--concurrency", type=int, default=CONCURRENCY,
        help="Max concurrent checks (default: 100)"
    )
    parser.add_argument(
        "--batch-size", type=int, default=BATCH_SIZE,
        help="Proxies per batch (default: 500)"
    )
    args = parser.parse_args()

    CONCURRENCY = args.concurrency
    BATCH_SIZE = args.batch_size

    asyncio.run(run_worker(args.master, args.secret))


if __name__ == "__main__":
    main()
