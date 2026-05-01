import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth import get_current_admin
from app.db import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


class DashboardStats(BaseModel):
    total_users: int
    blocked_users: int
    total_queries_today: int
    total_queries_all: int
    avg_response_ms: int
    queries_by_type: dict[str, int]
    low_confidence_count: int
    failed_count: int
    errors_today: int


@router.get("/stats", response_model=DashboardStats)
async def get_stats(_: str = Depends(get_current_admin)) -> DashboardStats:
    db = await get_db()

    total_rows = await db.query("SELECT count() AS cnt FROM users GROUP ALL")
    total_users = total_rows[0]["cnt"] if total_rows else 0

    blocked_rows = await db.query(
        "SELECT count() AS cnt FROM users WHERE is_blocked = true GROUP ALL"
    )
    blocked_users = blocked_rows[0]["cnt"] if blocked_rows else 0

    today_rows = await db.query(
        "SELECT count() AS cnt FROM query_logs WHERE created_at > time::now() - 1d GROUP ALL"
    )
    total_queries_today = today_rows[0]["cnt"] if today_rows else 0

    all_rows = await db.query("SELECT count() AS cnt FROM query_logs GROUP ALL")
    total_queries_all = all_rows[0]["cnt"] if all_rows else 0

    avg_rows = await db.query(
        "SELECT math::mean(response_time_ms) AS avg FROM query_logs GROUP ALL"
    )
    avg_response_ms = int(avg_rows[0]["avg"] or 0) if avg_rows else 0

    type_rows = await db.query(
        "SELECT query_type, count() AS cnt FROM query_logs GROUP BY query_type"
    )
    queries_by_type = {r["query_type"]: r["cnt"] for r in (type_rows or [])}

    lc_rows = await db.query(
        "SELECT count() AS cnt FROM query_logs"
        " WHERE confidence != NONE AND confidence < 0.7"
        " AND created_at > time::now() - 7d GROUP ALL"
    )
    low_confidence_count = lc_rows[0]["cnt"] if lc_rows else 0

    fail_rows = await db.query(
        "SELECT count() AS cnt FROM query_logs"
        " WHERE result_code = NONE AND created_at > time::now() - 7d GROUP ALL"
    )
    failed_count = fail_rows[0]["cnt"] if fail_rows else 0

    errors_today = 0
    try:
        err_rows = await db.query(
            "SELECT count() AS cnt FROM error_logs"
            " WHERE created_at > time::now() - 1d GROUP ALL"
        )
        errors_today = err_rows[0]["cnt"] if err_rows else 0
    except Exception:
        logger.debug("error_logs table not yet created")

    return DashboardStats(
        total_users=total_users,
        blocked_users=blocked_users,
        total_queries_today=total_queries_today,
        total_queries_all=total_queries_all,
        avg_response_ms=avg_response_ms,
        queries_by_type=queries_by_type,
        low_confidence_count=low_confidence_count,
        failed_count=failed_count,
        errors_today=errors_today,
    )
