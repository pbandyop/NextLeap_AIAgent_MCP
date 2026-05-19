from __future__ import annotations

import asyncio
import logging

from pulse_agent.audit.logger import McpSmokeResult
from pulse_agent.config.loader import AppConfig
from pulse_agent.mcp.client import McpClient, McpConnectionError

logger = logging.getLogger(__name__)

SMOKE_SERVER_ORDER = ("google_docs", "gmail")


async def _smoke_one(server_name: str, config: AppConfig) -> McpSmokeResult:
    mcp_cfg = config.mcp_servers.get(server_name)
    if not mcp_cfg or not mcp_cfg.enabled:
        return McpSmokeResult(
            server=server_name,
            ok=False,
            error=f"Server {server_name!r} not configured or disabled",
        )

    client = McpClient(mcp_cfg)
    try:
        tools = await client.list_tools()
        names = [t.name for t in tools]
        ok = len(names) > 0
        return McpSmokeResult(
            server=server_name,
            ok=ok,
            tool_count=len(names),
            tools=names,
            error=None if ok else "tools/list returned empty",
        )
    except McpConnectionError as exc:
        logger.warning("MCP smoke failed for %s: %s", server_name, exc)
        return McpSmokeResult(server=server_name, ok=False, error=str(exc))


async def run_mcp_smoke_async(config: AppConfig) -> list[McpSmokeResult]:
    results = []
    for name in SMOKE_SERVER_ORDER:
        results.append(await _smoke_one(name, config))
    return results


def run_mcp_smoke(config: AppConfig) -> list[McpSmokeResult]:
    return asyncio.run(run_mcp_smoke_async(config))
