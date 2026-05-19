from __future__ import annotations

import logging
from dataclasses import replace

from pulse_agent.config.loader import load_config
from pulse_agent.models.run import RunContext
from pulse_agent.phases.phase_06_e2e.exit_codes import EXIT_FATAL, EXIT_PARTIAL, EXIT_SUCCESS
from pulse_agent.phases.phase_06_e2e.pipeline import run_pipeline
from pulse_agent.phases.phase_06_e2e.weeks import expand_week_range, parse_week_list

logger = logging.getLogger(__name__)


def run_backfill(
    *,
    product_id: str,
    weeks: list[str],
    base_ctx: RunContext,
) -> int:
    """
    Run the full pipeline for each ISO week. Returns worst exit code seen.
    """
    config = load_config(base_ctx.project_root)
    config.get_product(product_id)

    worst = EXIT_SUCCESS
    for iso_week in weeks:
        logger.info("Backfill: product=%s week=%s", product_id, iso_week)
        ctx = replace(
            base_ctx,
            product_id=product_id,
            iso_week=iso_week,
        )
        code = run_pipeline(ctx, config)
        if code == EXIT_PARTIAL:
            worst = max(worst, EXIT_PARTIAL)
        elif code != EXIT_SUCCESS:
            worst = EXIT_FATAL
            logger.error("Backfill stopped at fatal exit for %s", iso_week)
            return worst
    return worst


def resolve_backfill_weeks(
    *,
    weeks: str | None,
    from_week: str | None,
    to_week: str | None,
) -> list[str]:
    if weeks:
        return parse_week_list(weeks)
    if from_week and to_week:
        return expand_week_range(from_week, to_week)
    raise ValueError("Provide --weeks or both --from-week and --to-week")
