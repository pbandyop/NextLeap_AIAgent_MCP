from pathlib import Path

from pulse_agent.phases.phase_03_render.email_teaser import (
    DOC_LINK_PLACEHOLDER,
    build_email_teaser,
)


def test_email_teaser_golden(groww_report, groww_product, render_limits, golden_dir: Path):
    subject, body_plain, body_html = build_email_teaser(
        groww_report,
        groww_product,
        iso_week="2026-W20",
        review_count=205,
        limits=render_limits,
    )
    golden_subject = (golden_dir / "email_subject_groww.txt").read_text(encoding="utf-8").strip()
    golden_plain = (golden_dir / "email_body_plain_groww.txt").read_text(encoding="utf-8")
    golden_html = (golden_dir / "email_body_html_groww.txt").read_text(encoding="utf-8")

    assert subject == golden_subject
    assert body_plain == golden_plain
    assert body_html == golden_html
    assert DOC_LINK_PLACEHOLDER in body_plain
    assert DOC_LINK_PLACEHOLDER in body_html


def test_email_teaser_within_limits(groww_report, groww_product):
    from pulse_agent.phases.phase_03_render.config import RenderLimits

    tight = RenderLimits(email_max_lines=5, email_max_words=30)
    _, body_plain, _ = build_email_teaser(
        groww_report,
        groww_product,
        iso_week="2026-W20",
        review_count=205,
        limits=tight,
    )
    assert len(body_plain.splitlines()) <= 6
    assert len(body_plain.split()) <= 31
