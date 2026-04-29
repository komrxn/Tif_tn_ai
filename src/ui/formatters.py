import html

from src.ai.llm import ClassifyResult
from src.ui.i18n import Lang, t

_MAX_MSG = 4000
_EXPL_PREVIEW = 800


def _escape(s: str) -> str:
    return html.escape(s)


def format_result(lang: Lang, result: ClassifyResult) -> str:
    if result.code is None:
        return _escape(t(lang, "null_code", justification=result.justification))

    pct = int(result.confidence * 100)
    lines = [
        t(lang, "result_header", code=result.code, name=_escape(result.name)),
        t(lang, "result_confidence", pct=pct),
        "",
        _escape(result.justification),
    ]

    if result.alternative_codes:
        lines.append("")
        lines.append(t(lang, "result_alternatives"))
        for alt in result.alternative_codes:
            lines.append(f"  • <b>{alt.code}</b> — {_escape(alt.reason)}")

    return "\n".join(lines)


def format_duty(lang: Lang, code: str, duty: dict | None) -> str:
    if duty is None:
        return t(lang, "duty_not_found")

    lines = [t(lang, "duty_header", code=code)]

    if lang == "uz":
        lines.append(_escape(duty.get("raw_text_uz", "")))
    else:
        pct = duty.get("duty_pct")
        if pct is not None:
            lines.append(t(lang, "duty_pct", pct=int(pct) if pct == int(pct) else pct))
        if kg := duty.get("min_per_kg_usd"):
            lines.append(t(lang, "duty_floor_kg", val=kg))
        if unit := duty.get("min_per_unit_usd"):
            lines.append(t(lang, "duty_floor_unit", val=unit))
        if liter := duty.get("min_per_liter_usd"):
            lines.append(t(lang, "duty_floor_liter", val=liter))
        lines.append(t(lang, "duty_stub_vat"))

    return "\n".join(lines)


def format_tree(lang: Lang, code: str, ancestors: list[dict]) -> str:
    lines = [t(lang, "tree_header", code=code)]
    for depth, row in enumerate(ancestors):
        prefix = "  " * depth + ("└─ " if depth > 0 else "")
        lines.append(f"{prefix}<b>{row['code']}</b> {_escape(row.get('name_ru', ''))}")
    return "\n".join(lines)


def format_explanation(
    lang: Lang, code: str, chunk: dict | None, full: bool = False
) -> tuple[str, bool]:
    """Return (text, has_more)."""
    if chunk is None:
        return t(lang, "expl_not_found"), False

    header = t(lang, "expl_header", code=code)
    body = chunk.get("text", "")

    if not full and len(body) > _EXPL_PREVIEW:
        return f"{header}\n\n{_escape(body[:_EXPL_PREVIEW])}…", True
    return f"{header}\n\n{_escape(body)}", False


def split_message(text: str) -> list[str]:
    """Split text at paragraph boundary if over 4000 chars."""
    if len(text) <= _MAX_MSG:
        return [text]
    parts = []
    while len(text) > _MAX_MSG:
        cut = text.rfind("\n\n", 0, _MAX_MSG)
        if cut == -1:
            cut = _MAX_MSG
        parts.append(text[:cut])
        text = text[cut:].lstrip()
    if text:
        parts.append(text)
    return parts
