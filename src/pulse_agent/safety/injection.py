from __future__ import annotations

import re

# Patterns that often appear in prompt-injection attempts in user reviews.
_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
        r"disregard\s+(the\s+)?(above|system)\s+",
        r"you\s+are\s+now\s+",
        r"<\s*/?\s*system\s*>",
        r"```\s*system",
        r"\bact\s+as\s+(a\s+)?(?:chatgpt|assistant|admin)\b",
        r"\bdo\s+not\s+follow\b",
    )
]

_DATA_BOUNDARY_START = "<<<USER_REVIEW_DATA>>>"
_DATA_BOUNDARY_END = "<<<END_USER_REVIEW_DATA>>>"


def neutralize_injection_markers(text: str) -> str:
    """Strip common injection phrases; reviews remain data, not instructions."""
    out = text
    for pattern in _INJECTION_PATTERNS:
        out = pattern.sub("[filtered]", out)
    return out


def sanitize_review_text(text: str) -> str:
    return neutralize_injection_markers(text)


def wrap_review_excerpt_for_llm(excerpt: str) -> str:
    """Delimit user content so the model treats it as quoted data."""
    cleaned = sanitize_review_text(excerpt)
    return f"{_DATA_BOUNDARY_START}\n{cleaned}\n{_DATA_BOUNDARY_END}"
