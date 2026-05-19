from __future__ import annotations

import logging

from pulse_agent.audit.logger import McpSmokeResult
from pulse_agent.config.loader import AppConfig
from pulse_agent.phases.phase_04_docs_mcp.client import WorkspaceHttpClient
from pulse_agent.phases.phase_04_docs_mcp.service import workspace_base_url, _timeout_seconds

logger = logging.getLogger(__name__)


def run_workspace_smoke(config: AppConfig) -> list[McpSmokeResult]:
    """Health-check the deployed Google workspace HTTP MCP server."""
    base = workspace_base_url(config)
    client = WorkspaceHttpClient(base, timeout_seconds=_timeout_seconds(config))
    try:
        data = client.health_check()
        ok = bool(data.get("credentials_ready")) and bool(data.get("token_configured"))
        return [
            McpSmokeResult(
                server="google_workspace",
                ok=ok,
                tool_count=2,
                tools=["append_to_doc", "create_email_draft"],
                error=None if ok else f"health: {data}",
            )
        ]
    except Exception as exc:
        logger.warning("Workspace MCP smoke failed: %s", exc)
        return [
            McpSmokeResult(
                server="google_workspace",
                ok=False,
                error=str(exc),
            )
        ]
