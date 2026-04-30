from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth import get_current_admin
from app.db import get_db
from app.pricing import GPT51_INPUT_PER_M, GPT51_OUTPUT_PER_M, WHISPER_PER_MIN

router = APIRouter(prefix="/api/usage", tags=["usage"])


class TrafficPoint(BaseModel):
    date: str
    count: int


class TrafficResponse(BaseModel):
    data: list[TrafficPoint]


class CostBreakdown(BaseModel):
    gpt51_input_usd: float
    gpt51_output_usd: float
    whisper_usd: float
    total_usd: float


class DailyCost(BaseModel):
    date: str
    total_usd: float


class CostResponse(BaseModel):
    total_usd: float
    breakdown: CostBreakdown
    by_day: list[DailyCost]


def _calc_cost(
    tokens_prompt: float,
    tokens_completion: float,
    audio_seconds: float,
) -> CostBreakdown:
    gpt_in = tokens_prompt * GPT51_INPUT_PER_M / 1_000_000
    gpt_out = tokens_completion * GPT51_OUTPUT_PER_M / 1_000_000
    whisper = audio_seconds / 60 * WHISPER_PER_MIN
    return CostBreakdown(
        gpt51_input_usd=round(gpt_in, 6),
        gpt51_output_usd=round(gpt_out, 6),
        whisper_usd=round(whisper, 6),
        total_usd=round(gpt_in + gpt_out + whisper, 6),
    )


@router.get("/traffic", response_model=TrafficResponse)
async def get_traffic(
    days: int = 30,
    _: str = Depends(get_current_admin),
) -> TrafficResponse:
    db = await get_db()
    rows = await db.query(
        """
        SELECT
            string::slice(string(created_at), 0, 10) AS date,
            count() AS count
        FROM query_logs
        WHERE created_at > time::now() - type::duration(string($days) + 'd')
        GROUP BY date
        ORDER BY date ASC
        """,
        {"days": days},
    )
    data = [TrafficPoint(date=r["date"], count=r["count"]) for r in (rows or [])]
    return TrafficResponse(data=data)


@router.get("/costs", response_model=CostResponse)
async def get_costs(
    days: int = 30,
    _: str = Depends(get_current_admin),
) -> CostResponse:
    db = await get_db()
    rows = await db.query(
        """
        SELECT
            string::slice(string(created_at), 0, 10) AS date,
            math::sum(tokens_prompt ?? 0)     AS prompt_tokens,
            math::sum(tokens_completion ?? 0) AS completion_tokens,
            math::sum(audio_seconds ?? 0)     AS audio_secs
        FROM query_logs
        WHERE created_at > time::now() - type::duration(string($days) + 'd')
        GROUP BY date
        ORDER BY date ASC
        """,
        {"days": days},
    )

    total_prompt = sum(r["prompt_tokens"] for r in (rows or []))
    total_completion = sum(r["completion_tokens"] for r in (rows or []))
    total_audio = sum(r["audio_secs"] for r in (rows or []))

    breakdown = _calc_cost(total_prompt, total_completion, total_audio)

    by_day = [
        DailyCost(
            date=r["date"],
            total_usd=_calc_cost(
                r["prompt_tokens"], r["completion_tokens"], r["audio_secs"]
            ).total_usd,
        )
        for r in (rows or [])
    ]

    return CostResponse(
        total_usd=breakdown.total_usd,
        breakdown=breakdown,
        by_day=by_day,
    )
