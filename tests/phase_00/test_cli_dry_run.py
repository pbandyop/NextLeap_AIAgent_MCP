import json

from pulse_agent.cli import main
from pulse_agent.models.run import sanitize_path_segment


def test_cli_dry_run_skip_ingest_writes_audit(project_root, tmp_path, monkeypatch):
    monkeypatch.chdir(project_root)
    code = main(
        [
            "run",
            "--product",
            "groww",
            "--week",
            "2026-W20",
            "--dry-run",
            "--skip-ingest",
        ]
    )
    assert code == 0
    legacy = project_root / "runs" / f"{sanitize_path_segment('pulse:groww:2026-W20')}.json"
    assert legacy.is_file()
    data = json.loads(legacy.read_text(encoding="utf-8"))
    assert data["status"] in ("dry_run", "stub")
    assert data["product_id"] == "groww"
    assert data["iso_week"] == "2026-W20"
