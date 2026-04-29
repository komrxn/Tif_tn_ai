import json
import logging
from typing import Any

import redis.asyncio as aioredis

from src.config import settings

logger = logging.getLogger(__name__)

_SESSION_TTL = 1800  # 30 minutes
_SESSION_KEY = "tnved:session:{}"

_client: aioredis.Redis | None = None


def _get_client() -> aioredis.Redis:
    global _client
    if _client is None:
        _client = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _client


async def get_session(chat_id: int) -> dict[str, Any] | None:
    raw = await _get_client().get(_SESSION_KEY.format(chat_id))
    if raw is None:
        return None
    return json.loads(raw)


async def set_session(chat_id: int, data: dict[str, Any]) -> None:
    await _get_client().setex(
        _SESSION_KEY.format(chat_id),
        _SESSION_TTL,
        json.dumps(data, ensure_ascii=False),
    )


async def clear_session(chat_id: int) -> None:
    await _get_client().delete(_SESSION_KEY.format(chat_id))
