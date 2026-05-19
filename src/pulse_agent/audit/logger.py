from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pulse_agent.models.run import RunContext, RunStatus


@dataclass
class McpSmokeResult:
    server: str
    ok: bool
    tool_count: int = 0
    tools: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RunAudit:
    run_id: str
    product_id: str
    iso_week: str
    idempotency_key: str
    status: RunStatus
    dry_run: bool
    started_at: str
    finished_at: str | None = None
    phases_completed: list[str] = field(default_factory=list)
    ingest: dict[str, Any] = field(default_factory=dict)
    analysis: dict[str, Any] = field(default_factory=dict)
    render: dict[str, Any] = field(default_factory=dict)
    mcp_smoke: list[dict[str, Any]] = field(default_factory=list)
    delivery: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value if isinstance(self.status, RunStatus) else self.status
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RunAudit:
        status = data.get("status", RunStatus.STUB.value)
        if isinstance(status, str):
            status = RunStatus(status)
        return cls(
            run_id=data["run_id"],
            product_id=data["product_id"],
            iso_week=data["iso_week"],
            idempotency_key=data["idempotency_key"],
            status=status,
            dry_run=bool(data.get("dry_run", False)),
            started_at=data["started_at"],
            finished_at=data.get("finished_at"),
            phases_completed=list(data.get("phases_completed") or []),
            ingest=dict(data.get("ingest") or {}),
            analysis=dict(data.get("analysis") or {}),
            render=dict(data.get("render") or {}),
            mcp_smoke=list(data.get("mcp_smoke") or []),
            delivery=dict(data.get("delivery") or {}),
            metrics=dict(data.get("metrics") or {}),
            errors=list(data.get("errors") or []),
        )

    @classmethod
    def stub_for(cls, ctx: RunContext, dry_run: bool) -> RunAudit:
        return cls(
            run_id=ctx.run_id,
            product_id=ctx.product_id,
            iso_week=ctx.iso_week,
            idempotency_key=ctx.idempotency_key,
            status=RunStatus.DRY_RUN if dry_run else RunStatus.STUB,
            dry_run=dry_run,
            started_at=ctx.started_at.isoformat(),
        )


def save_audit(ctx: RunContext, audit: RunAudit) -> None:
    audit.finished_at = datetime.now(timezone.utc).isoformat()
    payload = json.dumps(audit.to_dict(), indent=2)
    ctx.audit_path.write_text(payload, encoding="utf-8")
    ctx.legacy_audit_path.write_text(payload, encoding="utf-8")


def load_audit(path: Path) -> RunAudit:
    return RunAudit.from_dict(json.loads(path.read_text(encoding="utf-8")))
