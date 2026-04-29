from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from src.db.repo import get_daily_usage
from src.ui.i18n import t

DAILY_LIMIT = 40


class RateLimitMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        user = data.get("user")
        lang = data.get("lang", "ru")
        if user:
            count = await get_daily_usage(str(user["id"]))
            if count >= DAILY_LIMIT:
                await event.answer(t(lang, "rate_limit"))
                return None

        return await handler(event, data)
