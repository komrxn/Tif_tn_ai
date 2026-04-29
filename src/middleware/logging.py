import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        t0 = time.monotonic()
        update_id = event.update_id if isinstance(event, Update) else "-"
        logger.info("Update %s start", update_id)
        try:
            result = await handler(event, data)
            elapsed = int((time.monotonic() - t0) * 1000)
            logger.info("Update %s done in %dms", update_id, elapsed)
            return result
        except Exception:
            logger.error("Update %s failed", update_id, exc_info=True)
            raise
