from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path


class RunStatus(str, Enum):
    STUB = "stub"
    DRY_RUN = "dry_run"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


def build_idempotency_key(product_id: str, iso_week: str) -> str:
    return f"pulse:{product_id}:{iso_week}"


def sanitize_path_segment(idempotency_key: str) -> str:
    """Filesystem-safe directory name (Windows cannot use ':')."""
    return idempotency_key.replace(":", "_")


@dataclass
class RunContext:
    product_id: str
    iso_week: str
    window_weeks: int
    dry_run: bool = False
    skip_mcp: bool = False
    skip_ingest: bool = False
    skip_analyze: bool = False
    force_analyze: bool = False
    skip_render: bool = False
    force_render: bool = False
    skip_docs: bool = False
    force_docs: bool = False
    skip_gmail: bool = False
    force_gmail: bool = False
    force_stub_llm: bool = False
    play_count: int | None = None
    app_store_max_pages: int | None = None
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    project_root: Path = field(default_factory=Path.cwd)

    @property
    def idempotency_key(self) -> str:
        return build_idempotency_key(self.product_id, self.iso_week)

    @property
    def run_dir(self) -> Path:
        base = self.project_root / "data" / "runs" / sanitize_path_segment(self.idempotency_key)
        base.mkdir(parents=True, exist_ok=True)
        return base

    @property
    def audit_path(self) -> Path:
        return self.run_dir / "run_audit.json"

    @property
    def legacy_audit_path(self) -> Path:
        """Phase 0 eval compatibility: runs/<sanitized>.json"""
        legacy_dir = self.project_root / "runs"
        legacy_dir.mkdir(parents=True, exist_ok=True)
        return legacy_dir / f"{sanitize_path_segment(self.idempotency_key)}.json"

    @property
    def reviews_path(self) -> Path:
        return self.run_dir / "reviews.json"

    @property
    def pulse_report_path(self) -> Path:
        return self.run_dir / "pulse_report.json"

    @property
    def render_manifest_path(self) -> Path:
        return self.run_dir / "render_manifest.json"

    @property
    def doc_section_path(self) -> Path:
        return self.run_dir / "doc_section.txt"

    @property
    def email_teaser_path(self) -> Path:
        return self.run_dir / "email_teaser.json"

    @property
    def docs_delivery_path(self) -> Path:
        return self.run_dir / "docs_delivery.json"

    @property
    def gmail_delivery_path(self) -> Path:
        return self.run_dir / "gmail_delivery.json"
