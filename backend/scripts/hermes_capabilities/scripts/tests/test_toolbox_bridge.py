"""
Tests for ToolboxBridge - HC-01 to HC-10.

TDD: Write failing tests first.
"""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from scripts.hermes_capabilities.scripts.toolbox_bridge import (
    ToolboxBridge,
    MCPTool,
    ToolCapability,
)


class TestToolboxBridge:
    """Tests for ToolboxBridge connecting Hermes to mcp-hub."""

    @pytest.fixture
    def bridge(self) -> ToolboxBridge:
        return ToolboxBridge()

    # HC-01: ToolboxBridge connects to mcp-hub
    def test_mcp_hub_url_configured(self, bridge):
        """HC-01: Bridge has mcp-hub URL configured."""
        assert bridge.mcp_hub_url is not None
        assert "mcp-hub" in bridge.mcp_hub_url or "8080" in bridge.mcp_hub_url

    @pytest.mark.asyncio
    async def test_discover_tools_queries_mcp_hub(self, bridge):
        """HC-01: discover_tools queries mcp-hub for available tools."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tools": [
                {"name": "mcp-git", "port": 8070, "status": "running"},
                {"name": "mcp-rag", "port": 8071, "status": "running"},
            ]
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            tools = await bridge.discover_tools()

            assert len(tools) == 2
            assert tools[0].name == "mcp-git"
            assert tools[1].name == "mcp-rag"

    # HC-02: mcp-kubernetes-platform-engineer accessible
    @pytest.mark.asyncio
    async def test_k8s_platform_engineer_accessible(self, bridge):
        """HC-02: mcp-kubernetes-platform-engineer is accessible."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {"pods": ["pod1", "pod2"]},
            "success": True
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await bridge.invoke_tool(
                "mcp-kubernetes-platform-engineer",
                "get_pods",
                {"namespace": "default"}
            )

            assert result["success"] is True
            assert "pods" in result["result"]

    # HC-03: mcp-sequential-thinking accessible
    @pytest.mark.asyncio
    async def test_sequential_thinking_accessible(self, bridge):
        """HC-03: mcp-sequential-thinking is accessible."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {"thought_chain": ["step1", "step2", "conclusion"]},
            "success": True
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await bridge.invoke_tool(
                "mcp-sequential-thinking",
                "reason",
                {"prompt": "Analyze this problem"}
            )

            assert result["success"] is True
            assert "thought_chain" in result["result"]

    # HC-04: mcp-rag accessible
    @pytest.mark.asyncio
    async def test_rag_accessible(self, bridge):
        """HC-04: mcp-rag is accessible for semantic search."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {"matches": [{"file": "foo.py", "score": 0.95}]},
            "success": True
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await bridge.invoke_tool(
                "mcp-rag",
                "search",
                {"query": "authentication handler"}
            )

            assert result["success"] is True
            assert "matches" in result["result"]

    # HC-05: tdd-mcp accessible
    @pytest.mark.asyncio
    async def test_tdd_mcp_accessible(self, bridge):
        """HC-05: tdd-mcp is accessible for TDD workflow."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {"test_file": "test_foo.py", "status": "red"},
            "success": True
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await bridge.invoke_tool(
                "tdd-mcp",
                "create_failing_test",
                {"description": "test user login"}
            )

            assert result["success"] is True
            assert result["result"]["status"] == "red"

    # HC-06: mcp-project-indexer accessible
    @pytest.mark.asyncio
    async def test_project_indexer_accessible(self, bridge):
        """HC-06: mcp-project-indexer is accessible."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {"modules": ["auth", "api", "db"]},
            "success": True
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await bridge.invoke_tool(
                "mcp-project-indexer",
                "list_modules",
                {"repo": "kanboard_albrightLabs"}
            )

            assert result["success"] is True
            assert "modules" in result["result"]

    # HC-07: mcp-merge-resolver accessible
    @pytest.mark.asyncio
    async def test_merge_resolver_accessible(self, bridge):
        """HC-07: mcp-merge-resolver is accessible."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {"resolved": True, "strategy": "ours"},
            "success": True
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await bridge.invoke_tool(
                "mcp-merge-resolver",
                "resolve",
                {"file": "foo.py", "conflict": "<<<<<<< HEAD..."}
            )

            assert result["success"] is True
            assert result["result"]["resolved"] is True

    # HC-08: mcp-refactor accessible
    @pytest.mark.asyncio
    async def test_refactor_accessible(self, bridge):
        """HC-08: mcp-refactor is accessible."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {"changes": [{"file": "foo.py", "diff": "+new_code"}]},
            "success": True
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await bridge.invoke_tool(
                "mcp-refactor",
                "rename_function",
                {"old_name": "foo", "new_name": "bar"}
            )

            assert result["success"] is True
            assert "changes" in result["result"]

    # HC-09: Tool discovery by capability
    @pytest.mark.asyncio
    async def test_discover_by_capability(self, bridge):
        """HC-09: Hermes queries mcp-hub for tools by capability."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tools": [
                {"name": "mcp-pytest", "capabilities": ["testing"]},
                {"name": "tdd-mcp", "capabilities": ["testing", "tdd"]},
            ]
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            tools = await bridge.discover_by_capability(ToolCapability.TESTING)

            assert len(tools) == 2
            assert all("testing" in t.capabilities for t in tools)

    # HC-10: Tool invocation with auth
    @pytest.mark.asyncio
    async def test_invoke_with_auth(self):
        """HC-10: Tool invocation includes proper auth headers."""
        # Create bridge with API key
        bridge_with_key = ToolboxBridge(api_key="test-api-key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": {}, "success": True}

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            await bridge_with_key.invoke_tool("mcp-git", "status", {})

            call_args = mock_instance.post.call_args
            headers = call_args.kwargs.get("headers", {})
            assert "Authorization" in headers or "X-API-Key" in headers

    # Error handling
    @pytest.mark.asyncio
    async def test_invoke_tool_handles_timeout(self, bridge):
        """Tool invocation handles timeout gracefully."""
        import httpx

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.side_effect = httpx.TimeoutException("Timeout")
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await bridge.invoke_tool("mcp-git", "status", {})

            assert result["success"] is False
            assert "timeout" in result.get("error", "").lower()

    @pytest.mark.asyncio
    async def test_invoke_tool_handles_connection_error(self, bridge):
        """Tool invocation handles connection error gracefully."""
        import httpx

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.side_effect = httpx.ConnectError("Connection refused")
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await bridge.invoke_tool("mcp-git", "status", {})

            assert result["success"] is False
            assert "connection" in result.get("error", "").lower()
