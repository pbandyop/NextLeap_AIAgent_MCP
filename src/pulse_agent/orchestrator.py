from __future__ import annotations

from pathlib import Path

from pulse_agent.config.loader import AppConfig
from pulse_agent.models.run import RunContext
from pulse_agent.phases.phase_06_e2e.pipeline import run_pipeline


def run_pipeline_for_context(
    ctx: RunContext,
    config: AppConfig | None = None,
) -> int:
    """Run full E2E pipeline (Phase 6)."""
    return run_pipeline(ctx, config)


# Backward-compatible alias used by CLI and tests.
run_pipeline = run_pipeline_for_context


def find_project_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for path in [current, *current.parents]:
        if (path / "config" / "products.yaml").is_file():
            return path
    return current
