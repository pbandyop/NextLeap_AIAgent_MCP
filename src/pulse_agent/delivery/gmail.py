from __future__ import annotations

from dataclasses import dataclass

from pulse_agent.models.delivery import DocsDeliveryResult
from pulse_agent.models.render import RenderedDelivery
from pulse_agent.phases.phase_03_render.email_teaser import DOC_LINK_PLACEHOLDER

PULSE_RUN_ID_HEADER = "X-Pulse-Run-Id"


@dataclass(frozen=True)
class CreateEmailDraftPayload:
    """Arguments for POST /create_email_draft on the workspace HTTP MCP server."""

    to: str
    subject: str
    body: str


def inject_doc_link(text: str, section_url: str) -> str:
    return text.replace(DOC_LINK_PLACEHOLDER, section_url)


def append_idempotency_footer(body: str, *, idempotency_key: str, run_id: str) -> str:
    footer = (
        f"\n\n---\n"
        f"{PULSE_RUN_ID_HEADER}: {idempotency_key}\n"
        f"Run-Id: {run_id}\n"
    )
    return body.rstrip() + footer


def map_render_to_gmail_payload(
    rendered: RenderedDelivery,
    docs: DocsDeliveryResult,
    *,
    to: str,
    idempotency_key: str,
    run_id: str,
) -> CreateEmailDraftPayload:
    body = inject_doc_link(rendered.email_teaser.body_plain, docs.section_url)
    body = append_idempotency_footer(
        body,
        idempotency_key=idempotency_key,
        run_id=run_id,
    )
    return CreateEmailDraftPayload(
        to=to,
        subject=rendered.email_teaser.subject,
        body=body,
    )
