"""
MCP Adapter

Adapter for MCP-based workers (Claude Code via MCP protocol).
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import httpx

from .base import BaseLLMAdapter


class MCPAdapter(BaseLLMAdapter):
    """Adapter for MCP protocol workers."""

    def __init__(
        self,
        endpoint: str,
        auth_credentials: Optional[str] = None,
        timeout: float = 300.0
    ):
        """
        Initialize MCP adapter.

        Args:
            endpoint: MCP server endpoint
            auth_credentials: API key or token
            timeout: Request timeout in seconds (longer for MCP)
        """
        super().__init__(endpoint, auth_credentials)
        self.timeout = timeout

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with auth if configured."""
        headers = {"Content-Type": "application/json"}
        if self.auth_credentials:
            headers["Authorization"] = f"Bearer {self.auth_credentials}"
        return headers

    def send_prompt(
        self,
        prompt: str,
        model: Optional[str] = None,
        tool: str = "execute_task",
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Send prompt to MCP server.

        Args:
            prompt: The task/prompt text
            model: Not used for MCP
            tool: MCP tool to invoke (default: execute_task)
            **kwargs: Additional tool parameters

        Returns:
            Response dict with 'content' and metadata
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool,
                "arguments": {
                    "prompt": prompt,
                    **kwargs
                }
            }
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    self.endpoint,
                    json=payload,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                data = response.json()

                if "error" in data:
                    raise RuntimeError(f"MCP error: {data['error']}")

                result = data.get("result", {})
                content = result.get("content", [])

                # Extract text content from MCP response
                text_content = ""
                for item in content:
                    if item.get("type") == "text":
                        text_content += item.get("text", "")

                return {
                    "content": text_content,
                    "raw_result": result,
                    "tool": tool,
                    "success": True
                }
        except httpx.TimeoutException as e:
            raise TimeoutError(f"MCP request timed out: {e}")
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"MCP HTTP error: {e.response.status_code}")
        except Exception as e:
            raise RuntimeError(f"MCP error: {e}")

    def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call a specific MCP tool.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool result
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    self.endpoint,
                    json=payload,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                data = response.json()

                if "error" in data:
                    raise RuntimeError(f"MCP tool error: {data['error']}")

                return data.get("result", {})
        except Exception as e:
            raise RuntimeError(f"MCP tool call failed: {e}")

    def health_check(self) -> bool:
        """
        Check if MCP server is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Use tools/list as health check
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            }

            with httpx.Client(timeout=5.0) as client:
                response = client.post(
                    self.endpoint,
                    json=payload,
                    headers=self._get_headers()
                )
                return response.status_code == 200 and "error" not in response.json()
        except Exception:
            return False

    def list_models(self) -> List[str]:
        """
        List available tools (MCP doesn't have models).

        Returns:
            List of tool names
        """
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            }

            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    self.endpoint,
                    json=payload,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                data = response.json()

                tools = data.get("result", {}).get("tools", [])
                return [t.get("name", "") for t in tools]
        except Exception:
            return []

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available MCP tools with full details.

        Returns:
            List of tool definitions
        """
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            }

            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    self.endpoint,
                    json=payload,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                data = response.json()

                return data.get("result", {}).get("tools", [])
        except Exception:
            return []
