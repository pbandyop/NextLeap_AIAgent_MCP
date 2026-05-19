from __future__ import annotations

from pulse_agent.models.report import ValidatedQuote
from pulse_agent.models.review import Review
from pulse_agent.phases.phase_01_ingestion.content_filters import combined_review_text
from pulse_agent.phases.phase_02_analysis.sampling import _review_sort_key


def quote_exists_in_review(quote: str, review: Review) -> bool:
    if not quote or not quote.strip():
        return False
    source = combined_review_text(review)
    return quote in source or quote.strip() in source


def select_quote_for_cluster(
    reviews: list[Review],
    cluster_id: str,
    *,
    max_quotes: int = 1,
) -> list[ValidatedQuote]:
    ordered = sorted(reviews, key=_review_sort_key)
    quotes: list[ValidatedQuote] = []
    for review in ordered:
        text = combined_review_text(review).strip()
        if not text:
            continue
        candidate = text if len(text) <= 280 else text[:280].rsplit(" ", 1)[0]
        if not quote_exists_in_review(candidate, review):
            continue
        quotes.append(
            ValidatedQuote(
                text=candidate,
                source_review_id=review.review_id,
                cluster_id=cluster_id,
                rating=review.rating,
                source=review.source.value,
            )
        )
        if len(quotes) >= max_quotes:
            break
    return quotes


def validate_report_quotes(
    quotes: list[ValidatedQuote], reviews_by_id: dict[str, Review]
) -> list[str]:
    errors: list[str] = []
    for quote in quotes:
        review = reviews_by_id.get(quote.source_review_id)
        if review is None:
            errors.append(f"unknown review_id {quote.source_review_id}")
            continue
        if not quote_exists_in_review(quote.text, review):
            errors.append(f"quote not substring of review {quote.source_review_id}")
    return errors
