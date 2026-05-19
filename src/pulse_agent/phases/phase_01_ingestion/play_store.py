from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Any

from pulse_agent.models.review import Review, ReviewSource

logger = logging.getLogger(__name__)


def _parse_play_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except ValueError:
            pass
    return date.today()


def parse_play_store_records(records: list[dict[str, Any]]) -> list[Review]:
    """Normalize google-play-scraper or fixture dicts to Review."""
    reviews: list[Review] = []
    for rec in records:
        review_id = rec.get("reviewId") or rec.get("review_id")
        if not review_id:
            continue
        reviews.append(
            Review(
                source=ReviewSource.PLAY_STORE,
                review_id=str(review_id),
                rating=int(rec.get("score") or rec.get("rating") or 0),
                title=str(rec.get("title") or ""),
                body=str(rec.get("content") or rec.get("body") or ""),
                review_date=_parse_play_date(rec.get("at") or rec.get("review_date")),
                author=str(rec.get("userName") or rec.get("author") or "") or None,
                app_version=str(rec.get("appVersion") or rec.get("app_version") or "") or None,
            )
        )
    return reviews


def fetch_play_store_reviews(
    package_name: str,
    *,
    count: int = 200,
    lang: str = "en",
    country: str = "in",
) -> list[Review]:
    """Fetch reviews via google-play-scraper (paginates internally up to count)."""
    try:
        from google_play_scraper import Sort, reviews as gplay_reviews
    except ImportError as exc:
        raise RuntimeError("google-play-scraper is required for Play ingestion") from exc

    result, _continuation = gplay_reviews(
        package_name,
        lang=lang,
        country=country,
        sort=Sort.NEWEST,
        count=count,
    )
    return parse_play_store_records(list(result))
