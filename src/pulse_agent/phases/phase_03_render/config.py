from __future__ import annotations

import os
from dataclasses import dataclass


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


@dataclass(frozen=True)
class RenderLimits:
    email_max_lines: int = 15
    email_max_words: int = 500
    max_actions_per_theme: int = 4
    max_quotes_in_doc: int = 8

    @classmethod
    def from_env(cls) -> RenderLimits:
        return cls(
            email_max_lines=_int_env("PULSE_EMAIL_MAX_LINES", 15),
            email_max_words=_int_env("PULSE_EMAIL_MAX_WORDS", 500),
            max_actions_per_theme=_int_env("PULSE_MAX_ACTIONS_PER_THEME", 4),
            max_quotes_in_doc=_int_env("PULSE_MAX_QUOTES_IN_DOC", 8),
        )
