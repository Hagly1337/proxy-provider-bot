import asyncio
import logging
from aiohttp import web

from bot.config import API_PORT, API_SECRET
from db.database import get_unchecked_proxies, mark_alive

logger = logging.getLogger(__name__)

BATCH_SIZE = 1000


def _check_auth(request: web.Request) -> bool:
    token = request.headers.get("Authorization", "")
    return token == f"Bearer {API_SECRET}"


async def handle_get_batch(request: web.Request) -> web.Response:
    if not _check_auth(request):
        return web.json_response({"error": "unauthorized"}, status=401)

    try:
        limit = int(request.query.get("limit", str(BATCH_SIZE)))
        limit = min(limit, 3000)
    except ValueError:
        limit = BATCH_SIZE

    proxies = await get_unchecked_proxies(limit=limit)
    data = [{"ip": ip, "port": port} for ip, port in proxies]
    logger.info("API: Serving batch of %d proxies", len(data))
    return web.json_response({"proxies": data})


async def handle_submit_results(request: web.Request) -> web.Response:
    if not _check_auth(request):
        return web.json_response({"error": "unauthorized"}, status=401)

    try:
        body = await request.json()
        results = body.get("results", [])
    except Exception:
        return web.json_response({"error": "invalid json"}, status=400)

    updated = 0
    for item in results:
        ip = item.get("ip", "")
        port = item.get("port", 0)
        alive = item.get("alive", False)
        if ip and port:
            await mark_alive(ip, int(port), bool(alive))
            updated += 1

    logger.info("API: Received %d results from worker", updated)
    return web.json_response({"updated": updated})


async def handle_health(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/health", handle_health)
    app.router.add_get("/api/batch", handle_get_batch)
    app.router.add_post("/api/results", handle_submit_results)
    return app


async def start_api_server() -> None:
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", API_PORT)
    await site.start()
    logger.info("API server started on port %d", API_PORT)
