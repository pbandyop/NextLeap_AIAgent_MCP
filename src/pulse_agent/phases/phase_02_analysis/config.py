from __future__ import annotations

import os
from dataclasses import dataclass


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


def _float_env(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return float(raw)


@dataclass(frozen=True)
class AnalysisLimits:
    max_reviews: int = 2000
    max_clusters_positive: int = 5
    max_clusters_critical: int = 3
    critical_batch_max_reviews: int = 50
    critical_batch_max_tokens: int = 4000
    max_groq_requests_per_run: int = 10
    max_tokens_per_request: int = 1200
    max_tokens_per_run: int = 9000
    inter_request_delay_ms: int = 2500
    daily_token_budget: int = 80000
    min_themes: int = 3
    excerpts_per_cluster: int = 8
    max_words_per_excerpt: int = 120
    groq_temperature: float = 0.2

    @classmethod
    def from_env(cls) -> AnalysisLimits:
        return cls(
            max_reviews=_int_env("PULSE_MAX_REVIEWS", 2000),
            max_clusters_positive=_int_env("GROQ_MAX_CLUSTERS_POSITIVE", 5),
            max_clusters_critical=_int_env("GROQ_MAX_CLUSTERS_CRITICAL", 3),
            critical_batch_max_reviews=_int_env("PULSE_CRITICAL_BATCH_MAX_REVIEWS", 50),
            critical_batch_max_tokens=_int_env("PULSE_CRITICAL_BATCH_MAX_TOKENS", 4000),
            max_groq_requests_per_run=_int_env("GROQ_MAX_REQUESTS_PER_RUN", 10),
            max_tokens_per_request=_int_env("GROQ_MAX_TOKENS_PER_REQUEST", 1200),
            max_tokens_per_run=_int_env("GROQ_MAX_TOKENS_PER_RUN", 9000),
            inter_request_delay_ms=_int_env("GROQ_INTER_REQUEST_DELAY_MS", 2500),
            daily_token_budget=_int_env("GROQ_DAILY_TOKEN_BUDGET", 80000),
            min_themes=_int_env("PULSE_MIN_THEMES", 3),
            excerpts_per_cluster=_int_env("PULSE_EXCERPTS_PER_CLUSTER", 8),
            max_words_per_excerpt=_int_env("PULSE_MAX_WORDS_PER_EXCERPT", 120),
            groq_temperature=_float_env("GROQ_TEMPERATURE", 0.2),
        )


@dataclass(frozen=True)
class GroqSettings:
    api_key: str | None
    model: str
    base_url: str

    @classmethod
    def from_env(cls) -> GroqSettings:
        return cls(
            api_key=os.environ.get("GROQ_API_KEY") or None,
            model=os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
            base_url=os.environ.get(
                "GROQ_BASE_URL", "https://api.groq.com/openai/v1"
            ).rstrip("/"),
        )
