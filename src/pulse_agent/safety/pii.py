from __future__ import annotations

import re

EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    re.IGNORECASE,
)
# India + generic international phone patterns
PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}\b|"
    r"(?<!\d)\+?\d{1,3}[\s.-]?\(?\d{2,4}\)?[\s.-]?\d{3,4}[\s.-]?\d{3,4}\b"
)

REDACT_EMAIL = "[REDACTED_EMAIL]"
REDACT_PHONE = "[REDACTED_PHONE]"


def scrub_pii(text: str) -> str:
    if not text:
        return text
    out = EMAIL_PATTERN.sub(REDACT_EMAIL, text)
    return PHONE_PATTERN.sub(REDACT_PHONE, out)
