import asyncio
import contextlib
import logging
import time

from aiogram import Router
from aiogram.types import Message

from src.ai.context import get_history, push_turn
from src.ai.llm import classify
from src.cards import save_card
from src.db.repo import increment_daily_usage, log_query
from src.errors import ClassificationError
from src.rag.prompts import build_context
from src.rag.retriever import retrieve
from src.session import clear_session, get_session, set_session
from src.ui.formatters import format_result, split_message
from src.ui.i18n import Lang, t
from src.ui.keyboards import main_keyboard, result_keyboard, skip_keyboard

logger = logging.getLogger(__name__)
router = Router()

_SEARCH_LABELS = {"🔍 Поиск", "🔍 Qidiruv", "🔍 Search"}
_MAX_QUESTIONS = 5


async def _typing_loop(bot, chat_id: int, stop: asyncio.Event) -> None:
    while not stop.is_set():
        with contextlib.suppress(Exception):
            await bot.send_chat_action(chat_id, "typing")
        await asyncio.sleep(4)


async def _do_classify(
    message: Message,
    user_msg: str,
    lang: Lang,
    history: list[tuple[str, str | None, str]],
) -> tuple:
    """Run retrieve + classify, return (result, elapsed_ms)."""
    hits = await retrieve(user_msg, top_k=8)
    context = await build_context(hits)
    t0 = time.monotonic()
    result = await classify(user_msg, context, lang, history=history)
    elapsed_ms = int((time.monotonic() - t0) * 1000)
    return result, elapsed_ms


async def run_query(message: Message, query: str, user: dict, lang: Lang, prefix: str = "") -> None:
    chat_id = message.chat.id
    session = await get_session(chat_id)

    if session and session.get("state") == "clarifying":
        # User's message is the answer to the last question
        answer = query
        accumulated = session["accumulated"]
        last_question = session["last_question"]
        original_query = session["original_query"]
        question_count = session["question_count"]

        accumulated = f"{accumulated}\nQ: {last_question}\nA: {answer}"
        full_user_msg = f"{original_query}\n\n{accumulated}"
    else:
        original_query = query
        accumulated = ""
        full_user_msg = query
        question_count = 0

    placeholder = await message.answer(t(lang, "analyzing"))
    stop = asyncio.Event()
    typing_task = asyncio.create_task(_typing_loop(message.bot, chat_id, stop))

    try:
        history = await get_history(chat_id)
        result, elapsed_ms = await _do_classify(message, full_user_msg, lang, history)
    except Exception as exc:
        stop.set()
        typing_task.cancel()
        logger.error("Classification failed", exc_info=True)
        raise ClassificationError(str(exc)) from exc
    finally:
        stop.set()
        typing_task.cancel()

    should_ask = (
        result.next_question is not None
        and question_count < _MAX_QUESTIONS
        and not (result.code and result.confidence >= 0.85)
    )

    if result.code and result.confidence >= 0.7 and not should_ask:
        body = prefix + format_result(lang, result)
        parts = split_message(body)
        await placeholder.edit_text(
            parts[0], parse_mode="HTML", reply_markup=result_keyboard(lang, result.code)
        )
        for part in parts[1:]:
            await message.answer(part, parse_mode="HTML")
        await save_card(
            chat_id,
            result.code,
            result.name,
            result.justification,
            result.confidence,
            [a.model_dump() for a in result.alternative_codes],
            original_query,
        )
        await push_turn(chat_id, original_query, result.code, result.name)
        await clear_session(chat_id)
        await log_query(
            user_id=str(user["id"]),
            query_text=original_query,
            query_type="text",
            result_code=result.code,
            result_name=result.name,
            confidence=result.confidence,
            response_time_ms=elapsed_ms,
        )

    elif should_ask:
        question_count += 1
        await set_session(
            chat_id,
            {
                "state": "clarifying",
                "original_query": original_query,
                "accumulated": accumulated,
                "last_question": result.next_question,
                "question_count": question_count,
            },
        )
        await placeholder.edit_text(
            f"❓ {result.next_question}",
            reply_markup=skip_keyboard(lang),
        )

    else:
        # No code and no question — give up
        if result.code:
            body = prefix + format_result(lang, result)
            await placeholder.edit_text(
                body, parse_mode="HTML", reply_markup=result_keyboard(lang, result.code)
            )
            await save_card(
                chat_id,
                result.code,
                result.name,
                result.justification,
                result.confidence,
                [a.model_dump() for a in result.alternative_codes],
                original_query,
            )
        else:
            await placeholder.delete()
            await message.answer(t(lang, "unknown_msg"), reply_markup=main_keyboard(lang))
        await push_turn(chat_id, original_query, result.code, result.name if result.code else "")
        await clear_session(chat_id)
        await log_query(
            user_id=str(user["id"]),
            query_text=original_query,
            query_type="text",
            result_code=result.code,
            result_name=result.name if result.code else None,
            confidence=result.confidence,
            response_time_ms=elapsed_ms,
        )

    await increment_daily_usage(str(user["id"]))


@router.message(lambda m: m.text and m.text not in _SEARCH_LABELS and not m.text.startswith("/"))
async def handle_text_query(message: Message, user: dict, lang: Lang) -> None:
    query = message.text.strip()
    if not query:
        return
    try:
        await run_query(message, query, user, lang)
    except ClassificationError:
        await message.answer(t(lang, "unknown_msg"))
