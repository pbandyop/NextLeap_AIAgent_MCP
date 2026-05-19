import os

import pytest

from pulse_agent.config.loader import AppConfig, ProductConfig
from pulse_agent.models.delivery import DocsDeliveryResult, GmailDeliveryResult
from pulse_agent.models.run import RunContext
from pulse_agent.phases.phase_05_gmail_mcp.persist import persist_gmail_delivery
from pulse_agent.phases.phase_05_gmail_mcp.service import deliver_gmail


def test_deliver_gmail_uses_cache(tmp_path, rendered_groww, monkeypatch):
    monkeypatch.setenv("PULSE_EMAIL_TO", "cached@example.com")
    monkeypatch.setenv("EMAIL_MODE", "draft")

    ctx = RunContext(
        product_id="groww",
        iso_week="2026-W20",
        window_weeks=10,
        project_root=tmp_path,
    )
    ctx.run_dir.mkdir(parents=True, exist_ok=True)

    docs = DocsDeliveryResult(
        doc_id="doc-1",
        section_heading=rendered_groww.doc_section.heading,
        section_url="https://docs.google.com/document/d/doc-1/edit",
        anchor=rendered_groww.doc_section.anchor,
        idempotency_key=ctx.idempotency_key,
        status="success",
    )

    cached = GmailDeliveryResult(
        to="cached@example.com",
        subject=rendered_groww.email_teaser.subject,
        mode="draft",
        idempotency_key=ctx.idempotency_key,
        section_url=docs.section_url,
        status="success",
        gmail_draft_id="draft-cached",
        run_id=ctx.run_id,
    )
    persist_gmail_delivery(ctx, cached)

    def fail_draft(*args, **kwargs):
        raise AssertionError("should not call MCP when cache hit")

    import pulse_agent.phases.phase_05_gmail_mcp.service as svc

    monkeypatch.setattr(svc.WorkspaceHttpClient, "create_email_draft", fail_draft)
    monkeypatch.setattr(svc.WorkspaceHttpClient, "health_check", lambda self: {})

    product = ProductConfig(
        product_id="groww",
        display_name="Groww",
        app_store_id="1",
        play_package="x",
        doc_title_template="t",
    )
    config = AppConfig(products={"groww": product}, mcp_servers={}, project_root=tmp_path)

    result = deliver_gmail(ctx, rendered_groww, docs, product, config)
    assert result.gmail_draft_id == "draft-cached"


def test_resolve_email_recipient_from_env(monkeypatch):
    from pulse_agent.config.loader import resolve_email_recipient

    monkeypatch.setenv("PULSE_EMAIL_TO", "global@example.com")
    product = ProductConfig(
        product_id="groww",
        display_name="Groww",
        app_store_id="1",
        play_package="x",
        doc_title_template="t",
    )
    assert resolve_email_recipient(product) == "global@example.com"

    monkeypatch.setenv("PULSE_EMAIL_TO_GROWW", "groww@example.com")
    assert resolve_email_recipient(product) == "groww@example.com"


def test_email_mode_send_raises_without_production_approval(
    monkeypatch, tmp_path, rendered_groww
):
    monkeypatch.setenv("PULSE_EMAIL_TO", "a@b.com")
    monkeypatch.setenv("EMAIL_MODE", "send")
    monkeypatch.setenv("PULSE_ENV", "production")
    monkeypatch.delenv("PULSE_PRODUCTION_SEND_APPROVED", raising=False)

    from pulse_agent.phases.phase_07_hardening.gates import ProductionGateError

    ctx = RunContext(product_id="groww", iso_week="2026-W20", window_weeks=10, project_root=tmp_path)
    docs = DocsDeliveryResult(
        doc_id="d",
        section_heading="h",
        section_url="https://example.com",
        anchor="a",
        idempotency_key=ctx.idempotency_key,
        status="success",
    )
    product = ProductConfig(
        product_id="groww",
        display_name="Groww",
        app_store_id="1",
        play_package="x",
        doc_title_template="t",
    )
    config = AppConfig(
        products={"groww": product},
        mcp_servers={},
        project_root=tmp_path,
        pulse_env="production",
    )

    with pytest.raises(ProductionGateError):
        deliver_gmail(ctx, rendered_groww, docs, product, config, force_deliver=True)
