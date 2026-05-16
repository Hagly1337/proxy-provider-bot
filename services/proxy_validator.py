import asyncio
import logging
from typing import List, Tuple

import aiohttp
from aiohttp_socks import ProxyConnector

from bot.config import VALIDATE_TIMEOUT

logger = logging.getLogger(__name__)

CHECK_URL = "http://httpbin.org/ip"
CONCURRENCY = 50


async def _check_one(ip: str, port: int, semaphore: asyncio.Semaphore) -> bool:
    async with semaphore:
        proxy_url = f"socks5://{ip}:{port}"
        try:
            connector = ProxyConnector.from_url(proxy_url)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(
                    CHECK_URL,
                    timeout=aiohttp.ClientTimeout(total=VALIDATE_TIMEOUT),
                ) as resp:
                    if resp.status == 200:
                        logger.debug("ALIVE %s:%d", ip, port)
                        return True
        except Exception:
            pass
        logger.debug("DEAD  %s:%d", ip, port)
        return False


async def validate_proxies(
    proxies: List[Tuple[str, int]],
) -> List[Tuple[Tuple[str, int], bool]]:
    semaphore = asyncio.Semaphore(CONCURRENCY)
    tasks = [_check_one(ip, port, semaphore) for ip, port in proxies]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    output: List[Tuple[Tuple[str, int], bool]] = []
    for proxy, result in zip(proxies, results):
        alive = result if isinstance(result, bool) else False
        output.append((proxy, alive))

    alive_count = sum(1 for _, a in output if a)
    logger.info("Validation done: %d/%d alive", alive_count, len(proxies))
    return output
