from __future__ import annotations

import json
import re
from typing import Any


class LlmParseError(ValueError):
    pass


def parse_theme_response(raw: str) -> dict[str, Any]:
    data = _extract_json(raw)
    label = str(data.get("label", "")).strip()
    summary = str(data.get("summary", "")).strip()
    actions_raw = data.get("actions") or []
    if not label or not summary:
        raise LlmParseError("missing label or summary in LLM JSON")
    actions = [str(a).strip() for a in actions_raw if str(a).strip()]
    if not actions:
        actions = ["Review cluster feedback in product backlog."]
    return {"label": label, "summary": summary, "actions": actions[:5]}


def _extract_json(raw: str) -> dict[str, Any]:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LlmParseError(f"invalid JSON from LLM: {exc}") from exc
    if not isinstance(data, dict):
        raise LlmParseError("LLM JSON must be an object")
    return data
