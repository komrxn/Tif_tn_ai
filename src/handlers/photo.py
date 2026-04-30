import logging
import traceback as tb_module

from aiogram import Bot, Router
from aiogram.types import Message

from src.ai.vision import describe_image
from src.db.repo import log_error
from src.errors import ClassificationError
from src.handlers.query import run_query
from src.ui.i18n import Lang, t

logger = logging.getLogger(__name__)
router = Router()


@router.message(lambda m: m.photo)
async def handle_photo(message: Message, user: dict, lang: Lang, bot: Bot) -> None:
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    image_bytes = await bot.download_file(file.file_path)

    try:
        desc, vision_prompt_tokens, vision_completion_tokens = await describe_image(
            image_bytes.read()
        )
    except Exception as exc:
        logger.error("Vision description failed", exc_info=True)
        await log_error(
            handler="photo",
            error_type=type(exc).__name__,
            message=str(exc),
            traceback=tb_module.format_exc(),
            user_id=str(user["id"]) if user else None,
            query_type="photo",
        )
        await message.answer(t(lang, "unknown_msg"))
        return

    logger.info("Vision description: %s", desc[:100])
    prefix = t(lang, "photo_recognized", desc=desc)

    try:
        await run_query(
            message,
            desc,
            user,
            lang,
            prefix=prefix,
            extra_tokens_prompt=vision_prompt_tokens + vision_completion_tokens,
        )
    except ClassificationError:
        await message.answer(t(lang, "unknown_msg"))
