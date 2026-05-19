from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Theme:
    cluster_id: str
    label: str
    summary: str
    sentiment: str  # "positive" | "critical"
    review_count: int
    actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "label": self.label,
            "summary": self.summary,
            "sentiment": self.sentiment,
            "review_count": self.review_count,
            "actions": list(self.actions),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Theme:
        return cls(
            cluster_id=str(data["cluster_id"]),
            label=str(data["label"]),
            summary=str(data["summary"]),
            sentiment=str(data["sentiment"]),
            review_count=int(data["review_count"]),
            actions=list(data.get("actions") or []),
        )


@dataclass
class ValidatedQuote:
    text: str
    source_review_id: str
    cluster_id: str
    rating: int
    source: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "source_review_id": self.source_review_id,
            "cluster_id": self.cluster_id,
            "rating": self.rating,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ValidatedQuote:
        return cls(
            text=str(data["text"]),
            source_review_id=str(data["source_review_id"]),
            cluster_id=str(data["cluster_id"]),
            rating=int(data["rating"]),
            source=str(data["source"]),
        )


@dataclass
class AnalysisStats:
    groq_requests: int = 0
    groq_tokens_estimated: int = 0
    clustering_method: str = ""
    positive_review_count: int = 0
    critical_review_count: int = 0
    theme_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "groq_requests": self.groq_requests,
            "groq_tokens_estimated": self.groq_tokens_estimated,
            "clustering_method": self.clustering_method,
            "positive_review_count": self.positive_review_count,
            "critical_review_count": self.critical_review_count,
            "theme_count": self.theme_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AnalysisStats:
        return cls(
            groq_requests=int(data.get("groq_requests", 0)),
            groq_tokens_estimated=int(data.get("groq_tokens_estimated", 0)),
            clustering_method=str(data.get("clustering_method", "")),
            positive_review_count=int(data.get("positive_review_count", 0)),
            critical_review_count=int(data.get("critical_review_count", 0)),
            theme_count=int(data.get("theme_count", 0)),
        )


@dataclass
class PulseReport:
    themes: list[Theme] = field(default_factory=list)
    quotes: list[ValidatedQuote] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    stats: AnalysisStats = field(default_factory=AnalysisStats)

    def to_dict(self) -> dict[str, Any]:
        return {
            "themes": [t.to_dict() for t in self.themes],
            "quotes": [q.to_dict() for q in self.quotes],
            "metadata": dict(self.metadata),
            "stats": self.stats.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PulseReport:
        return cls(
            themes=[Theme.from_dict(t) for t in data.get("themes", [])],
            quotes=[ValidatedQuote.from_dict(q) for q in data.get("quotes", [])],
            metadata=dict(data.get("metadata") or {}),
            stats=AnalysisStats.from_dict(data.get("stats") or {}),
        )
