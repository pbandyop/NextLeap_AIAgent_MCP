from pathlib import Path

from pulse_agent.phases.phase_03_render.doc_section import build_doc_section


def test_doc_section_golden(groww_report, groww_product, render_limits, golden_dir: Path):
    _, _, content = build_doc_section(
        groww_report,
        groww_product,
        iso_week="2026-W20",
        review_count=205,
        limits=render_limits,
    )
    golden = golden_dir / "doc_section_groww.txt"
    assert golden.is_file(), f"Missing golden file: {golden}"
    expected = golden.read_text(encoding="utf-8")
    assert content == expected


def test_doc_section_includes_required_sections(
    groww_report, groww_product, render_limits
):
    heading, _, content = build_doc_section(
        groww_report,
        groww_product,
        iso_week="2026-W20",
        review_count=205,
        limits=render_limits,
    )
    assert heading == "Groww — Weekly Pulse — 2026-W20"
    for phrase in (
        "Who this helps",
        "Critical themes",
        "Positive themes",
        "Top suggested actions",
        "Period: 2026-W20",
        "Reviews analyzed: 205",
    ):
        assert phrase in content
