from __future__ import annotations

from pulse_agent.models.run import build_idempotency_key


def section_heading(display_name: str, iso_week: str) -> str:
    return f"{display_name} — Weekly Pulse — {iso_week}"


def section_anchor(product_id: str, iso_week: str) -> str:
    return f"<!-- {build_idempotency_key(product_id, iso_week)} -->"
