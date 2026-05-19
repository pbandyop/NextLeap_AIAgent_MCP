import pytest

from pulse_agent.config.loader import load_config
from pulse_agent.mcp.client import McpClient, McpConnectionError


@pytest.mark.integration
@pytest.mark.asyncio
async def test_mcp_docs_lists_tools(project_root):
    config = load_config(project_root)
    server = config.mcp_servers.get("google_docs")
    if not server or not server.enabled:
        pytest.skip("google_docs MCP not configured")
    client = McpClient(server)
    try:
        tools = await client.list_tools()
    except McpConnectionError as exc:
        pytest.skip(f"MCP docs server unavailable: {exc}")
    assert len(tools) > 0
