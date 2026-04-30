import logging
from datetime import UTC, datetime
from typing import Literal

from src.db.client import get_db

logger = logging.getLogger(__name__)

Lang = Literal["uz", "ru", "en"]


async def get_or_create_user(
    telegram_id: int,
    username: str | None = None,
    language: Lang = "uz",
) -> dict:
    db = await get_db()
    rows = await db.query(
        "SELECT * FROM users WHERE telegram_id = $tg",
        {"tg": telegram_id},
    )
    if rows:
        user = rows[0]
        await db.query(
            "UPDATE type::record($uid) SET last_seen_at = time::now()",
            {"uid": str(user["id"])},
        )
        return user

    created = await db.create(
        "users",
        {"telegram_id": telegram_id, "username": username, "language": language},
    )
    return created[0] if isinstance(created, list) else created


async def set_user_language(user_id: str, language: Lang) -> None:
    db = await get_db()
    await db.query(
        "UPDATE type::record($uid) SET language = $lang",
        {"uid": user_id, "lang": language},
    )


async def get_daily_usage(user_id: str) -> int:
    db = await get_db()
    today = datetime.now(UTC).date().isoformat()
    rows = await db.query(
        "SELECT count FROM daily_usage WHERE user = type::record($uid) AND date = $d",
        {"uid": user_id, "d": today},
    )
    return rows[0]["count"] if rows else 0


async def increment_daily_usage(user_id: str) -> None:
    db = await get_db()
    today = datetime.now(UTC).date().isoformat()
    await db.query(
        """
        LET $existing = (SELECT * FROM daily_usage WHERE user = type::record($uid) AND date = $d);
        IF $existing {
            UPDATE $existing[0].id SET count += 1;
        } ELSE {
            CREATE daily_usage SET user = type::record($uid), date = $d, count = 1;
        }
        """,
        {"uid": user_id, "d": today},
    )


async def log_query(
    user_id: str,
    query_text: str,
    query_type: Literal["text", "photo", "voice"],
    result_code: str | None,
    result_name: str | None,
    confidence: float | None,
    response_time_ms: int,
    tokens_prompt: int | None = None,
    tokens_completion: int | None = None,
    audio_seconds: float | None = None,
) -> None:
    db = await get_db()
    await db.query(
        """
        CREATE query_logs SET
            user             = type::record($uid),
            query_text       = $qt,
            query_type       = $qtype,
            result_code      = $code,
            result_name      = $name,
            confidence       = $conf,
            response_time_ms = $ms,
            tokens_prompt    = $tp,
            tokens_completion = $tc,
            audio_seconds    = $as
        """,
        {
            "uid": user_id,
            "qt": query_text,
            "qtype": query_type,
            "code": result_code,
            "name": result_name,
            "conf": confidence,
            "ms": response_time_ms,
            "tp": tokens_prompt,
            "tc": tokens_completion,
            "as": audio_seconds,
        },
    )


async def set_user_blocked(user_id: str, is_blocked: bool) -> None:
    db = await get_db()
    await db.query(
        "UPDATE type::record($uid) SET is_blocked = $blocked",
        {"uid": user_id, "blocked": is_blocked},
    )


async def log_error(
    handler: str,
    error_type: str,
    message: str,
    traceback: str | None = None,
    user_id: str | None = None,
    query_type: str | None = None,
) -> None:
    db = await get_db()
    await db.query(
        """
        CREATE error_logs SET
            user       = IF $uid != NONE THEN type::record($uid) ELSE NONE END,
            handler    = $handler,
            error_type = $etype,
            message    = $msg,
            traceback  = $tb,
            query_type = $qtype
        """,
        {
            "uid": user_id,
            "handler": handler,
            "etype": error_type,
            "msg": message,
            "tb": traceback,
            "qtype": query_type,
        },
    )


async def get_user_history(user_id: str, limit: int = 10) -> list[dict]:
    db = await get_db()
    return await db.query(
        "SELECT * FROM query_logs WHERE user = type::record($uid)"
        " ORDER BY created_at DESC LIMIT $n",
        {"uid": user_id, "n": limit},
    )


async def lookup_duty(code: str) -> dict | None:
    """Exact match then longest prefix fallback: 10→8→6→4."""
    db = await get_db()
    for prefix_len in (len(code), 8, 6, 4):
        prefix = code[:prefix_len]
        if not prefix:
            break
        rows = await db.query(
            "SELECT * FROM duties WHERE code = $c",
            {"c": prefix},
        )
        if rows:
            return rows[0]
    return None


async def lookup_code(code: str) -> dict | None:
    db = await get_db()
    rows = await db.query("SELECT * FROM codes WHERE code = $c", {"c": code})
    return rows[0] if rows else None


async def get_code_ancestors(code: str) -> list[dict]:
    """Walk up the parent chain and return ordered list root→leaf."""
    db = await get_db()
    chain: list[dict] = []
    current = code
    visited: set[str] = set()
    while current and current not in visited:
        visited.add(current)
        rows = await db.query("SELECT * FROM codes WHERE code = $c", {"c": current})
        if not rows:
            break
        row = rows[0]
        chain.append(row)
        current = row.get("parent")
    chain.reverse()
    return chain


async def get_code_children(code: str) -> list[dict]:
    db = await get_db()
    return await db.query("SELECT * FROM codes WHERE parent = $c", {"c": code})


async def get_top_chunk_for_code(code: str) -> dict | None:
    db = await get_db()
    for prefix_len in (len(code), 4):
        prefix = code[:prefix_len]
        rows = await db.query(
            "SELECT * FROM chunks WHERE primary_code = $c LIMIT 1",
            {"c": prefix},
        )
        if rows:
            return rows[0]
    return None
