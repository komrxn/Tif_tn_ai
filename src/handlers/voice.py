import logging
import traceback as tb_module

from aiogram import Bot, Router
from aiogram.types import Message

from src.db.repo import log_error
from src.errors import ClassificationError
from src.handlers.query import run_query
from src.stt.openai_whisper import WhisperSTT
from src.ui.i18n import Lang, t

logger = logging.getLogger(__name__)
router = Router()

_whisper = WhisperSTT()


@router.message(lambda m: m.voice)
async def handle_voice(message: Message, user: dict, lang: Lang, bot: Bot) -> None:
    if lang == "uz":
        await message.answer(t(lang, "voice_uz_stub"))
        return

    file = await bot.get_file(message.voice.file_id)
    audio_bytes = await bot.download_file(file.file_path)
    audio_seconds = float(message.voice.duration)

    try:
        text = await _whisper.transcribe(audio_bytes.read())
    except Exception as exc:
        logger.error("STT transcription failed", exc_info=True)
        await log_error(
            handler="voice",
            error_type=type(exc).__name__,
            message=str(exc),
            traceback=tb_module.format_exc(),
            user_id=str(user["id"]) if user else None,
            query_type="voice",
        )
        await message.answer(t(lang, "unknown_msg"))
        return

    logger.info("STT result: %s", text[:100])

    try:
        await run_query(message, text, user, lang, audio_seconds=audio_seconds)
    except ClassificationError:
        await message.answer(t(lang, "unknown_msg"))
