import asyncio
import json
import logging
import re
from typing import List, Set, Tuple

import aiohttp

logger = logging.getLogger(__name__)

SOCKS5_SOURCES: List[str] = [
    # ===== GitHub repositories =====
    # --- Top-tier (updated every 5-10 min) ---
    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/socks5/data.txt",
    "https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/main/socks5.txt",
    "https://raw.githubusercontent.com/prxchk/proxy-list/main/socks5.txt",
    "https://raw.githubusercontent.com/r00tee/Proxy-List/main/Socks5.txt",
    # --- Updated every 15-30 min ---
    "https://raw.githubusercontent.com/VPSLabCloud/VPSLab-Free-Proxy-List/main/socks5_alive.txt",
    "https://raw.githubusercontent.com/Thordata/awesome-free-proxy-list/refs/heads/main/socks5.txt",
    "https://raw.githubusercontent.com/iplocate/free-proxy-list/main/proxy-list-socks5.txt",
    "https://raw.githubusercontent.com/gfpcom/free-proxy-list/main/lists/socks5.txt",
    # --- Updated hourly ---
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies_anonymous/socks5.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks5.txt",
    "https://raw.githubusercontent.com/thenasty1337/free-proxy-list/main/data/latest/types/socks5/proxies.txt",
    "https://raw.githubusercontent.com/proxygenerator1/ProxyGenerator/main/MostStable/socks5.txt",
    # --- Updated daily / regularly ---
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt",
    "https://vakhov.github.io/fresh-proxy-list/socks5.txt",
    "https://raw.githubusercontent.com/officialputuid/KangProxy/master/socks5/socks5.txt",
    "https://raw.githubusercontent.com/B4RC0DE-TM/proxy-list/main/SOCKS5.txt",
    "https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/socks5.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt",
    "https://raw.githubusercontent.com/HyperBeats/proxy-list/main/socks5.txt",
    "https://raw.githubusercontent.com/manuGMG/proxy-365/main/SOCKS5.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
    "https://raw.githubusercontent.com/BlackSnowDot/proxylist-update-every-minute/main/socks.txt",
    "https://raw.githubusercontent.com/ebrasha/abdal-proxy-hub/main/socks5-proxy-list-by-EbraSha.txt",
    # ===== API / external services =====
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&timeout=10000&country=all",
    "https://api.proxyscrape.com/?request=displayproxies&proxytype=socks5",
    "https://www.proxy-list.download/api/v1/get?type=socks5",
    "https://api.openproxylist.xyz/socks5.txt",
    "https://proxyspace.pro/socks5.txt",
    "https://proxylist.geonode.com/api/proxy-list?protocols=socks5&limit=500&page=1&sort_by=lastChecked&sort_type=desc",
    "https://raw.githubusercontent.com/wiki/gfpcom/free-proxy-list/lists/socks5.txt",
    "https://sunny9577.github.io/proxy-scraper/generated/socks5_proxies.txt",
]

_IP_PORT_RE = re.compile(
    r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})[:\s]+(\d{2,5})"
)


def _parse_proxies(text: str) -> List[Tuple[str, int]]:
    results: List[Tuple[str, int]] = []
    for match in _IP_PORT_RE.finditer(text):
        ip = match.group(1)
        port = int(match.group(2))
        if 1 <= port <= 65535:
            results.append((ip, port))
    return results


def _parse_json_proxies(text: str) -> List[Tuple[str, int]]:
    results: List[Tuple[str, int]] = []
    try:
        data = json.loads(text)
        items = data if isinstance(data, list) else data.get("data", [])
        for item in items:
            if isinstance(item, dict):
                ip = item.get("ip", "")
                port = item.get("port", "")
                if ip and port:
                    try:
                        p = int(port)
                        if 1 <= p <= 65535:
                            results.append((ip, p))
                    except (ValueError, TypeError):
                        continue
    except (json.JSONDecodeError, AttributeError):
        pass
    return results


async def _fetch_one(
    session: aiohttp.ClientSession, url: str
) -> List[Tuple[str, int]]:
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
            if resp.status != 200:
                logger.warning("Source %s returned status %d", url, resp.status)
                return []
            text = await resp.text(errors="ignore")
            proxies = _parse_proxies(text)
            if not proxies:
                proxies = _parse_json_proxies(text)
            logger.info("Source %s → %d proxies", url, len(proxies))
            return proxies
    except Exception as exc:
        logger.warning("Failed to fetch %s: %s", url, exc)
        return []


async def scrape_all(dedup_by_ip: bool = True) -> List[Tuple[str, int]]:
    seen_pair: Set[Tuple[str, int]] = set()
    seen_ip: Set[str] = set()
    all_proxies: List[Tuple[str, int]] = []

    async with aiohttp.ClientSession(
        headers={"User-Agent": "ProxyProviderBot/1.0"}
    ) as session:
        tasks = [_fetch_one(session, url) for url in SOCKS5_SOURCES]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, list):
            for ip, port in result:
                if (ip, port) in seen_pair:
                    continue
                seen_pair.add((ip, port))
                if dedup_by_ip:
                    if ip in seen_ip:
                        continue
                    seen_ip.add(ip)
                all_proxies.append((ip, port))

    dupes = len(seen_pair) - len(all_proxies)
    logger.info(
        "Total SOCKS5 scraped: %d unique pairs, %d after IP dedup (%d dupes removed)",
        len(seen_pair), len(all_proxies), dupes,
    )
    return all_proxies
