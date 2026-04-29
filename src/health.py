import asyncio
import json
import logging

from aiohttp import web

logger = logging.getLogger(__name__)

_PORT = 8080


async def _handle(_: web.Request) -> web.Response:
    return web.Response(
        text=json.dumps({"status": "ok"}),
        content_type="application/json",
    )


async def run_health_server() -> None:
    app = web.Application()
    app.router.add_get("/health", _handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", _PORT)
    await site.start()
    logger.info("Health server listening on :%d", _PORT)
    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()
