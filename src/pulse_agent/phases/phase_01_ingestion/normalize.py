from __future__ import annotations

from datetime import date, timedelta

from pulse_agent.models.review import IngestStats, Review, ReviewCorpus, ReviewSource
from pulse_agent.phases.phase_01_ingestion.content_filters import filter_reviews_by_content


def dedupe_reviews(reviews: list[Review]) -> list[Review]:
    """Keep first occurrence per (source, review_id)."""
    seen: set[tuple[str, str]] = set()
    out: list[Review] = []
    for r in reviews:
        key = (r.source.value, r.review_id)
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def filter_by_window(
    reviews: list[Review],
    *,
    window_weeks: int,
    reference_date: date | None = None,
) -> list[Review]:
    ref = reference_date or date.today()
    cutoff = ref - timedelta(weeks=window_weeks)
    return [r for r in reviews if r.review_date >= cutoff]


def normalize_corpus(
    app_store: list[Review],
    play_store: list[Review],
    *,
    window_weeks: int,
    reference_date: date | None = None,
    app_store_error: str | None = None,
    play_store_error: str | None = None,
) -> ReviewCorpus:
    combined = list(app_store) + list(play_store)
    stats = IngestStats(
        app_store_fetched=len(app_store),
        play_store_fetched=len(play_store),
        app_store_error=app_store_error,
        play_store_error=play_store_error,
    )
    deduped = dedupe_reviews(combined)
    stats.after_dedupe = len(deduped)
    windowed = filter_by_window(deduped, window_weeks=window_weeks, reference_date=reference_date)
    stats.after_window = len(windowed)

    filtered, content_stats = filter_reviews_by_content(windowed)
    from pulse_agent.safety.corpus import scrub_corpus_reviews

    filtered = scrub_corpus_reviews(filtered)
    stats.after_content_filter = len(filtered)
    stats.content_filter_removals = content_stats.to_dict()

    if filtered:
        dates = [r.review_date for r in filtered]
        stats.date_min = min(dates).isoformat()
        stats.date_max = max(dates).isoformat()

    return ReviewCorpus(reviews=filtered, stats=stats)


def count_by_source(reviews: list[Review]) -> dict[str, int]:
    counts = {ReviewSource.APP_STORE.value: 0, ReviewSource.PLAY_STORE.value: 0}
    for r in reviews:
        counts[r.source.value] = counts.get(r.source.value, 0) + 1
    return counts
