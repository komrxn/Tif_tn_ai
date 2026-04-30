import logging

from surrealdb import AsyncSurreal

from app.config import settings

logger = logging.getLogger(__name__)

_db: AsyncSurreal | None = None


async def get_db() -> AsyncSurreal:
    global _db
    if _db is None:
        raise RuntimeError("DB not initialized — call connect_db() first")
    return _db


async def connect_db() -> None:
    global _db
    _db = AsyncSurreal(settings.surreal_url)
    await _db.connect()
    await _db.signin({"username": settings.surreal_user, "password": settings.surreal_pass})
    await _db.use(settings.surreal_ns, settings.surreal_db)
    logger.info("Admin DB connected")


async def close_db() -> None:
    global _db
    if _db is not None:
        await _db.close()
        _db = None
