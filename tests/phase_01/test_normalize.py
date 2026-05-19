from datetime import date

from pulse_agent.models.review import Review, ReviewSource
from pulse_agent.phases.phase_01_ingestion.content_filters import (
    clean_review,
    filter_reviews_by_content,
    strip_emojis,
    word_count,
)
from pulse_agent.phases.phase_01_ingestion.normalize import (
    dedupe_reviews,
    filter_by_window,
    normalize_corpus,
)


def _review(
    rid: str,
    source: ReviewSource,
    day: str,
    *,
    title: str = "",
    body: str = "",
) -> Review:
    return Review(
        source=source,
        review_id=rid,
        rating=4,
        title=title,
        body=body,
        review_date=date.fromisoformat(day),
    )


def test_dedupe_by_review_id():
    reviews = [
        _review("a1", ReviewSource.APP_STORE, "2026-04-01", body="one two three four five six seven"),
        _review("a1", ReviewSource.APP_STORE, "2026-04-02", body="one two three four five six seven"),
        _review("p1", ReviewSource.PLAY_STORE, "2026-04-01", body="one two three four five six seven"),
    ]
    assert len(dedupe_reviews(reviews)) == 2


def test_filter_by_window():
    ref = date(2026, 5, 16)
    reviews = [
        _review("old", ReviewSource.APP_STORE, "2025-01-01", body="one two three four five six seven"),
        _review("new", ReviewSource.APP_STORE, "2026-05-01", body="one two three four five six seven"),
    ]
    filtered = filter_by_window(reviews, window_weeks=10, reference_date=ref)
    assert len(filtered) == 1
    assert filtered[0].review_id == "new"


def test_strip_emojis():
    assert strip_emojis("good 👍😊 app") == "good app"


def test_remove_too_few_words():
    reviews = [
        _review("short", ReviewSource.PLAY_STORE, "2026-05-01", body="good app"),
        _review(
            "long",
            ReviewSource.PLAY_STORE,
            "2026-05-01",
            body="this is a sufficiently long english review text",
        ),
    ]
    kept, stats = filter_reviews_by_content(reviews)
    assert len(kept) == 1
    assert kept[0].review_id == "long"
    assert stats.removed_too_few_words == 1


def test_remove_non_english():
    reviews = [
        _review(
            "hi",
            ReviewSource.PLAY_STORE,
            "2026-05-01",
            body="यह एक हिंदी समीक्षा है जो काफी लंबी है और पर्याप्त शब्दों वाली है",
        ),
        _review(
            "en",
            ReviewSource.PLAY_STORE,
            "2026-05-01",
            body="this is an english review with enough words to pass the filter",
        ),
    ]
    kept, stats = filter_reviews_by_content(reviews)
    assert len(kept) == 1
    assert kept[0].review_id == "en"
    assert stats.removed_non_english >= 1


def test_emoji_stripped_in_output():
    raw = _review(
        "e1",
        ReviewSource.PLAY_STORE,
        "2026-05-01",
        body="great trading experience overall very smooth and reliable 👍😊",
    )
    cleaned = clean_review(raw)
    assert "👍" not in cleaned.body
    assert word_count(cleaned.body) >= 7


def test_normalize_corpus_stats():
    body = "one two three four five six seven eight"
    app = [_review("a1", ReviewSource.APP_STORE, "2026-04-01", body=body)]
    play = [_review("p1", ReviewSource.PLAY_STORE, "2026-04-02", body=body)]
    corpus = normalize_corpus(
        app,
        play,
        window_weeks=12,
        reference_date=date(2026, 5, 16),
    )
    assert corpus.stats.after_dedupe == 2
    assert corpus.stats.after_window == 2
    assert corpus.stats.after_content_filter == 2
