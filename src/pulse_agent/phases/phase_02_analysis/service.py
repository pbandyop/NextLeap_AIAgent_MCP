from __future__ import annotations

import logging

from pulse_agent.models.report import AnalysisStats, PulseReport, Theme
from pulse_agent.models.review import Review, ReviewCorpus
from pulse_agent.models.run import RunContext
from pulse_agent.phases.phase_02_analysis.clustering import cluster_reviews, review_texts
from pulse_agent.phases.phase_02_analysis.config import AnalysisLimits, GroqSettings
from pulse_agent.phases.phase_02_analysis.embeddings import embed_texts, embedding_method
from pulse_agent.phases.phase_02_analysis.groq_client import (
    GroqUsage,
    ThemeLlmClient,
    build_theme_client,
)
from pulse_agent.phases.phase_02_analysis.persist import load_report, persist_report, report_path
from pulse_agent.phases.phase_02_analysis.prompts import build_cluster_user_prompt
from pulse_agent.phases.phase_02_analysis.quotes import (
    select_quote_for_cluster,
    validate_report_quotes,
)
from pulse_agent.phases.phase_02_analysis.sampling import estimate_tokens, select_exemplars
from pulse_agent.phases.phase_02_analysis.sentiment import split_by_sentiment

logger = logging.getLogger(__name__)


class AnalysisError(Exception):
    pass


def analyze_reviews(
    ctx: RunContext,
    corpus: ReviewCorpus,
    *,
    limits: AnalysisLimits | None = None,
    groq_settings: GroqSettings | None = None,
    force_stub_llm: bool = False,
    force_analyze: bool = False,
) -> PulseReport:
    limits = limits or AnalysisLimits.from_env()
    groq_settings = groq_settings or GroqSettings.from_env()

    existing = load_report(report_path(ctx))
    if existing and not force_analyze:
        logger.info("Using cached PulseReport at %s", report_path(ctx))
        return existing

    reviews = list(corpus.reviews)
    if len(reviews) > limits.max_reviews:
        logger.warning(
            "Truncating reviews from %s to max_reviews=%s",
            len(reviews),
            limits.max_reviews,
        )
        reviews = reviews[: limits.max_reviews]

    positive, critical = split_by_sentiment(reviews)
    llm = build_theme_client(groq_settings, limits, force_stub=force_stub_llm)
    usage = getattr(llm, "usage", GroqUsage())

    themes: list[Theme] = []
    quotes = []
    methods: list[str] = []
    cluster_members: dict[str, list[Review]] = {}

    critical_themes, critical_method, critical_members = _analyze_bucket(
        critical,
        sentiment="critical",
        max_clusters=limits.max_clusters_critical,
        limits=limits,
        llm=llm,
        usage=usage,
    )
    methods.append(critical_method)
    themes.extend(critical_themes)
    cluster_members.update(critical_members)

    positive_themes, positive_method, positive_members = _analyze_bucket(
        positive,
        sentiment="positive",
        max_clusters=limits.max_clusters_positive,
        limits=limits,
        llm=llm,
        usage=usage,
    )
    methods.append(positive_method)
    themes.extend(positive_themes)
    cluster_members.update(positive_members)

    themes = _sort_themes(themes)
    reviews_by_id = {r.review_id: r for r in reviews}

    for theme in themes:
        members = cluster_members.get(theme.cluster_id, [])
        quotes.extend(select_quote_for_cluster(members, theme.cluster_id))

    errors = validate_report_quotes(quotes, reviews_by_id)
    if errors:
        raise AnalysisError(f"Quote validation failed: {errors[:3]}")

    if len(themes) < limits.min_themes and themes:
        logger.warning(
            "Only %s themes produced (min %s); proceeding with available data",
            len(themes),
            limits.min_themes,
        )

    report = PulseReport(
        themes=themes,
        quotes=quotes,
        metadata={
            "idempotency_key": ctx.idempotency_key,
            "product_id": ctx.product_id,
            "iso_week": ctx.iso_week,
            "embedding_method": embedding_method(),
            "clustering_methods": methods,
            "llm_stub": force_stub_llm or not groq_settings.api_key,
        },
        stats=AnalysisStats(
            groq_requests=usage.requests,
            groq_tokens_estimated=usage.tokens_estimated,
            clustering_method=",".join(methods),
            positive_review_count=len(positive),
            critical_review_count=len(critical),
            theme_count=len(themes),
        ),
    )
    persist_report(ctx, report)
    return report


def _analyze_bucket(
    reviews: list[Review],
    *,
    sentiment: str,
    max_clusters: int,
    limits: AnalysisLimits,
    llm: ThemeLlmClient,
    usage: GroqUsage,
) -> tuple[list[Theme], str, dict[str, list[Review]]]:
    members_map: dict[str, list[Review]] = {}
    if not reviews:
        return [], "empty", members_map

    if (
        sentiment == "critical"
        and len(reviews) <= limits.critical_batch_max_reviews
    ):
        batch_tokens = sum(
            estimate_tokens(excerpt)
            for _, excerpt in select_exemplars(
                reviews,
                max_count=len(reviews),
                max_words_per_excerpt=limits.max_words_per_excerpt,
            )
        )
        if batch_tokens < limits.critical_batch_max_tokens and usage.can_call(
            limits, batch_tokens + 200
        ):
            themes = _batched_critical_theme(reviews, llm, usage)
            members_map["critical_batch"] = list(reviews)
            return themes, "critical_batch", members_map

    texts = review_texts(reviews)
    embeddings = embed_texts(texts)
    clusters, method = cluster_reviews(
        reviews,
        embeddings,
        max_clusters=max_clusters,
        min_cluster_size=10 if len(reviews) > 30 else 3,
    )
    themes: list[Theme] = []
    for label, members in clusters.items():
        cluster_id = f"{sentiment}_{label}"
        if not usage.can_call(limits, 500):
            logger.warning("Groq budget exhausted; skipping cluster %s", cluster_id)
            break
        exemplars = select_exemplars(
            members,
            max_count=limits.excerpts_per_cluster,
            max_words_per_excerpt=limits.max_words_per_excerpt,
        )
        prompt = build_cluster_user_prompt(sentiment, cluster_id, exemplars)
        try:
            parsed = llm.complete_theme(prompt)
        except Exception as exc:
            logger.warning("LLM failed for %s: %s", cluster_id, exc)
            parsed = {
                "label": f"{sentiment.title()} theme {label}",
                "summary": "Theme summary unavailable (LLM error).",
                "actions": ["Review cluster manually"],
            }
        themes.append(
            Theme(
                cluster_id=cluster_id,
                label=parsed["label"],
                summary=parsed["summary"],
                sentiment=sentiment,
                review_count=len(members),
                actions=list(parsed.get("actions") or []),
            )
        )
        members_map[cluster_id] = members
    return themes, method, members_map


def _batched_critical_theme(
    reviews: list[Review], llm: ThemeLlmClient, usage: GroqUsage
) -> list[Theme]:
    exemplars = select_exemplars(reviews, max_count=min(50, len(reviews)), max_words_per_excerpt=120)
    prompt = build_cluster_user_prompt("critical", "critical_batch", exemplars)
    parsed = llm.complete_theme(prompt)
    return [
        Theme(
            cluster_id="critical_batch",
            label=parsed["label"],
            summary=parsed["summary"],
            sentiment="critical",
            review_count=len(reviews),
            actions=list(parsed.get("actions") or []),
        )
    ]


def _sort_themes(themes: list[Theme]) -> list[Theme]:
    def key(theme: Theme) -> tuple:
        critical_first = 0 if theme.sentiment == "critical" else 1
        return (critical_first, -theme.review_count, theme.label)

    return sorted(themes, key=key)

