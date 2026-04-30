from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from src.db.repo import get_or_create_user


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Update):
            tg_user = (
                event.message.from_user
                if event.message
                else event.callback_query.from_user
                if event.callback_query
                else None
            )
            if tg_user:
                user = await get_or_create_user(
                    telegram_id=tg_user.id,
                    username=tg_user.username,
                )
                data["user"] = user
                data["lang"] = user.get("language", "uz")
                if user.get("is_blocked"):
                    return None
        return await handler(event, data)
