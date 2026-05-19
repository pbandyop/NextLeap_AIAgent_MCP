from datetime import date

from pulse_agent.models.report import ValidatedQuote
from pulse_agent.models.review import Review, ReviewSource
from pulse_agent.phases.phase_02_analysis.quotes import (
    quote_exists_in_review,
    select_quote_for_cluster,
    validate_report_quotes,
)


def test_quote_must_be_substring():
    review = Review(
        source=ReviewSource.PLAY_STORE,
        review_id="x1",
        rating=1,
        title="Bad",
        body="The login screen freezes every time I open the app.",
        review_date=date(2026, 5, 1),
    )
    assert quote_exists_in_review("login screen freezes", review)
    assert not quote_exists_in_review("hallucinated quote text", review)


def test_rejects_hallucinated_quote_in_report():
    review = Review(
        source=ReviewSource.PLAY_STORE,
        review_id="x1",
        rating=1,
        title="Bad",
        body="The login screen freezes every time I open the app.",
        review_date=date(2026, 5, 1),
    )
    quotes = [
        ValidatedQuote(
            text="completely made up",
            source_review_id="x1",
            cluster_id="critical_0",
            rating=1,
            source="play_store",
        )
    ]
    errors = validate_report_quotes(quotes, {"x1": review})
    assert errors


def test_select_quote_from_cluster():
    review = Review(
        source=ReviewSource.PLAY_STORE,
        review_id="x1",
        rating=1,
        title="Fees",
        body="Hidden charges on every trade make this app expensive for small investors.",
        review_date=date(2026, 5, 1),
    )
    quotes = select_quote_for_cluster([review], "critical_0")
    assert len(quotes) == 1
    assert quote_exists_in_review(quotes[0].text, review)
