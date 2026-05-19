import json

from pulse_agent.config.loader import load_config
from pulse_agent.models.run import RunContext
from pulse_agent.phases.phase_06_e2e.exit_codes import EXIT_SUCCESS
from pulse_agent.phases.phase_06_e2e.pipeline import run_pipeline


def test_dry_run_skips_delivery(project_root, tmp_path):
    ctx = RunContext(
        product_id="groww",
        iso_week="2026-W20",
        window_weeks=10,
        project_root=tmp_path,
        dry_run=True,
        skip_ingest=True,
        skip_analyze=True,
        skip_render=True,
        skip_mcp=True,
    )
    config = load_config(project_root)
    code = run_pipeline(ctx, config)
    assert code == EXIT_SUCCESS
    assert not (ctx.run_dir / "docs_delivery.json").exists()
    assert not (ctx.run_dir / "gmail_delivery.json").exists()
    audit = json.loads(ctx.audit_path.read_text(encoding="utf-8"))
    assert audit["dry_run"] is True
    assert "phase_04_docs_skipped_dry_run" in audit["phases_completed"]
