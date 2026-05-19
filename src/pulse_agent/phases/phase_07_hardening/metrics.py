from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pulse_agent.audit.logger import RunAudit
from pulse_agent.config.loader import AppConfig, resolve_email_mode
from pulse_agent.models.run import RunContext, RunStatus


def attach_run_metrics(
    audit: RunAudit,
    ctx: RunContext,
    config: AppConfig,
    *,
    started_at: datetime,
) -> dict[str, Any]:
    finished = datetime.now(timezone.utc)
    duration = (finished - started_at).total_seconds()
    metrics: dict[str, Any] = {
        "duration_seconds": round(duration, 2),
        "pulse_env": config.pulse_env,
        "email_mode": resolve_email_mode(config),
        "product_id": ctx.product_id,
        "iso_week": ctx.iso_week,
        "idempotency_key": ctx.idempotency_key,
        "run_id": ctx.run_id,
    }
    if audit.ingest:
        metrics["review_count"] = audit.ingest.get("review_count")
    if audit.analysis:
        metrics["groq_requests"] = audit.analysis.get("groq_requests")
        metrics["groq_tokens_estimated"] = audit.analysis.get("groq_tokens_estimated")
        metrics["theme_count"] = audit.analysis.get("theme_count")
    audit.metrics = metrics
    return metrics


def finalize_audit(
    audit: RunAudit,
    ctx: RunContext,
    config: AppConfig,
    *,
    started_at: datetime,
    exit_code: int,
) -> None:
    attach_run_metrics(audit, ctx, config, started_at=started_at)
    if exit_code == 0:
        audit.status = RunStatus.DRY_RUN if ctx.dry_run else RunStatus.COMPLETED
    elif exit_code == 2:
        audit.status = RunStatus.PARTIAL
    else:
        audit.status = RunStatus.FAILED
