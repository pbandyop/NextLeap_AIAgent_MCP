from pulse_agent.audit.logger import RunAudit, RunStatus
from pulse_agent.models.delivery import GmailDeliveryResult
from pulse_agent.models.run import RunContext


def test_audit_includes_gmail_delivery_fields():
    ctx = RunContext(product_id="groww", iso_week="2026-W20", window_weeks=10)
    audit = RunAudit.stub_for(ctx, dry_run=False)
    gmail = GmailDeliveryResult(
        to="pm@example.com",
        subject="Groww Weekly Pulse",
        mode="draft",
        idempotency_key=ctx.idempotency_key,
        section_url="https://docs.google.com/document/d/abc/edit",
        status="success",
        gmail_draft_id="draft-123",
        run_id=ctx.run_id,
    )
    audit.delivery["gmail"] = gmail.to_dict()
    audit.status = RunStatus.COMPLETED

    payload = audit.to_dict()
    assert payload["delivery"]["gmail"]["gmail_draft_id"] == "draft-123"
    assert payload["delivery"]["gmail"]["mode"] == "draft"
    assert payload["delivery"]["gmail"]["to"] == "pm@example.com"
