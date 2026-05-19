from pulse_agent.audit.logger import RunAudit, RunStatus
from pulse_agent.models.delivery import DocsDeliveryResult
from pulse_agent.models.run import RunContext


def test_audit_includes_docs_delivery_fields():
    ctx = RunContext(product_id="groww", iso_week="2026-W20", window_weeks=10)
    audit = RunAudit.stub_for(ctx, dry_run=False)
    docs = DocsDeliveryResult(
        doc_id="abc123",
        section_heading="Groww — Weekly Pulse — 2026-W20",
        section_url="https://docs.google.com/document/d/abc123/edit",
        anchor="<!-- pulse:groww:2026-W20 -->",
        idempotency_key=ctx.idempotency_key,
        status="success",
    )
    audit.delivery["docs"] = docs.to_dict()
    audit.status = RunStatus.COMPLETED

    payload = audit.to_dict()
    assert payload["delivery"]["docs"]["doc_id"] == "abc123"
    assert payload["delivery"]["docs"]["section_heading"] == docs.section_heading
    assert payload["delivery"]["docs"]["section_url"].startswith("https://docs.google.com/")
