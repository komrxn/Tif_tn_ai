import json
import logging

import redis.asyncio as aioredis

from src.config import settings

logger = logging.getLogger(__name__)

_CARDS_TTL = 30 * 24 * 3600  # 30 days
_MAX_CARDS = 10
_CARDS_KEY = "tnved:cards:{}"

_client: aioredis.Redis | None = None


def _get_client() -> aioredis.Redis:
    global _client
    if _client is None:
        _client = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _client


async def save_card(
    chat_id: int,
    code: str,
    name: str,
    justification: str,
    confidence: float,
    alternative_codes: list[dict],
    query: str,
) -> None:
    key = _CARDS_KEY.format(chat_id)
    client = _get_client()
    raw = await client.get(key)
    cards: list[dict] = json.loads(raw) if raw else []
    cards = [c for c in cards if c.get("code") != code]
    cards.insert(
        0,
        {
            "code": code,
            "name": name,
            "justification": justification,
            "confidence": confidence,
            "alternative_codes": alternative_codes,
            "query": query,
        },
    )
    cards = cards[:_MAX_CARDS]
    await client.setex(key, _CARDS_TTL, json.dumps(cards, ensure_ascii=False))


async def get_card(chat_id: int, code: str) -> dict | None:
    raw = await _get_client().get(_CARDS_KEY.format(chat_id))
    if not raw:
        return None
    for card in json.loads(raw):
        if card.get("code") == code:
            return card
    return None


async def get_cards(chat_id: int, limit: int = 10) -> list[dict]:
    raw = await _get_client().get(_CARDS_KEY.format(chat_id))
    if not raw:
        return []
    return json.loads(raw)[:limit]
