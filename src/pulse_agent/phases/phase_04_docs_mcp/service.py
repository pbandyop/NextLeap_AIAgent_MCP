from __future__ import annotations

import logging
import os

from pulse_agent.config.loader import AppConfig, ProductConfig, resolve_google_doc_id
from pulse_agent.delivery.docs import build_section_url, map_render_to_append_payload
from pulse_agent.models.delivery import DocsDeliveryResult
from pulse_agent.models.render import RenderedDelivery
from pulse_agent.models.run import RunContext
from pulse_agent.phases.phase_04_docs_mcp.client import WorkspaceHttpClient, WorkspaceMcpError
from pulse_agent.phases.phase_04_docs_mcp.persist import load_docs_delivery, persist_docs_delivery

logger = logging.getLogger(__name__)


class DocsDeliveryError(RuntimeError):
    pass


def workspace_base_url(config: AppConfig) -> str:
    env_url = os.environ.get("GOOGLE_MCP_BASE_URL", "").strip()
    if env_url:
        return env_url.rstrip("/")
    server = config.mcp_servers.get("google_workspace")
    if server and server.base_url:
        return server.base_url.rstrip("/")
    return "https://saksham-mcp-server-production-b243.up.railway.app"


def deliver_docs(
    ctx: RunContext,
    rendered: RenderedDelivery,
    product: ProductConfig,
    config: AppConfig,
    *,
    force_deliver: bool = False,
) -> DocsDeliveryResult:
    """
    Append rendered doc section via workspace MCP HTTP server.
    Idempotent per idempotency_key using local docs_delivery.json (anchor recorded).
    """
    doc_id = resolve_google_doc_id(product)
    heading = rendered.doc_section.heading
    anchor = rendered.doc_section.anchor
    section_url = build_section_url(doc_id, heading)

    if not force_deliver:
        cached = load_docs_delivery(ctx)
        if (
            cached is not None
            and cached.idempotency_key == ctx.idempotency_key
            and cached.status in ("success", "skipped")
            and cached.anchor == anchor
        ):
            logger.info("Docs delivery cached for %s", ctx.idempotency_key)
            return cached

    payload = map_render_to_append_payload(rendered, doc_id)
    client = WorkspaceHttpClient(
        workspace_base_url(config),
        timeout_seconds=_timeout_seconds(config),
    )

    try:
        client.health_check()
    except Exception as exc:
        raise DocsDeliveryError(f"Workspace MCP health check failed: {exc}") from exc

    try:
        response = client.append_to_doc(payload.doc_id, payload.content)
    except WorkspaceMcpError as exc:
        raise DocsDeliveryError(str(exc)) from exc

    result = DocsDeliveryResult(
        doc_id=doc_id,
        section_heading=heading,
        section_url=section_url,
        anchor=anchor,
        idempotency_key=ctx.idempotency_key,
        status="success",
        message=str(response.get("message", "Content appended to document")),
        document_id=str(response.get("document_id") or doc_id),
    )
    persist_docs_delivery(ctx, result)
    return result


def _timeout_seconds(config: AppConfig) -> float:
    server = config.mcp_servers.get("google_workspace")
    if server:
        return float(server.timeout_seconds)
    return 120.0
