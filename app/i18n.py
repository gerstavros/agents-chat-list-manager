from __future__ import annotations

import json
from pathlib import Path

LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"
DEFAULT_LANG = "en"

_translations: dict[str, str] = {}
_current_lang = DEFAULT_LANG


def available_locales() -> list[str]:
    if not LOCALES_DIR.exists():
        return [DEFAULT_LANG]
    return sorted(p.stem for p in LOCALES_DIR.glob("*.json"))


def load_locale(lang: str = DEFAULT_LANG) -> None:
    global _translations, _current_lang
    path = LOCALES_DIR / f"{lang}.json"
    if not path.exists():
        lang = DEFAULT_LANG
        path = LOCALES_DIR / f"{DEFAULT_LANG}.json"
    try:
        _translations = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        _translations = {}
    _current_lang = lang


def current_locale() -> str:
    return _current_lang


def _(key: str, **kwargs) -> str:
    text = _translations.get(key, key)
    return text.format(**kwargs) if kwargs else text
