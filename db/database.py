import os
from datetime import datetime
from typing import List, Tuple

import aiosqlite

from bot.config import DB_PATH, MAX_FAIL_COUNT
from db.models import SCHEMA


async def init_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()


async def upsert_proxies(
    proxies: List[Tuple[str, int]],
    source: str = "scraper",
    is_alive: bool = False,
) -> int:
    inserted = 0
    async with aiosqlite.connect(DB_PATH) as db:
        for ip, port in proxies:
            try:
                await db.execute(
                    """
                    INSERT INTO proxies (ip, port, protocol, source, is_alive)
                    VALUES (?, ?, 'socks5', ?, ?)
                    ON CONFLICT(ip, port) DO UPDATE SET
                        source = excluded.source,
                        last_checked = datetime('now')
                    """,
                    (ip, port, source, int(is_alive)),
                )
                inserted += 1
            except Exception:
                continue
        await db.commit()
    return inserted


async def mark_alive(ip: str, port: int, alive: bool) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        if alive:
            await db.execute(
                """
                UPDATE proxies
                SET is_alive = 1, fail_count = 0, last_checked = datetime('now')
                WHERE ip = ? AND port = ?
                """,
                (ip, port),
            )
        else:
            await db.execute(
                """
                UPDATE proxies
                SET is_alive = 0, fail_count = fail_count + 1,
                    last_checked = datetime('now')
                WHERE ip = ? AND port = ?
                """,
                (ip, port),
            )
        await db.commit()


async def get_alive_proxies(limit: int = 10) -> List[Tuple[str, int]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT ip, port FROM proxies
            WHERE is_alive = 1
            ORDER BY last_checked DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = await cursor.fetchall()
        return [(row["ip"], row["port"]) for row in rows]


async def get_all_alive_proxies() -> List[Tuple[str, int]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT ip, port FROM proxies WHERE is_alive = 1 ORDER BY last_checked DESC"
        )
        rows = await cursor.fetchall()
        return [(row["ip"], row["port"]) for row in rows]


async def get_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM proxies")
        total = (await cursor.fetchone())[0]
        cursor = await db.execute("SELECT COUNT(*) FROM proxies WHERE is_alive = 1")
        alive = (await cursor.fetchone())[0]
        return {"total": total, "alive": alive}


async def delete_stale() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM proxies WHERE fail_count >= ?", (MAX_FAIL_COUNT,)
        )
        await db.commit()
        return cursor.rowcount


async def get_unchecked_proxies(limit: int = 200) -> List[Tuple[str, int]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT ip, port FROM proxies
            ORDER BY last_checked ASC NULLS FIRST
            LIMIT ?
            """,
            (limit,),
        )
        rows = await cursor.fetchall()
        return [(row["ip"], row["port"]) for row in rows]
