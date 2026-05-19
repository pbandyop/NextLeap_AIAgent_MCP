from __future__ import annotations

import json

from pulse_agent.models.render import RenderedDelivery
from pulse_agent.models.run import RunContext


def load_rendered(ctx: RunContext) -> RenderedDelivery | None:
    path = ctx.render_manifest_path
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return RenderedDelivery.from_dict(data)


def persist_rendered(ctx: RunContext, delivery: RenderedDelivery) -> None:
    payload = {
        "idempotency_key": ctx.idempotency_key,
        "product_id": ctx.product_id,
        "iso_week": ctx.iso_week,
        **delivery.to_dict(),
    }
    ctx.render_manifest_path.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    ctx.doc_section_path.write_text(
        delivery.doc_section.content,
        encoding="utf-8",
    )
    ctx.email_teaser_path.write_text(
        json.dumps(delivery.email_teaser.to_dict(), indent=2),
        encoding="utf-8",
    )
