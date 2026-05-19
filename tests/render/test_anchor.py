from pulse_agent.phases.phase_03_render.doc_section import build_doc_section
from pulse_agent.phases.phase_03_render.heading import section_anchor


def test_idempotency_anchor_format():
    assert section_anchor("groww", "2026-W20") == "<!-- pulse:groww:2026-W20 -->"


def test_anchor_embedded_in_doc_section(groww_report, groww_product, render_limits):
    _, anchor, content = build_doc_section(
        groww_report,
        groww_product,
        iso_week="2026-W20",
        review_count=205,
        limits=render_limits,
    )
    assert anchor in content
    assert content.startswith("<!-- pulse:groww:2026-W20 -->")
