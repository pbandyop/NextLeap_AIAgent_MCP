import json
import shutil

from pulse_agent.config.loader import load_config
from pulse_agent.models.run import RunContext
from pulse_agent.phases.phase_02_analysis.persist import load_report
from pulse_agent.phases.phase_03_render.service import render_report


def test_render_persists_artifacts(project_root, tmp_path):
    fixture = project_root / "tests" / "fixtures" / "pulse_report_groww.json"
    ctx = RunContext(
        product_id="groww",
        iso_week="2026-W20",
        window_weeks=10,
        project_root=tmp_path,
    )
    ctx.run_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(fixture, ctx.pulse_report_path)

    config = load_config(project_root)
    product = config.get_product("groww")
    report = load_report(ctx.pulse_report_path)
    assert report is not None

    delivery = render_report(ctx, report, product, review_count=205, force_render=True)

    assert ctx.doc_section_path.is_file()
    assert ctx.email_teaser_path.is_file()
    assert ctx.render_manifest_path.is_file()
    assert delivery.doc_section.content == ctx.doc_section_path.read_text(encoding="utf-8")

    manifest = json.loads(ctx.render_manifest_path.read_text(encoding="utf-8"))
    assert manifest["idempotency_key"] == "pulse:groww:2026-W20"
    assert manifest["email_teaser"]["subject"] == delivery.email_teaser.subject
