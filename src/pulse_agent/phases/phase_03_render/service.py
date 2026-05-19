from __future__ import annotations

import logging

from pulse_agent.config.loader import ProductConfig
from pulse_agent.models.render import DocSectionPayload, EmailTeaserPayload, RenderedDelivery
from pulse_agent.models.report import PulseReport
from pulse_agent.models.run import RunContext
from pulse_agent.phases.phase_03_render.config import RenderLimits
from pulse_agent.phases.phase_03_render.doc_section import build_doc_section
from pulse_agent.phases.phase_03_render.email_teaser import DOC_LINK_PLACEHOLDER, build_email_teaser
from pulse_agent.phases.phase_03_render.persist import load_rendered, persist_rendered

logger = logging.getLogger(__name__)


class RenderError(RuntimeError):
    pass


def review_count_for_render(report: PulseReport, corpus_review_count: int | None = None) -> int:
    if corpus_review_count is not None and corpus_review_count > 0:
        return corpus_review_count
    total = report.stats.positive_review_count + report.stats.critical_review_count
    if total > 0:
        return total
    return sum(t.review_count for t in report.themes)


def render_report(
    ctx: RunContext,
    report: PulseReport,
    product: ProductConfig,
    *,
    review_count: int,
    limits: RenderLimits | None = None,
    force_render: bool = False,
) -> RenderedDelivery:
    limits = limits or RenderLimits.from_env()

    if not force_render:
        cached = load_rendered(ctx)
        if cached is not None:
            logger.info("Using cached render artifacts in %s", ctx.run_dir)
            return cached

    heading, anchor, content = build_doc_section(
        report,
        product,
        iso_week=ctx.iso_week,
        review_count=review_count,
        limits=limits,
    )
    subject, body_plain, body_html = build_email_teaser(
        report,
        product,
        iso_week=ctx.iso_week,
        review_count=review_count,
        limits=limits,
    )

    delivery = RenderedDelivery(
        doc_section=DocSectionPayload(
            heading=heading,
            anchor=anchor,
            content=content,
        ),
        email_teaser=EmailTeaserPayload(
            subject=subject,
            body_plain=body_plain,
            body_html=body_html,
            doc_link_placeholder=DOC_LINK_PLACEHOLDER,
            to_recipients=list(product.recipients),
        ),
        review_count=review_count,
        theme_count=len(report.themes),
    )
    persist_rendered(ctx, delivery)
    return delivery
