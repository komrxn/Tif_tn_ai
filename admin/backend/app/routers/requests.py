from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth import get_current_admin
from app.db import get_db

router = APIRouter(prefix="/api/requests", tags=["requests"])


class RequestOut(BaseModel):
    id: str
    user_id: str
    telegram_id: int | None
    username: str | None
    query_text: str
    query_type: str
    result_code: str | None
    result_name: str | None
    confidence: float | None
    response_time_ms: int
    tokens_prompt: int | None
    tokens_completion: int | None
    audio_seconds: float | None
    created_at: str


class RequestPage(BaseModel):
    total: int
    items: list[RequestOut]


def _serialize(row: dict) -> RequestOut:
    user = row.get("user") or {}
    if isinstance(user, str):
        user = {}
    return RequestOut(
        id=str(row["id"]),
        user_id=str(row.get("user", "")),
        telegram_id=user.get("telegram_id"),
        username=user.get("username"),
        query_text=row.get("query_text", ""),
        query_type=row.get("query_type", "text"),
        result_code=row.get("result_code"),
        result_name=row.get("result_name"),
        confidence=row.get("confidence"),
        response_time_ms=row.get("response_time_ms", 0),
        tokens_prompt=row.get("tokens_prompt"),
        tokens_completion=row.get("tokens_completion"),
        audio_seconds=row.get("audio_seconds"),
        created_at=str(row.get("created_at", "")),
    )


async def _fetch_requests(where: str, params: dict, page: int, limit: int) -> RequestPage:
    db = await get_db()
    offset = (page - 1) * limit

    count_rows = await db.query(
        f"SELECT count() AS cnt FROM query_logs {where} GROUP ALL",
        params,
    )
    total = count_rows[0]["cnt"] if count_rows else 0

    rows = await db.query(
        f"SELECT *, user.* FROM query_logs {where} ORDER BY created_at DESC LIMIT $lim START $off",
        {**params, "lim": limit, "off": offset},
    )
    return RequestPage(total=total, items=[_serialize(r) for r in (rows or [])])


@router.get("", response_model=RequestPage)
async def list_requests(
    page: int = 1,
    limit: int = 50,
    type: str = "all",
    _: str = Depends(get_current_admin),
) -> RequestPage:
    conditions: list[str] = []
    params: dict = {}

    if type in ("text", "photo", "voice"):
        conditions.append("query_type = $qtype")
        params["qtype"] = type
    elif type == "low_confidence":
        conditions.append("confidence != NONE AND confidence < 0.7")
    elif type == "failed":
        conditions.append("result_code = NONE")

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    return await _fetch_requests(where, params, page, limit)


@router.get("/low-confidence", response_model=RequestPage)
async def list_low_confidence(
    page: int = 1,
    limit: int = 50,
    _: str = Depends(get_current_admin),
) -> RequestPage:
    where = "WHERE confidence != NONE AND confidence < 0.7"
    return await _fetch_requests(where, {}, page, limit)


@router.get("/failed", response_model=RequestPage)
async def list_failed(
    page: int = 1,
    limit: int = 50,
    _: str = Depends(get_current_admin),
) -> RequestPage:
    return await _fetch_requests("WHERE result_code = NONE", {}, page, limit)
