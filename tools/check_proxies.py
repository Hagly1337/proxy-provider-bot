#!/usr/bin/env python3
"""
Local SOCKS5 proxy checker.
Reads proxies from a .txt file (ip:port per line), checks them, and saves alive ones.

Usage:
  pip install aiohttp aiohttp-socks
  python check_proxies.py proxies.txt
  python check_proxies.py proxies.txt --output alive.txt --concurrency 300 --timeout 10
"""
import argparse
import asyncio
import sys
import time

try:
    import aiohttp
    from aiohttp_socks import ProxyConnector
except ImportError:
    print("Install dependencies first:\n  pip install aiohttp aiohttp-socks")
    sys.exit(1)

CHECK_URL = "http://httpbin.org/ip"
DEFAULT_TIMEOUT = 10
DEFAULT_CONCURRENCY = 200


async def check_one(
    ip: str, port: int, semaphore: asyncio.Semaphore, timeout: int
) -> tuple:
    async with semaphore:
        proxy_url = f"socks5://{ip}:{port}"
        try:
            connector = ProxyConnector.from_url(proxy_url)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(
                    CHECK_URL,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                ) as resp:
                    if resp.status == 200:
                        return ip, port, True
        except Exception:
            pass
        return ip, port, False


def load_proxies(filepath: str) -> list:
    proxies = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or ":" not in line:
                continue
            parts = line.split(":")
            if len(parts) != 2:
                continue
            ip, port_str = parts
            try:
                port = int(port_str)
                if 1 <= port <= 65535:
                    proxies.append((ip, port))
            except ValueError:
                continue
    return proxies


async def main(args):
    proxies = load_proxies(args.input)
    if not proxies:
        print(f"No proxies found in {args.input}")
        return

    print(f"Loaded {len(proxies)} proxies from {args.input}")
    print(f"Concurrency: {args.concurrency}, Timeout: {args.timeout}s")
    print()

    semaphore = asyncio.Semaphore(args.concurrency)
    checked = 0
    alive_count = 0
    alive_list = []
    start = time.time()

    tasks = [check_one(ip, port, semaphore, args.timeout) for ip, port in proxies]

    for coro in asyncio.as_completed(tasks):
        ip, port, is_alive = await coro
        checked += 1
        if is_alive:
            alive_count += 1
            alive_list.append(f"{ip}:{port}")
            print(f"  \033[92m✓ {ip}:{port}\033[0m")

        if checked % 100 == 0 or checked == len(proxies):
            elapsed = time.time() - start
            speed = checked / elapsed if elapsed > 0 else 0
            print(
                f"  [{checked}/{len(proxies)}] "
                f"alive: {alive_count} | "
                f"{speed:.0f} proxies/sec",
                end="\r",
            )

    elapsed = time.time() - start
    print()
    print()
    print(f"Done in {elapsed:.1f}s")
    print(f"Total: {len(proxies)}, Alive: {alive_count}, Dead: {len(proxies) - alive_count}")

    if alive_list:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write("\n".join(alive_list) + "\n")
        print(f"Saved {alive_count} alive proxies to {args.output}")
    else:
        print("No alive proxies found.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Local SOCKS5 proxy checker")
    parser.add_argument("input", help="Input file with proxies (ip:port per line)")
    parser.add_argument(
        "--output", "-o", default="alive.txt",
        help="Output file for alive proxies (default: alive.txt)"
    )
    parser.add_argument(
        "--concurrency", "-c", type=int, default=DEFAULT_CONCURRENCY,
        help=f"Max concurrent checks (default: {DEFAULT_CONCURRENCY})"
    )
    parser.add_argument(
        "--timeout", "-t", type=int, default=DEFAULT_TIMEOUT,
        help=f"Timeout per proxy in seconds (default: {DEFAULT_TIMEOUT})"
    )
    asyncio.run(main(parser.parse_args()))
