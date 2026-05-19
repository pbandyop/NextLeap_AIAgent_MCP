from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any


class ReviewSource(str, Enum):
    APP_STORE = "app_store"
    PLAY_STORE = "play_store"


@dataclass
class Review:
    source: ReviewSource
    review_id: str
    rating: int
    title: str
    body: str
    review_date: date
    author: str | None = None
    locale: str | None = None
    app_version: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source.value,
            "review_id": self.review_id,
            "rating": self.rating,
            "title": self.title,
            "body": self.body,
            "review_date": self.review_date.isoformat(),
            "author": self.author,
            "locale": self.locale,
            "app_version": self.app_version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Review:
        return cls(
            source=ReviewSource(data["source"]),
            review_id=data["review_id"],
            rating=int(data["rating"]),
            title=data.get("title") or "",
            body=data.get("body") or "",
            review_date=date.fromisoformat(data["review_date"]),
            author=data.get("author"),
            locale=data.get("locale"),
            app_version=data.get("app_version"),
        )


@dataclass
class IngestStats:
    app_store_fetched: int = 0
    play_store_fetched: int = 0
    after_dedupe: int = 0
    after_window: int = 0
    after_content_filter: int = 0
    content_filter_removals: dict[str, int] = field(default_factory=dict)
    date_min: str | None = None
    date_max: str | None = None
    app_store_error: str | None = None
    play_store_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "app_store_fetched": self.app_store_fetched,
            "play_store_fetched": self.play_store_fetched,
            "after_dedupe": self.after_dedupe,
            "after_window": self.after_window,
            "after_content_filter": self.after_content_filter,
            "content_filter_removals": dict(self.content_filter_removals),
            "date_min": self.date_min,
            "date_max": self.date_max,
            "app_store_error": self.app_store_error,
            "play_store_error": self.play_store_error,
        }

    @property
    def by_source(self) -> dict[str, int]:
        return {
            "app_store": self.after_window if not self.app_store_error else 0,
            "play_store": self.after_window if not self.play_store_error else 0,
        }


@dataclass
class ReviewCorpus:
    reviews: list[Review] = field(default_factory=list)
    stats: IngestStats = field(default_factory=IngestStats)

    def to_dict(self) -> dict[str, Any]:
        return {
            "reviews": [r.to_dict() for r in self.reviews],
            "stats": self.stats.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReviewCorpus:
        raw_stats = data.get("stats") or {}
        stats = IngestStats(
            app_store_fetched=int(raw_stats.get("app_store_fetched", 0)),
            play_store_fetched=int(raw_stats.get("play_store_fetched", 0)),
            after_dedupe=int(raw_stats.get("after_dedupe", 0)),
            after_window=int(raw_stats.get("after_window", 0)),
            after_content_filter=int(raw_stats.get("after_content_filter", 0)),
            content_filter_removals=dict(raw_stats.get("content_filter_removals") or {}),
            date_min=raw_stats.get("date_min"),
            date_max=raw_stats.get("date_max"),
            app_store_error=raw_stats.get("app_store_error"),
            play_store_error=raw_stats.get("play_store_error"),
        )
        return cls(
            reviews=[Review.from_dict(r) for r in data.get("reviews", [])],
            stats=stats,
        )
