import asyncio
import logging

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth import get_current_admin
from app.config import settings
from app.db import get_db

router = APIRouter(prefix="/api/broadcast", tags=["broadcast"])
logger = logging.getLogger(__name__)

_broadcast_lock = asyncio.Lock()


class BroadcastRequest(BaseModel):
    text: str
    parse_mode: str | None = None


class BroadcastResponse(BaseModel):
    queued: int


async def _send_all(chat_ids: list[int], text: str, parse_mode: str | None) -> None:
    sem = asyncio.Semaphore(10)
    bot_url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"

    async def send_one(chat_id: int) -> None:
        async with sem:
            payload: dict = {"chat_id": chat_id, "text": text}
            if parse_mode:
                payload["parse_mode"] = parse_mode
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    await client.post(bot_url, json=payload)
            except Exception as exc:
                logger.warning("Broadcast failed for %s: %s", chat_id, exc)
            await asyncio.sleep(0.04)

    await asyncio.gather(*[send_one(cid) for cid in chat_ids])
    _broadcast_lock.release()
    logger.info("Broadcast done: %d messages", len(chat_ids))


@router.post("", response_model=BroadcastResponse, status_code=status.HTTP_202_ACCEPTED)
async def broadcast(
    body: BroadcastRequest,
    background: BackgroundTasks,
    _: str = Depends(get_current_admin),
) -> BroadcastResponse:
    if not body.text.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Empty text")

    acquired = _broadcast_lock.locked()
    if acquired:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Another broadcast is already in progress",
        )

    db = await get_db()
    rows = await db.query("SELECT telegram_id FROM users WHERE is_blocked = false OR is_blocked = NONE")
    chat_ids = [r["telegram_id"] for r in (rows or []) if r.get("telegram_id")]

    await _broadcast_lock.acquire()
    background.add_task(_send_all, chat_ids, body.text, body.parse_mode)
    return BroadcastResponse(queued=len(chat_ids))
