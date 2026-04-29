import json
from pathlib import Path
from typing import Literal

Lang = Literal["uz", "ru", "en"]

_LOCALES_DIR = Path(__file__).parent.parent / "locales"
_strings: dict[str, dict[str, str]] = {}


def _load(lang: str) -> dict[str, str]:
    if lang not in _strings:
        path = _LOCALES_DIR / f"{lang}.json"
        _strings[lang] = json.loads(path.read_text(encoding="utf-8"))
    return _strings[lang]


def t(lang: Lang, key: str, **kwargs: object) -> str:
    strings = _load(lang)
    template = strings.get(key, key)
    return template.format(**kwargs) if kwargs else template
