from __future__ import annotations

import json
import logging
from datetime import date

from pulse_agent.config.loader import ProductConfig
from pulse_agent.models.review import ReviewCorpus
from pulse_agent.models.run import RunContext
from pulse_agent.phases.phase_01_ingestion.app_store import fetch_app_store_reviews
from pulse_agent.phases.phase_01_ingestion.normalize import normalize_corpus
from pulse_agent.phases.phase_01_ingestion.play_store import fetch_play_store_reviews

logger = logging.getLogger(__name__)


class IngestionError(Exception):
    """Raised when both stores fail or corpus below minimum threshold."""


def ingest_reviews(
    ctx: RunContext,
    product: ProductConfig,
    *,
    reference_date: date | None = None,
    play_count: int | None = None,
    app_store_max_pages: int | None = None,
) -> ReviewCorpus:
    play_limit = play_count if play_count is not None else product.play_fetch_count
    app_pages = (
        app_store_max_pages
        if app_store_max_pages is not None
        else product.app_store_max_pages
    )
    app_reviews = []
    play_reviews = []
    app_err: str | None = None
    play_err: str | None = None

    try:
        app_reviews = fetch_app_store_reviews(
            product.app_store_id,
            country=product.app_store_country,
            max_pages=app_pages,
        )
        logger.info(
            "App Store: fetched %s reviews for %s",
            len(app_reviews),
            product.product_id,
        )
    except Exception as exc:
        app_err = str(exc)
        logger.exception("App Store ingest failed: %s", exc)

    try:
        play_reviews = fetch_play_store_reviews(
            product.play_package,
            count=play_limit,
        )
        logger.info(
            "Play Store: fetched %s reviews for %s",
            len(play_reviews),
            product.product_id,
        )
    except Exception as exc:
        play_err = str(exc)
        logger.exception("Play Store ingest failed: %s", exc)

    corpus = normalize_corpus(
        app_reviews,
        play_reviews,
        window_weeks=product.window_weeks,
        reference_date=reference_date,
        app_store_error=app_err,
        play_store_error=play_err,
    )

    if not app_reviews and not play_reviews and (app_err or play_err):
        if app_err and play_err:
            raise IngestionError(
                f"Both stores failed. app_store={app_err}; play_store={play_err}"
            )

    if corpus.stats.after_content_filter < product.min_reviews_threshold:
        if app_err and play_err:
            raise IngestionError(
                f"Insufficient reviews ({corpus.stats.after_content_filter}) "
                f"and both stores failed."
            )
        logger.warning(
            "Review count %s below threshold %s for %s",
            corpus.stats.after_window,
            product.min_reviews_threshold,
            product.product_id,
        )

    return corpus


def persist_corpus(ctx: RunContext, corpus: ReviewCorpus) -> None:
    payload = {
        "idempotency_key": ctx.idempotency_key,
        "product_id": ctx.product_id,
        "iso_week": ctx.iso_week,
        **corpus.to_dict(),
    }
    ctx.reviews_path.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
