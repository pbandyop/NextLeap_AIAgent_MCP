from __future__ import annotations

from pulse_agent.models.review import Review


def split_by_sentiment(reviews: list[Review]) -> tuple[list[Review], list[Review]]:
    """Positive = 4–5★, critical = 1–3★."""
    positive: list[Review] = []
    critical: list[Review] = []
    for review in reviews:
        if review.rating >= 4:
            positive.append(review)
        else:
            critical.append(review)
    return positive, critical
