from __future__ import annotations

import logging

from surrealdb import AsyncSurreal, AsyncWsSurrealConnection

from app.config import settings

logger = logging.getLogger(__name__)

_db: AsyncWsSurrealConnection | None = None


async def get_db() -> AsyncWsSurrealConnection:
    global _db
    if _db is None:
        raise RuntimeError("DB not initialized — call connect_db() first")
    return _db


async def connect_db() -> None:
    global _db
    conn = AsyncSurreal(settings.surreal_url)
    await conn.connect()
    await conn.signin({"username": settings.surreal_user, "password": settings.surreal_pass})
    await conn.use(settings.surreal_ns, settings.surreal_db)
    _db = conn
    logger.info("Admin DB connected to %s", settings.surreal_url)


async def close_db() -> None:
    global _db
    if _db is not None:
        await _db.close()
        _db = None
