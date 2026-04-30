import logging

from openai import AsyncOpenAI

from src.config import settings

logger = logging.getLogger(__name__)

_MODEL = "gpt-5.1"

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=60.0)
    return _client


async def describe_image(image_bytes: bytes, mime: str = "image/jpeg") -> str:
    """Return a Russian product description from an image."""
    import base64

    b64 = base64.b64encode(image_bytes).decode()
    resp = await _get_client().chat.completions.create(
        model=_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{b64}"},
                    },
                    {
                        "type": "text",
                        "text": (
                            "Опиши товар на этом изображении на русском языке. "
                            "Укажи тип товара, материал, назначение и любые другие "
                            "характеристики, видимые на изображении. "
                            "Только описание, без вступительных фраз."
                        ),
                    },
                ],
            }
        ],
        max_tokens=300,
    )
    usage = resp.usage
    prompt_tokens = usage.prompt_tokens if usage else 0
    completion_tokens = usage.completion_tokens if usage else 0
    return resp.choices[0].message.content or "", prompt_tokens, completion_tokens
