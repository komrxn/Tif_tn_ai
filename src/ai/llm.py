import json
import logging
from pathlib import Path
from typing import Literal

from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from src.config import settings

logger = logging.getLogger(__name__)

_MODEL = "gpt-5.1"
_SYSTEM_TPL = (Path(__file__).parent.parent / "prompts" / "system_base.md").read_text(
    encoding="utf-8"
)
_OUTPUT_SCHEMA = json.loads(
    (Path(__file__).parent.parent / "prompts" / "output_schema.json").read_text(encoding="utf-8")
)
_RULES_TEXT: str | None = None

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=60.0)
    return _client


def _get_rules() -> str:
    global _RULES_TEXT
    if _RULES_TEXT is None:
        rules_path = Path(__file__).parent.parent.parent / "data" / "build" / "rules.txt"
        _RULES_TEXT = rules_path.read_text(encoding="utf-8")
    return _RULES_TEXT


def _build_system(language: str) -> str:
    return _SYSTEM_TPL.replace("{{language}}", language).replace("{{rules_block}}", _get_rules())


class AlternativeCode(BaseModel):
    code: str
    reason: str


class ClassifyResult(BaseModel):
    code: str | None = Field(pattern=r"^\d{10}$", default=None)
    name: str
    justification: str
    confidence: float = Field(ge=0.0, le=1.0)
    next_question: str | None = None
    alternative_codes: list[AlternativeCode] = Field(default_factory=list, max_length=3)


async def classify(
    query: str,
    context: str,
    language: Literal["uz", "ru", "en"],
    history: list[tuple[str, str | None, str]] | None = None,
) -> ClassifyResult:
    system_msg = _build_system(language)
    user_msg = f"Product description: {query}\n\n=== CONTEXT ===\n{context}"

    messages: list[dict] = [{"role": "system", "content": system_msg}]
    for prev_query, prev_code, prev_name in history or []:
        messages.append({"role": "user", "content": f"Product description: {prev_query}"})
        if prev_code:
            label = f"{prev_code} — {prev_name}" if prev_name else prev_code
            messages.append({"role": "assistant", "content": f"Classified as: {label}"})
        else:
            messages.append({"role": "assistant", "content": "Could not classify"})
    messages.append({"role": "user", "content": user_msg})

    resp = await _get_client().chat.completions.create(
        model=_MODEL,
        messages=messages,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "classify_result",
                "strict": True,
                "schema": _OUTPUT_SCHEMA,
            },
        },
        temperature=0.0,
    )

    raw = resp.choices[0].message.content
    logger.debug("LLM raw: %s", raw[:200])
    usage = resp.usage
    prompt_tokens = usage.prompt_tokens if usage else 0
    completion_tokens = usage.completion_tokens if usage else 0
    return ClassifyResult.model_validate_json(raw), prompt_tokens, completion_tokens


_EXAMPLES_SYSTEM = (
    "You are a TN VED customs expert. List 5-7 specific, real-world goods "
    "that are classified under the given TN VED code. "
    "Use plain trade terminology, no jargon, no explanations. "
    "Return a numbered list only — no preamble, no trailing text. "
    "Respond in language: {lang}."
)


async def list_examples(
    code: str,
    name: str,
    chunk_text: str | None,
    lang: Literal["uz", "ru", "en"],
) -> str:
    notes = chunk_text[:600] if chunk_text else "Not available"
    user_msg = f"Code: {code} — {name}\n\nExplanatory notes:\n{notes}"
    resp = await _get_client().chat.completions.create(
        model=_MODEL,
        messages=[
            {"role": "system", "content": _EXAMPLES_SYSTEM.format(lang=lang)},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.0,
    )
    return resp.choices[0].message.content or ""
