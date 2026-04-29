from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.ui.i18n import Lang, t

router = Router()

_HELP_LABELS = {"❓ Помощь", "❓ Yordam", "❓ Help"}


@router.message(Command("help"))
@router.message(lambda m: m.text and m.text in _HELP_LABELS)
async def handle_help(message: Message, lang: Lang) -> None:
    await message.answer(t(lang, "help_text"), parse_mode="HTML")
