import logging

from aiogram import Bot, Router
from aiogram.types import Message

from src.ai.vision import describe_image
from src.handlers.query import run_query
from src.ui.i18n import Lang, t

logger = logging.getLogger(__name__)
router = Router()


@router.message(lambda m: m.photo)
async def handle_photo(message: Message, user: dict, lang: Lang, bot: Bot) -> None:
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    image_bytes = await bot.download_file(file.file_path)

    desc = await describe_image(image_bytes.read())
    logger.info("Vision description: %s", desc[:100])

    prefix = t(lang, "photo_recognized", desc=desc)
    await run_query(message, desc, user, lang, prefix=prefix)
