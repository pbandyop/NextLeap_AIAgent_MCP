from __future__ import annotations

from pathlib import Path

import pytest

from pulse_agent.config.loader import ProductConfig
from pulse_agent.models.render import RenderedDelivery
from pulse_agent.phases.phase_02_analysis.persist import load_report


@pytest.fixture
def groww_product() -> ProductConfig:
    return ProductConfig(
        product_id="groww",
        display_name="Groww",
        app_store_id="1404871703",
        play_package="com.nextbillion.groww",
        doc_title_template="Weekly Review Pulse — Groww",
        google_doc_id="test-doc-id-abc123",
    )


@pytest.fixture
def rendered_groww(project_root: Path) -> RenderedDelivery:
    from pulse_agent.phases.phase_03_render.config import RenderLimits
    from pulse_agent.phases.phase_03_render.doc_section import build_doc_section
    from pulse_agent.phases.phase_03_render.email_teaser import build_email_teaser
    from pulse_agent.models.render import DocSectionPayload, EmailTeaserPayload

    fixture = project_root / "tests" / "fixtures" / "pulse_report_groww.json"
    report = load_report(fixture)
    assert report is not None
    product = ProductConfig(
        product_id="groww",
        display_name="Groww",
        app_store_id="1",
        play_package="com.nextbillion.groww",
        doc_title_template="Weekly Review Pulse — Groww",
    )
    limits = RenderLimits()
    heading, anchor, content = build_doc_section(
        report, product, iso_week="2026-W20", review_count=205, limits=limits
    )
    subject, body_plain, body_html = build_email_teaser(
        report, product, iso_week="2026-W20", review_count=205, limits=limits
    )
    return RenderedDelivery(
        doc_section=DocSectionPayload(heading=heading, anchor=anchor, content=content),
        email_teaser=EmailTeaserPayload(
            subject=subject,
            body_plain=body_plain,
            body_html=body_html,
            doc_link_placeholder="{{DOC_LINK}}",
        ),
        review_count=205,
        theme_count=2,
    )
