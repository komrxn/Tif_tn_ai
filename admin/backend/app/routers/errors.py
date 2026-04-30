from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth import get_current_admin
from app.db import get_db

router = APIRouter(prefix="/api/errors", tags=["errors"])


class ErrorOut(BaseModel):
    id: str
    user_id: str | None
    telegram_id: int | None
    handler: str
    error_type: str
    message: str
    traceback: str | None
    query_type: str | None
    created_at: str


class ErrorPage(BaseModel):
    total: int
    items: list[ErrorOut]


def _serialize(row: dict) -> ErrorOut:
    user = row.get("user") or {}
    if isinstance(user, str):
        user = {}
    return ErrorOut(
        id=str(row["id"]),
        user_id=str(row["user"]) if row.get("user") else None,
        telegram_id=user.get("telegram_id"),
        handler=row.get("handler", ""),
        error_type=row.get("error_type", ""),
        message=row.get("message", ""),
        traceback=row.get("traceback"),
        query_type=row.get("query_type"),
        created_at=str(row.get("created_at", "")),
    )


@router.get("", response_model=ErrorPage)
async def list_errors(
    page: int = 1,
    limit: int = 50,
    handler: str = "",
    _: str = Depends(get_current_admin),
) -> ErrorPage:
    db = await get_db()
    offset = (page - 1) * limit
    params: dict = {"lim": limit, "off": offset}

    where = ""
    if handler:
        where = "WHERE handler = $handler"
        params["handler"] = handler

    count_rows = await db.query(
        f"SELECT count() AS cnt FROM error_logs {where} GROUP ALL",
        params,
    )
    total = count_rows[0]["cnt"] if count_rows else 0

    rows = await db.query(
        f"SELECT *, user.* FROM error_logs {where} ORDER BY created_at DESC LIMIT $lim START $off",
        params,
    )
    return ErrorPage(total=total, items=[_serialize(r) for r in (rows or [])])
