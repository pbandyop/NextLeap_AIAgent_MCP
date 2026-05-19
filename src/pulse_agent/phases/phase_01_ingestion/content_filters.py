from __future__ import annotations

import re
from dataclasses import dataclass

from pulse_agent.models.review import Review

# Minimum words required in review text (title + body); "more than 6" => at least 7.
MIN_WORD_COUNT = 7

_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U0001F600-\U0001F64F"
    "\U00002600-\U000027BF"
    "\U0000FE00-\U0000FE0F"
    "\u200d"
    "\ufe0f"
    "]+",
    flags=re.UNICODE,
)
_NON_LATIN_RE = re.compile(r"[^\x00-\x7F]+")


@dataclass
class ContentFilterStats:
    removed_too_few_words: int = 0
    removed_non_english: int = 0
    removed_empty_after_clean: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "removed_too_few_words": self.removed_too_few_words,
            "removed_non_english": self.removed_non_english,
            "removed_empty_after_clean": self.removed_empty_after_clean,
        }


def strip_emojis(text: str) -> str:
    if not text:
        return ""
    cleaned = _EMOJI_RE.sub("", text)
    return re.sub(r"\s+", " ", cleaned).strip()


def combined_review_text(review: Review) -> str:
    parts = [review.title.strip(), review.body.strip()]
    return " ".join(p for p in parts if p)


def word_count(text: str) -> int:
    if not text:
        return 0
    return len([w for w in text.split() if w])


def is_english(text: str) -> bool:
    """Return True if text is English (langdetect with Latin-script fallback)."""
    text = text.strip()
    if not text:
        return False

    if _NON_LATIN_RE.search(text):
        try:
            from langdetect import LangDetectException, detect

            lang = detect(text)
            return lang == "en"
        except Exception:
            return False

    try:
        from langdetect import LangDetectException, detect

        return detect(text) == "en"
    except Exception:
        # Short or ambiguous: allow basic Latin reviews without non-Latin scripts
        return word_count(text) >= MIN_WORD_COUNT


def clean_review(review: Review) -> Review:
    return Review(
        source=review.source,
        review_id=review.review_id,
        rating=review.rating,
        title=strip_emojis(review.title),
        body=strip_emojis(review.body),
        review_date=review.review_date,
        author=review.author,
        locale=review.locale,
        app_version=review.app_version,
    )


def passes_content_rules(review: Review) -> tuple[bool, str]:
    """
    Apply word-count and English rules on emoji-stripped text.
    Returns (ok, reason_if_rejected).
    """
    text = combined_review_text(review)
    if not text:
        return False, "empty_after_clean"

    if word_count(text) < MIN_WORD_COUNT:
        return False, "too_few_words"

    if not is_english(text):
        return False, "non_english"

    return True, ""


def filter_reviews_by_content(reviews: list[Review]) -> tuple[list[Review], ContentFilterStats]:
    """Strip emojis, keep English reviews with more than six words."""
    stats = ContentFilterStats()
    kept: list[Review] = []

    for raw in reviews:
        cleaned = clean_review(raw)
        ok, reason = passes_content_rules(cleaned)
        if ok:
            kept.append(cleaned)
            continue
        if reason == "too_few_words":
            stats.removed_too_few_words += 1
        elif reason == "non_english":
            stats.removed_non_english += 1
        else:
            stats.removed_empty_after_clean += 1

    return kept, stats
