from pulse_agent.config.loader import AppConfig, ProductConfig
from pulse_agent.models.delivery import DocsDeliveryResult
from pulse_agent.models.run import RunContext
from pulse_agent.phases.phase_04_docs_mcp.persist import load_docs_delivery, persist_docs_delivery
from pulse_agent.phases.phase_04_docs_mcp.service import deliver_docs


def test_deliver_docs_uses_cache(tmp_path, rendered_groww, monkeypatch):
    ctx = RunContext(
        product_id="groww",
        iso_week="2026-W20",
        window_weeks=10,
        project_root=tmp_path,
    )
    ctx.run_dir.mkdir(parents=True, exist_ok=True)

    cached = DocsDeliveryResult(
        doc_id="test-doc-id-abc123",
        section_heading=rendered_groww.doc_section.heading,
        section_url="https://docs.google.com/document/d/test-doc-id-abc123/edit",
        anchor=rendered_groww.doc_section.anchor,
        idempotency_key=ctx.idempotency_key,
        status="success",
        message="cached",
    )
    persist_docs_delivery(ctx, cached)

    def fail_append(*args, **kwargs):
        raise AssertionError("should not call MCP when cache hit")

    import pulse_agent.phases.phase_04_docs_mcp.service as svc

    monkeypatch.setattr(svc.WorkspaceHttpClient, "append_to_doc", fail_append)
    monkeypatch.setattr(svc.WorkspaceHttpClient, "health_check", lambda self: {})

    product = ProductConfig(
        product_id="groww",
        display_name="Groww",
        app_store_id="1",
        play_package="x",
        doc_title_template="t",
        google_doc_id="test-doc-id-abc123",
    )
    config = AppConfig(products={"groww": product}, mcp_servers={}, project_root=tmp_path)

    result = deliver_docs(ctx, rendered_groww, product, config)
    assert result.message == "cached"
    assert load_docs_delivery(ctx).doc_id == "test-doc-id-abc123"
