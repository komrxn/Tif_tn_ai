import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.config import settings
from src.db.client import close_db
from src.handlers import code_actions, help, history, photo, query, start, stats, unknown, voice
from src.health import run_health_server
from src.middleware.logging import LoggingMiddleware
from src.middleware.ratelimit import RateLimitMiddleware
from src.middleware.user import UserMiddleware

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()

    dp.update.middleware(LoggingMiddleware())
    dp.update.middleware(UserMiddleware())
    dp.message.middleware(RateLimitMiddleware())

    # Order matters: specific handlers before catch-all
    dp.include_router(start.router)
    dp.include_router(help.router)
    dp.include_router(history.router)
    dp.include_router(stats.router)
    dp.include_router(photo.router)
    dp.include_router(voice.router)
    dp.include_router(code_actions.router)
    dp.include_router(query.router)
    dp.include_router(unknown.router)

    return dp


async def main() -> None:
    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = build_dispatcher()
    logger.info("Starting bot")
    health_task = asyncio.create_task(run_health_server())
    try:
        await dp.start_polling(bot, drop_pending_updates=True)
    finally:
        health_task.cancel()
        await close_db()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
