from __future__ import annotations

import logging

from pulse_agent.config.loader import (
    AppConfig,
    ProductConfig,
    resolve_email_mode,
    resolve_email_recipient,
)
from pulse_agent.delivery.gmail import map_render_to_gmail_payload
from pulse_agent.models.delivery import DocsDeliveryResult, GmailDeliveryResult
from pulse_agent.models.render import RenderedDelivery
from pulse_agent.models.run import RunContext
from pulse_agent.phases.phase_04_docs_mcp.client import WorkspaceHttpClient, WorkspaceMcpError
from pulse_agent.phases.phase_04_docs_mcp.persist import load_docs_delivery
from pulse_agent.phases.phase_04_docs_mcp.service import (
    DocsDeliveryError,
    _timeout_seconds,
    workspace_base_url,
)
from pulse_agent.phases.phase_05_gmail_mcp.persist import load_gmail_delivery, persist_gmail_delivery

logger = logging.getLogger(__name__)


class GmailDeliveryError(RuntimeError):
    pass


def deliver_gmail(
    ctx: RunContext,
    rendered: RenderedDelivery,
    docs: DocsDeliveryResult,
    product: ProductConfig,
    config: AppConfig,
    *,
    force_deliver: bool = False,
) -> GmailDeliveryResult:
    """
    Create Gmail draft (or send when supported) via workspace MCP HTTP server.
    Idempotent per idempotency_key using local gmail_delivery.json.
    """
    mode = resolve_email_mode(config)
    if mode == "send":
        raise GmailDeliveryError(
            "EMAIL_MODE=send is not supported by the workspace HTTP MCP server yet; "
            "use EMAIL_MODE=draft and send from Gmail, or extend the MCP server with a send tool."
        )

    to = resolve_email_recipient(product)

    if not force_deliver:
        cached = load_gmail_delivery(ctx)
        if (
            cached is not None
            and cached.idempotency_key == ctx.idempotency_key
            and cached.status == "success"
            and cached.to == to
        ):
            logger.info("Gmail delivery cached for %s", ctx.idempotency_key)
            return cached

    payload = map_render_to_gmail_payload(
        rendered,
        docs,
        to=to,
        idempotency_key=ctx.idempotency_key,
        run_id=ctx.run_id,
    )

    client = WorkspaceHttpClient(
        workspace_base_url(config),
        timeout_seconds=_timeout_seconds(config),
    )

    try:
        client.health_check()
    except Exception as exc:
        raise GmailDeliveryError(f"Workspace MCP health check failed: {exc}") from exc

    try:
        response = client.create_email_draft(payload.to, payload.subject, payload.body)
    except WorkspaceMcpError as exc:
        raise GmailDeliveryError(str(exc)) from exc

    draft_id = response.get("draft_id")
    result = GmailDeliveryResult(
        to=to,
        subject=payload.subject,
        mode=mode,
        idempotency_key=ctx.idempotency_key,
        section_url=docs.section_url,
        status="success",
        gmail_draft_id=str(draft_id) if draft_id else None,
        gmail_message_id=None,
        message=str(response.get("message", "Draft created")),
        run_id=ctx.run_id,
    )
    persist_gmail_delivery(ctx, result)
    return result


def load_docs_for_gmail(ctx: RunContext) -> DocsDeliveryResult:
    docs = load_docs_delivery(ctx)
    if docs is None or docs.status != "success":
        raise DocsDeliveryError(
            f"No successful docs delivery at {ctx.docs_delivery_path}; run Phase 4 first"
        )
    return docs
