"""
ToolboxBridge - Connect Hermes to mcp-hub for dynamic MCP tool discovery.

Provides access to corey-toolbox MCPs:
- mcp-kubernetes-platform-engineer (cluster RCA, self-healing)
- mcp-sequential-thinking (CoT reasoning)
- mcp-rag (semantic search)
- tdd-mcp (TDD workflow)
- mcp-project-indexer (module mapping)
- mcp-merge-resolver (merge conflicts)
- mcp-refactor (safe refactoring)
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class ToolCapability(Enum):
    """Tool capability categories for discovery."""
    TESTING = "testing"
    KUBERNETES = "kubernetes"
    GIT = "git"
    REASONING = "reasoning"
    SEARCH = "search"
    REFACTORING = "refactoring"
    CODE_QUALITY = "code_quality"
    DATABASE = "database"


@dataclass
class MCPTool:
    """Represents an MCP tool from the registry."""
    name: str
    port: int
    status: str = "unknown"
    capabilities: List[str] = field(default_factory=list)
    endpoint: Optional[str] = None


class ToolboxBridge:
    """
    Bridge connecting Hermes to mcp-hub for dynamic tool discovery.

    Queries mcp-hub for available tools and invokes them via HTTP.
    """

    def __init__(
        self,
        mcp_hub_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout_s: float = 30.0,
    ):
        """
        Initialize ToolboxBridge.

        Args:
            mcp_hub_url: URL of mcp-hub service
            api_key: API key for tool authentication
            timeout_s: Default timeout for tool invocations
        """
        self.mcp_hub_url = mcp_hub_url or os.getenv(
            "MCP_HUB_URL",
            "http://mcp-hub.corey-coder.svc.cluster.local:8080"
        )
        self._api_key = api_key or os.getenv("MCP_API_KEY", "")
        self._timeout_s = timeout_s
        self._tool_cache: Dict[str, MCPTool] = {}

    async def discover_tools(self) -> List[MCPTool]:
        """
        Discover all available MCP tools from mcp-hub.

        Returns:
            List of available MCPTool instances
        """
        try:
            async with httpx.AsyncClient(timeout=self._timeout_s) as client:
                r = await client.get(
                    f"{self.mcp_hub_url}/tools",
                    headers=self._auth_headers(),
                )

                if r.status_code != 200:
                    logger.warning(f"mcp-hub returned {r.status_code}")
                    return []

                data = r.json()
                tools = []
                for t in data.get("tools", []):
                    tool = MCPTool(
                        name=t.get("name", ""),
                        port=t.get("port", 0),
                        status=t.get("status", "unknown"),
                        capabilities=t.get("capabilities", []),
                        endpoint=t.get("endpoint"),
                    )
                    tools.append(tool)
                    self._tool_cache[tool.name] = tool

                logger.info(f"Discovered {len(tools)} MCP tools")
                return tools

        except httpx.TimeoutException:
            logger.warning("Timeout discovering tools from mcp-hub")
            return []
        except httpx.ConnectError as e:
            logger.warning(f"Connection error to mcp-hub: {e}")
            return []
        except Exception as e:
            logger.error(f"Error discovering tools: {e}")
            return []

    async def discover_by_capability(
        self,
        capability: ToolCapability
    ) -> List[MCPTool]:
        """
        Discover tools matching a specific capability.

        Args:
            capability: The capability to filter by

        Returns:
            List of tools with the requested capability
        """
        try:
            async with httpx.AsyncClient(timeout=self._timeout_s) as client:
                r = await client.get(
                    f"{self.mcp_hub_url}/tools",
                    params={"capability": capability.value},
                    headers=self._auth_headers(),
                )

                if r.status_code != 200:
                    logger.warning(f"mcp-hub returned {r.status_code}")
                    return []

                data = r.json()
                tools = []
                for t in data.get("tools", []):
                    caps = t.get("capabilities", [])
                    if capability.value in caps:
                        tool = MCPTool(
                            name=t.get("name", ""),
                            port=t.get("port", 0),
                            status=t.get("status", "unknown"),
                            capabilities=caps,
                            endpoint=t.get("endpoint"),
                        )
                        tools.append(tool)

                return tools

        except Exception as e:
            logger.error(f"Error discovering tools by capability: {e}")
            return []

    async def invoke_tool(
        self,
        tool_name: str,
        method: str,
        params: Dict[str, Any],
        timeout_s: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Invoke an MCP tool method.

        Args:
            tool_name: Name of the tool (e.g., "mcp-git")
            method: Method to invoke (e.g., "status")
            params: Parameters for the method
            timeout_s: Optional timeout override

        Returns:
            Dict with 'success', 'result', and optionally 'error'
        """
        timeout = timeout_s or self._timeout_s

        # Get tool endpoint
        endpoint = self._get_tool_endpoint(tool_name)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                payload = {
                    "method": method,
                    "params": params,
                }

                r = await client.post(
                    endpoint,
                    json=payload,
                    headers=self._auth_headers(),
                )

                if r.status_code >= 300:
                    return {
                        "success": False,
                        "error": f"HTTP {r.status_code}: {r.text[:200]}",
                        "result": None,
                    }

                data = r.json()
                return {
                    "success": data.get("success", True),
                    "result": data.get("result", data),
                    "error": data.get("error"),
                }

        except httpx.TimeoutException:
            logger.warning(f"Timeout invoking {tool_name}.{method}")
            return {
                "success": False,
                "error": "Timeout: tool invocation timed out",
                "result": None,
            }
        except httpx.ConnectError as e:
            logger.warning(f"Connection error invoking {tool_name}: {e}")
            return {
                "success": False,
                "error": f"Connection error: {e}",
                "result": None,
            }
        except Exception as e:
            logger.error(f"Error invoking {tool_name}.{method}: {e}")
            return {
                "success": False,
                "error": str(e),
                "result": None,
            }

    def _get_tool_endpoint(self, tool_name: str) -> str:
        """Get the HTTP endpoint for a tool."""
        # Check cache first
        if tool_name in self._tool_cache:
            tool = self._tool_cache[tool_name]
            if tool.endpoint:
                return tool.endpoint
            return f"http://{tool_name}.corey-coder.svc.cluster.local:{tool.port}/invoke"

        # Default endpoint pattern
        return f"http://{tool_name}.corey-coder.svc.cluster.local:8080/invoke"

    def _auth_headers(self) -> Dict[str, str]:
        """Build authentication headers."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "hermes-toolbox-bridge/1.0",
        }
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
            headers["X-API-Key"] = self._api_key
        return headers

    async def health_check(self) -> bool:
        """Check if mcp-hub is reachable."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(f"{self.mcp_hub_url}/health")
                return r.status_code == 200
        except Exception:
            return False
