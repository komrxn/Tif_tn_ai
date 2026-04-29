import functools
import hashlib
import logging

from openai import AsyncOpenAI

from src.config import settings

logger = logging.getLogger(__name__)

_MODEL = "text-embedding-3-large"
_DIMENSIONS = 1536

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=30.0)
    return _client


@functools.lru_cache(maxsize=1024)
def _cache_key(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


# lru_cache doesn't support async directly; we use a plain dict with sha256 key
_embed_cache: dict[str, list[float]] = {}


async def embed(text: str) -> list[float]:
    key = _cache_key(text)
    if key in _embed_cache:
        return _embed_cache[key]

    resp = await _get_client().embeddings.create(
        model=_MODEL,
        input=text,
        dimensions=_DIMENSIONS,
    )
    vec = resp.data[0].embedding
    _embed_cache[key] = vec
    logger.debug("Embedded text (len=%d, cache_size=%d)", len(text), len(_embed_cache))
    return vec
