from aiogram import Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from src.cards import get_cards
from src.db.repo import get_user_history
from src.ui.i18n import Lang, t

router = Router()

_HISTORY_LABELS = {"📜 История", "📜 Tarix", "📜 History"}


@router.message(Command("history"))
@router.message(lambda m: m.text and m.text in _HISTORY_LABELS)
async def handle_history(message: Message, user: dict, lang: Lang) -> None:
    cards = await get_cards(message.chat.id, limit=10)

    if cards:
        buttons = [
            [
                InlineKeyboardButton(
                    text=t(lang, "history_item", code=c["code"], name=c.get("name", "")[:30]),
                    callback_data=f"back:{c['code']}",
                )
            ]
            for c in cards
        ]
    else:
        # Fall back to DB query_logs (no Redis cards yet — first session)
        all_rows = await get_user_history(str(user["id"]), limit=20)
        db_rows = [r for r in all_rows if r.get("result_code")][:10]
        if not db_rows:
            await message.answer(t(lang, "history_empty"))
            return
        buttons = [
            [
                InlineKeyboardButton(
                    text=t(
                        lang,
                        "history_item",
                        code=r["result_code"],
                        name=(r.get("result_name") or r.get("query_text", ""))[:30],
                    ),
                    callback_data=f"back:{r['result_code']}",
                )
            ]
            for r in db_rows
        ]

    await message.answer(
        t(lang, "history_header"), reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
