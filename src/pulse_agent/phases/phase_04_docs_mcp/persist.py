from __future__ import annotations

import json

from pulse_agent.models.delivery import DocsDeliveryResult
from pulse_agent.models.run import RunContext


def load_docs_delivery(ctx: RunContext) -> DocsDeliveryResult | None:
    path = ctx.docs_delivery_path
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return DocsDeliveryResult.from_dict(data)


def persist_docs_delivery(ctx: RunContext, result: DocsDeliveryResult) -> None:
    payload = {
        "product_id": ctx.product_id,
        "iso_week": ctx.iso_week,
        **result.to_dict(),
    }
    ctx.docs_delivery_path.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
