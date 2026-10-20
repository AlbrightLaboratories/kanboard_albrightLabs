"""
Test WR-16: MCP adapter wraps Claude Code via MCP protocol.
"""
import pytest
from unittest.mock import patch, MagicMock


class TestMCPAdapter:
    """Tests for MCP adapter."""

    def test_send_prompt_success(self):
        """WR-16a: Send prompt calls MCP tools/call."""
        from worker_registry.llm_adapters import MCPAdapter

        adapter = MCPAdapter(endpoint="http://localhost:3000/mcp")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "content": [
                    {"type": "text", "text": "Task completed successfully"}
                ]
            }
        }

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value.__enter__.return_value = mock_instance
            mock_instance.post.return_value = mock_response

            result = adapter.send_prompt("Complete this task")

            assert result["content"] == "Task completed successfully"
            assert result["success"] is True

    def test_call_tool_success(self):
        """WR-16b: Can call specific MCP tools."""
        from worker_registry.llm_adapters import MCPAdapter

        adapter = MCPAdapter(endpoint="http://localhost:3000/mcp")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"status": "ok", "data": {"key": "value"}}
        }

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value.__enter__.return_value = mock_instance
            mock_instance.post.return_value = mock_response

            result = adapter.call_tool("custom_tool", {"arg1": "value1"})

            assert result["status"] == "ok"
            assert result["data"]["key"] == "value"

    def test_auth_header_included(self):
        """WR-16c: Auth credentials sent as Bearer token."""
        from worker_registry.llm_adapters import MCPAdapter

        adapter = MCPAdapter(
            endpoint="http://localhost:3000/mcp",
            auth_credentials="mcp-token"
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"content": []}
        }

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value.__enter__.return_value = mock_instance
            mock_instance.post.return_value = mock_response

            adapter.send_prompt("Test")

            call_args = mock_instance.post.call_args
            headers = call_args[1]["headers"]
            assert headers["Authorization"] == "Bearer mcp-token"

    def test_health_check_uses_tools_list(self):
        """WR-16d: Health check uses tools/list method."""
        from worker_registry.llm_adapters import MCPAdapter

        adapter = MCPAdapter(endpoint="http://localhost:3000/mcp")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"tools": []}
        }

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value.__enter__.return_value = mock_instance
            mock_instance.post.return_value = mock_response

            assert adapter.health_check() is True

    def test_list_tools(self):
        """WR-16e: List tools returns available MCP tools."""
        from worker_registry.llm_adapters import MCPAdapter

        adapter = MCPAdapter(endpoint="http://localhost:3000/mcp")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tools": [
                    {"name": "execute_task", "description": "Execute a task"},
                    {"name": "read_file", "description": "Read a file"}
                ]
            }
        }

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value.__enter__.return_value = mock_instance
            mock_instance.post.return_value = mock_response

            tools = adapter.list_tools()

            assert len(tools) == 2
            assert tools[0]["name"] == "execute_task"

    def test_error_handling(self):
        """WR-16f: MCP errors are properly raised."""
        from worker_registry.llm_adapters import MCPAdapter

        adapter = MCPAdapter(endpoint="http://localhost:3000/mcp")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {"code": -32600, "message": "Invalid request"}
        }

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value.__enter__.return_value = mock_instance
            mock_instance.post.return_value = mock_response

            with pytest.raises(RuntimeError, match="MCP error"):
                adapter.send_prompt("Test")
