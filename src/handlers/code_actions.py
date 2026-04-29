import logging

from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardButton

from src.ai.llm import AlternativeCode, ClassifyResult, list_examples
from src.cards import get_card
from src.db.repo import get_code_ancestors, get_top_chunk_for_code, lookup_code, lookup_duty
from src.session import clear_session, get_session
from src.ui.formatters import (
    format_duty,
    format_explanation,
    format_result,
    format_tree,
    split_message,
)
from src.ui.i18n import Lang, t
from src.ui.keyboards import back_keyboard, result_keyboard

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(lambda c: c.data and c.data.startswith("duties:"))
async def handle_duties(callback: CallbackQuery, user: dict, lang: Lang) -> None:
    code = callback.data.split(":", 1)[1]
    duty = await lookup_duty(code)
    text = format_duty(lang, code, duty)
    for part in split_message(text):
        await callback.message.edit_text(
            part, parse_mode="HTML", reply_markup=back_keyboard(lang, code)
        )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("tree:"))
async def handle_tree(callback: CallbackQuery, user: dict, lang: Lang) -> None:
    code = callback.data.split(":", 1)[1]
    ancestors = await get_code_ancestors(code)
    if not ancestors:
        logger.warning("No ancestors found for code %s", code)
    text = format_tree(lang, code, ancestors)
    await callback.message.edit_text(
        text, parse_mode="HTML", reply_markup=back_keyboard(lang, code)
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("expl:"))
async def handle_explanation(callback: CallbackQuery, user: dict, lang: Lang) -> None:
    code = callback.data.split(":", 1)[1]
    chunk = await get_top_chunk_for_code(code)
    text, has_more = format_explanation(lang, code, chunk, full=False)
    kb = back_keyboard(lang, code)
    if has_more:
        expand_btn = InlineKeyboardButton(
            text=t(lang, "expl_expand"), callback_data=f"expl_full:{code}"
        )
        kb.inline_keyboard.insert(0, [expand_btn])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("expl_full:"))
async def handle_explanation_full(callback: CallbackQuery, user: dict, lang: Lang) -> None:
    code = callback.data.split(":", 1)[1]
    chunk = await get_top_chunk_for_code(code)
    text, _ = format_explanation(lang, code, chunk, full=True)
    for part in split_message(text):
        await callback.message.edit_text(
            part, parse_mode="HTML", reply_markup=back_keyboard(lang, code)
        )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("examples:"))
async def handle_examples(callback: CallbackQuery, user: dict, lang: Lang) -> None:
    code = callback.data.split(":", 1)[1]
    await callback.message.edit_text(t(lang, "analyzing"), reply_markup=None)
    row = await lookup_code(code)
    name = row.get("name_ru", "") if row else ""
    chunk = await get_top_chunk_for_code(code)
    chunk_text = chunk.get("text") if chunk else None
    examples = await list_examples(code, name, chunk_text, lang)
    header = t(lang, "examples_header", code=code)
    await callback.message.edit_text(
        f"{header}\n\n{examples}",
        parse_mode="HTML",
        reply_markup=back_keyboard(lang, code),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "skip_clarify")
async def handle_skip_clarify(callback: CallbackQuery, user: dict, lang: Lang) -> None:
    chat_id = callback.message.chat.id
    session = await get_session(chat_id)
    await clear_session(chat_id)

    if session and session.get("original_query"):
        from src.handlers.query import run_query

        await callback.message.edit_reply_markup(reply_markup=None)
        await run_query(callback.message, session["original_query"], user, lang)
    else:
        await callback.message.edit_text(t(lang, "unknown_msg"), reply_markup=None)

    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("back:"))
async def handle_back(callback: CallbackQuery, user: dict, lang: Lang) -> None:
    code = callback.data.split(":", 1)[1]
    card = await get_card(callback.message.chat.id, code)
    if card:
        result = ClassifyResult(
            code=card["code"],
            name=card["name"],
            justification=card["justification"],
            confidence=card["confidence"],
            next_question=None,
            alternative_codes=[AlternativeCode(**a) for a in card.get("alternative_codes", [])],
        )
    else:
        logger.warning("No stored card for %s, falling back to DB lookup", code)
        row = await lookup_code(code)
        result = ClassifyResult(
            code=code,
            name=row.get("name_ru", "") if row else "",
            justification="",
            confidence=1.0,
            next_question=None,
            alternative_codes=[],
        )
    await callback.message.edit_text(
        format_result(lang, result),
        parse_mode="HTML",
        reply_markup=result_keyboard(lang, code),
    )
    await callback.answer()
