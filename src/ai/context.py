import json
import logging

import redis.asyncio as aioredis

from src.config import settings

logger = logging.getLogger(__name__)

_HISTORY_TTL = 3600  # 1 hour
_MAX_TURNS = 3
_HISTORY_KEY = "tnved:history:{}"

_client: aioredis.Redis | None = None


def _get_client() -> aioredis.Redis:
    global _client
    if _client is None:
        _client = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _client


async def get_history(chat_id: int) -> list[tuple[str, str | None, str]]:
    raw = await _get_client().get(_HISTORY_KEY.format(chat_id))
    if raw is None:
        return []
    stored = json.loads(raw)
    # Migrate old 2-tuple format to 3-tuple
    result = []
    for item in stored:
        if len(item) == 2:
            result.append((item[0], item[1], ""))
        else:
            result.append(tuple(item))
    return result


async def push_turn(chat_id: int, query: str, result_code: str | None, name: str = "") -> None:
    turns = await get_history(chat_id)
    turns.append((query, result_code, name))
    if len(turns) > _MAX_TURNS:
        turns = turns[-_MAX_TURNS:]
    await _get_client().setex(
        _HISTORY_KEY.format(chat_id),
        _HISTORY_TTL,
        json.dumps(turns, ensure_ascii=False),
    )
