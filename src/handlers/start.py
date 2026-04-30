from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from src.db.repo import set_user_language
from src.ui.i18n import Lang, t
from src.ui.keyboards import language_keyboard, main_keyboard

router = Router()


@router.message(Command("start"))
async def handle_start(message: Message, user: dict, lang: Lang) -> None:
    is_new = not user.get("last_seen_at") or str(user.get("language")) == "uz"
    if is_new or message.text == "/start":
        await message.answer(
            t(lang, "start_welcome_new"),
            reply_markup=language_keyboard(),
        )
    else:
        await message.answer(
            t(lang, "start_welcome_back"),
            reply_markup=main_keyboard(lang),
            parse_mode="HTML",
        )


_LANGUAGE_LABELS = {"⚙️ Язык", "⚙️ Til", "⚙️ Language"}


@router.message(Command("language"))
@router.message(lambda m: m.text and m.text in _LANGUAGE_LABELS)
async def handle_language_cmd(message: Message, lang: Lang) -> None:
    await message.answer(t(lang, "start_welcome_new"), reply_markup=language_keyboard())


@router.callback_query(lambda c: c.data and c.data.startswith("lang:"))
async def handle_lang_callback(callback: CallbackQuery, user: dict) -> None:
    new_lang: Lang = callback.data.split(":")[1]  # type: ignore[assignment]
    if new_lang not in ("uz", "ru", "en"):
        await callback.answer()
        return

    await set_user_language(str(user["id"]), new_lang)
    await callback.message.edit_text(
        t(new_lang, "lang_set"),
        reply_markup=None,
    )
    await callback.message.answer(
        t(new_lang, "start_welcome_back"),
        reply_markup=main_keyboard(new_lang),
        parse_mode="HTML",
    )
    await callback.answer()
