from aiogram import Router
from aiogram.types import Message

from src.ui.i18n import Lang, t

router = Router()


@router.message()
async def handle_unknown(message: Message, lang: Lang) -> None:
    await message.answer(t(lang, "unknown_msg"))
