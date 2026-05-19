from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

from pulse_agent.models.render import RenderedDelivery


@dataclass(frozen=True)
class AppendToDocPayload:
    """Arguments for POST /append_to_doc on the workspace HTTP MCP server."""

    doc_id: str
    content: str


def map_render_to_append_payload(
    rendered: RenderedDelivery,
    doc_id: str,
) -> AppendToDocPayload:
    return AppendToDocPayload(
        doc_id=doc_id,
        content=rendered.doc_section.content,
    )


def build_section_url(doc_id: str, heading: str | None = None) -> str:
    """
    Google Docs edit URL for Gmail deep links (Phase 5).
    The MCP server appends plain text only; heading fragments are best-effort.
    """
    base = f"https://docs.google.com/document/d/{doc_id}/edit"
    if not heading:
        return base
    fragment = quote(heading.replace(" ", "-"), safe="")
    return f"{base}#heading={fragment}"
