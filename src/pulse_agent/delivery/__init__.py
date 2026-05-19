"""Map render artifacts to workspace MCP HTTP tool payloads."""

from pulse_agent.delivery.docs import (
    AppendToDocPayload,
    build_section_url,
    map_render_to_append_payload,
)
from pulse_agent.delivery.gmail import (
    CreateEmailDraftPayload,
    map_render_to_gmail_payload,
)

__all__ = [
    "AppendToDocPayload",
    "build_section_url",
    "map_render_to_append_payload",
    "CreateEmailDraftPayload",
    "map_render_to_gmail_payload",
]
