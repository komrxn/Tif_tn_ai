import io

from openai import AsyncOpenAI

from src.config import settings


class WhisperSTT:
    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=30.0)

    async def transcribe(self, audio_bytes: bytes) -> str:
        resp = await self._client.audio.transcriptions.create(
            model="whisper-1",
            file=("audio.ogg", io.BytesIO(audio_bytes), "audio/ogg"),
        )
        return resp.text
