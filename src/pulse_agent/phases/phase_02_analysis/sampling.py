from __future__ import annotations

from pulse_agent.models.review import Review
from pulse_agent.phases.phase_01_ingestion.content_filters import combined_review_text, word_count


def truncate_words(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words])


def excerpt_for_review(review: Review, max_words: int) -> str:
    text = combined_review_text(review)
    return truncate_words(text, max_words)


def _review_sort_key(review: Review) -> tuple:
    # Lower rating first (1–2★), then longer text for exemplars.
    low_rating = 0 if review.rating <= 2 else 1
    return (low_rating, review.rating, -word_count(combined_review_text(review)))


def select_exemplars(
    reviews: list[Review],
    *,
    max_count: int,
    max_words_per_excerpt: int,
) -> list[tuple[Review, str]]:
    """Oversample low ratings by sorting them first."""
    ordered = sorted(reviews, key=_review_sort_key)
    picked: list[tuple[Review, str]] = []
    for review in ordered[:max_count]:
        picked.append((review, excerpt_for_review(review, max_words_per_excerpt)))
    return picked


def estimate_tokens(text: str) -> int:
    return max(1, int(len(text.split()) * 1.35))
