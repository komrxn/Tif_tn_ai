from typing import Protocol


class STTBackend(Protocol):
    async def transcribe(self, audio_bytes: bytes) -> str: ...
