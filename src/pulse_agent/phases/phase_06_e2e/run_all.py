from __future__ import annotations

import logging
from dataclasses import replace

from pulse_agent.config.loader import load_config
from pulse_agent.models.run import RunContext
from pulse_agent.phases.phase_06_e2e.exit_codes import EXIT_FATAL, EXIT_PARTIAL, EXIT_SUCCESS
from pulse_agent.phases.phase_06_e2e.pipeline import run_pipeline

logger = logging.getLogger(__name__)


def run_all_products(base_ctx: RunContext, product_ids: list[str] | None = None) -> int:
    config = load_config(base_ctx.project_root)
    ids = product_ids or list(config.products.keys())
    worst = EXIT_SUCCESS
    for pid in ids:
        logger.info("run-all: product=%s week=%s", pid, base_ctx.iso_week)
        ctx = replace(base_ctx, product_id=pid)
        try:
            config.get_product(pid)
        except KeyError:
            logger.warning("Skipping unknown product %s", pid)
            continue
        code = run_pipeline(ctx, config)
        if code == EXIT_PARTIAL:
            worst = max(worst, EXIT_PARTIAL)
        elif code != EXIT_SUCCESS:
            return EXIT_FATAL
    return worst
