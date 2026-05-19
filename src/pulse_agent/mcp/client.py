from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncIterator

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from pulse_agent.config.loader import McpServerConfig

logger = logging.getLogger(__name__)


class McpConnectionError(Exception):
    """Raised when MCP server connection or tool listing fails."""


@dataclass
class McpToolInfo:
    name: str
    description: str | None = None


class McpClient:
    """MCP host client for a single server (stdio transport)."""

    def __init__(self, server_config: McpServerConfig) -> None:
        self._config = server_config

    @asynccontextmanager
    async def session(self) -> AsyncIterator[ClientSession]:
        if self._config.transport != "stdio":
            raise McpConnectionError(f"Unsupported transport: {self._config.transport}")

        params = StdioServerParameters(
            command=self._config.command,
            args=self._config.args,
            env=None,
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session

    async def list_tools(self) -> list[McpToolInfo]:
        try:
            async with self.session() as session:
                result = await session.list_tools()
                return [
                    McpToolInfo(name=t.name, description=t.description)
                    for t in result.tools
                ]
        except Exception as exc:
            raise McpConnectionError(
                f"MCP server {self._config.name!r}: {exc}"
            ) from exc

    async def invoke_tool(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        async with self.session() as session:
            return await session.call_tool(name, arguments or {})
