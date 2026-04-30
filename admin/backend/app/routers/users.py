from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth import get_current_admin
from app.db import get_db

router = APIRouter(prefix="/api/users", tags=["users"])


class UserOut(BaseModel):
    id: str
    telegram_id: int
    username: str | None
    language: str
    is_blocked: bool
    last_seen_at: str
    created_at: str


class UserPage(BaseModel):
    total: int
    items: list[UserOut]


class BlockRequest(BaseModel):
    is_blocked: bool


def _serialize_user(row: dict) -> UserOut:
    return UserOut(
        id=str(row["id"]),
        telegram_id=row["telegram_id"],
        username=row.get("username"),
        language=row.get("language", "uz"),
        is_blocked=row.get("is_blocked", False),
        last_seen_at=str(row.get("last_seen_at", "")),
        created_at=str(row.get("created_at", "")),
    )


async def _count_and_fetch(
    where: str,
    params: dict,
    page: int,
    limit: int,
) -> UserPage:
    db = await get_db()
    offset = (page - 1) * limit

    count_rows = await db.query(
        f"SELECT count() AS cnt FROM users {where} GROUP ALL",
        params,
    )
    total = count_rows[0]["cnt"] if count_rows else 0

    rows = await db.query(
        f"SELECT * FROM users {where} ORDER BY created_at DESC LIMIT $lim START $off",
        {**params, "lim": limit, "off": offset},
    )
    return UserPage(total=total, items=[_serialize_user(r) for r in (rows or [])])


@router.get("", response_model=UserPage)
async def list_users(
    page: int = 1,
    limit: int = 50,
    search: str = "",
    filter: str = "all",
    _: str = Depends(get_current_admin),
) -> UserPage:
    conditions: list[str] = []
    params: dict = {}

    if filter == "active":
        conditions.append("id IN (SELECT user FROM query_logs WHERE created_at > time::now() - 7d)")
    elif filter == "blocked":
        conditions.append("is_blocked = true")

    if search:
        conditions.append("(string::contains(string(telegram_id), $search) OR string::contains(username ?? '', $search))")
        params["search"] = search

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    return await _count_and_fetch(where, params, page, limit)


@router.get("/active", response_model=UserPage)
async def list_active(
    page: int = 1,
    limit: int = 50,
    days: int = 7,
    _: str = Depends(get_current_admin),
) -> UserPage:
    where = "WHERE id IN (SELECT VALUE user FROM query_logs WHERE created_at > time::now() - type::duration(string($days) + 'd'))"
    return await _count_and_fetch(where, {"days": days}, page, limit)


@router.get("/blocked", response_model=UserPage)
async def list_blocked(
    page: int = 1,
    limit: int = 50,
    _: str = Depends(get_current_admin),
) -> UserPage:
    return await _count_and_fetch("WHERE is_blocked = true", {}, page, limit)


@router.patch("/{user_id}/block", response_model=dict)
async def set_blocked(
    user_id: str,
    body: BlockRequest,
    _: str = Depends(get_current_admin),
) -> dict:
    db = await get_db()
    result = await db.query(
        "UPDATE type::record($uid) SET is_blocked = $blocked RETURN id, is_blocked",
        {"uid": user_id, "blocked": body.is_blocked},
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    row = result[0]
    return {"id": str(row["id"]), "is_blocked": row["is_blocked"]}
