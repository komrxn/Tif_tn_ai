import logging
from datetime import UTC, datetime, timedelta

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.config import settings
from src.db.client import get_db

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("stats"))
async def handle_stats(message: Message) -> None:
    if message.from_user.id != settings.admin_telegram_id:
        return

    db = await get_db()
    today = datetime.now(UTC).date().isoformat()

    total_today = await db.query(
        "SELECT count() FROM query_logs WHERE string::startsWith(string(created_at), $d) GROUP ALL",
        {"d": today},
    )

    avg_ms = await db.query(
        "SELECT math::mean(response_time_ms) AS avg_ms FROM query_logs"
        " WHERE string::startsWith(string(created_at), $d) GROUP ALL",
        {"d": today},
    )

    top_codes = await db.query(
        "SELECT result_code, count() AS cnt FROM query_logs"
        " WHERE string::startsWith(string(created_at), $d)"
        " AND result_code != NONE GROUP BY result_code ORDER BY cnt DESC LIMIT 10",
        {"d": today},
    )

    dau_rows = []
    for i in range(7):
        day = (datetime.now(UTC).date() - timedelta(days=i)).isoformat()
        r = await db.query(
            "SELECT count() FROM daily_usage WHERE date = $d GROUP ALL",
            {"d": day},
        )
        dau_rows.append(f"  {day}: {r[0]['count'] if r else 0} users")

    total = total_today[0]["count"] if total_today else 0
    avg = int(avg_ms[0]["avg_ms"]) if avg_ms and avg_ms[0].get("avg_ms") else 0
    top_str = "\n".join(f"  {r['result_code']}: {r['cnt']}" for r in (top_codes or []))
    dau_str = "\n".join(dau_rows)

    text = (
        f"<b>Stats for {today}</b>\n\n"
        f"Queries today: {total}\n"
        f"Avg response: {avg}ms\n\n"
        f"<b>Top codes:</b>\n{top_str or '—'}\n\n"
        f"<b>DAU (7d):</b>\n{dau_str}"
    )
    await message.answer(text, parse_mode="HTML")
