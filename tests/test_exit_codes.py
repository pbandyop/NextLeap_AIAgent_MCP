import json

import pytest

from pulse_agent.config.loader import AppConfig, ProductConfig, load_config
from pulse_agent.models.delivery import DocsDeliveryResult
from pulse_agent.models.render import DocSectionPayload, EmailTeaserPayload, RenderedDelivery
from pulse_agent.models.run import RunContext, RunStatus
from pulse_agent.phases.phase_03_render.persist import persist_rendered
from pulse_agent.phases.phase_05_gmail_mcp.service import GmailDeliveryError
from pulse_agent.phases.phase_06_e2e.exit_codes import EXIT_FATAL, EXIT_PARTIAL
from pulse_agent.phases.phase_06_e2e.pipeline import run_pipeline


def _minimal_rendered() -> RenderedDelivery:
    return RenderedDelivery(
        doc_section=DocSectionPayload(
            heading="Test — Weekly Pulse — 2026-W20",
            anchor="<!-- pulse:groww:2026-W20 -->",
            content="section body",
        ),
        email_teaser=EmailTeaserPayload(
            subject="Test Weekly Pulse",
            body_plain="teaser\nFull report: {{DOC_LINK}}",
            body_html="<p>teaser</p>",
            doc_link_placeholder="{{DOC_LINK}}",
        ),
        review_count=10,
        theme_count=1,
    )


def test_partial_exit_when_gmail_fails_after_docs(project_root, tmp_path, monkeypatch):
    monkeypatch.setenv("PULSE_EMAIL_TO", "test@example.com")
    monkeypatch.setenv("EMAIL_MODE", "draft")
    monkeypatch.setenv("GOOGLE_DOC_ID", "doc-test")

    ctx = RunContext(
        product_id="groww",
        iso_week="2026-W20",
        window_weeks=10,
        project_root=tmp_path,
        skip_ingest=True,
        skip_analyze=True,
        skip_render=True,
        skip_mcp=True,
    )
    ctx.run_dir.mkdir(parents=True, exist_ok=True)
    persist_rendered(ctx, _minimal_rendered())

    config = load_config(project_root)
    docs = DocsDeliveryResult(
        doc_id="doc-test",
        section_heading="Test — Weekly Pulse — 2026-W20",
        section_url="https://docs.google.com/document/d/doc-test/edit",
        anchor="<!-- pulse:groww:2026-W20 -->",
        idempotency_key=ctx.idempotency_key,
        status="success",
    )

    import pulse_agent.phases.phase_06_e2e.pipeline as pipeline_mod

    monkeypatch.setattr(pipeline_mod, "deliver_docs", lambda *a, **k: docs)

    def fail_gmail(*args, **kwargs):
        raise GmailDeliveryError("simulated gmail failure")

    monkeypatch.setattr(pipeline_mod, "deliver_gmail", fail_gmail)

    code = run_pipeline(ctx, config)
    assert code == EXIT_PARTIAL
    audit = json.loads(ctx.audit_path.read_text(encoding="utf-8"))
    assert audit["status"] == RunStatus.PARTIAL.value
    assert audit["delivery"]["docs"]
    assert "gmail" not in audit["delivery"]


def test_fatal_when_no_render_for_docs(project_root, tmp_path, monkeypatch):
    monkeypatch.setenv("GOOGLE_DOC_ID", "doc-test")
    ctx = RunContext(
        product_id="groww",
        iso_week="2026-W20",
        window_weeks=10,
        project_root=tmp_path,
        skip_ingest=True,
        skip_analyze=True,
        skip_render=True,
        skip_mcp=True,
    )
    config = load_config(project_root)
    code = run_pipeline(ctx, config)
    assert code == EXIT_FATAL
