from pulse_agent.models.run import RunContext, build_idempotency_key, sanitize_path_segment


def test_idempotency_key_format():
    assert build_idempotency_key("groww", "2026-W20") == "pulse:groww:2026-W20"


def test_sanitize_path_segment_windows_safe():
    key = build_idempotency_key("groww", "2026-W20")
    assert ":" not in sanitize_path_segment(key)
    assert sanitize_path_segment(key) == "pulse_groww_2026-W20"


def test_run_context_paths(project_root, tmp_path):
    ctx = RunContext(
        product_id="groww",
        iso_week="2026-W20",
        window_weeks=10,
        project_root=project_root,
    )
    assert ctx.idempotency_key == "pulse:groww:2026-W20"
    assert "pulse_groww_2026-W20" in str(ctx.run_dir)
