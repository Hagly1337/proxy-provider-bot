import asyncio
import logging
from typing import Callable, List, Optional, Tuple

import aiohttp
from aiohttp_socks import ProxyConnector

from bot.config import VALIDATE_TIMEOUT

logger = logging.getLogger(__name__)

CHECK_URL = "http://httpbin.org/ip"
CONCURRENCY = 100


async def _check_one(
    ip: str,
    port: int,
    semaphore: asyncio.Semaphore,
    on_result: Optional[Callable[[str, int, bool], None]] = None,
) -> Tuple[Tuple[str, int], bool]:
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

        if on_result:
            on_result(ip, port, alive)
        return (ip, port), alive


async def validate_proxies(
    proxies: List[Tuple[str, int]],
    on_result: Optional[Callable[[str, int, bool], None]] = None,
) -> List[Tuple[Tuple[str, int], bool]]:
    semaphore = asyncio.Semaphore(CONCURRENCY)
    tasks = [
        _check_one(ip, port, semaphore, on_result) for ip, port in proxies
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    output: List[Tuple[Tuple[str, int], bool]] = []
    for r in results:
        if isinstance(r, tuple):
            output.append(r)

    alive_count = sum(1 for _, a in output if a)
    logger.info("Validation done: %d/%d alive", alive_count, len(proxies))
    return output
