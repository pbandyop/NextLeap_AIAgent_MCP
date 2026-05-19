from __future__ import annotations

import json
from pathlib import Path

from pulse_agent.models.report import PulseReport
from pulse_agent.models.run import RunContext


def report_path(ctx: RunContext) -> Path:
    return ctx.run_dir / "pulse_report.json"


def load_report(path: Path) -> PulseReport | None:
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    report = PulseReport.from_dict(data)
    meta = dict(report.metadata)
    for key in ("product_id", "iso_week", "idempotency_key"):
        if key in data and key not in meta:
            meta[key] = data[key]
    report.metadata = meta
    return report


def load_report_from_run(ctx: RunContext) -> PulseReport | None:
    return load_report(report_path(ctx))


def persist_report(ctx: RunContext, report: PulseReport) -> Path:
    path = report_path(ctx)
    payload = {
        "idempotency_key": ctx.idempotency_key,
        "product_id": ctx.product_id,
        "iso_week": ctx.iso_week,
        **report.to_dict(),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def load_corpus_from_run(ctx: RunContext):
    from pulse_agent.models.review import ReviewCorpus

    if not ctx.reviews_path.is_file():
        raise FileNotFoundError(f"Missing reviews file: {ctx.reviews_path}")
    data = json.loads(ctx.reviews_path.read_text(encoding="utf-8"))
    return ReviewCorpus.from_dict(data)
