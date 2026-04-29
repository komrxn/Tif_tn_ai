import logging

from aiogram import Bot, Router
from aiogram.types import Message

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

    text = await _whisper.transcribe(audio_bytes.read())
    logger.info("STT result: %s", text[:100])

    await run_query(message, text, user, lang)
