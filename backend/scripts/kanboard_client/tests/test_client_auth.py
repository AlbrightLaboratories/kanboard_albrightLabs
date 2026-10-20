"""
Test KC-01: JSON-RPC client connects to Kanboard API and authenticates.

TDD Phase: RED - This test must fail before implementation.
"""
import pytest
from unittest.mock import patch, MagicMock
import httpx


class TestKanboardClientAuth:
    """Tests for Kanboard JSON-RPC client authentication."""

    def test_client_connects_with_valid_credentials(self):
        """KC-01a: Client connects successfully with valid API credentials."""
        from kanboard_client.client import KanboardClient

        client = KanboardClient(
            url="http://kanboard.local/jsonrpc.php",
            username="admin",
            api_token="test-token-123"
        )

        assert client.url == "http://kanboard.local/jsonrpc.php"
        assert client.username == "admin"
        assert client.api_token == "test-token-123"
        assert client.is_configured is True

    def test_client_authenticates_via_json_rpc(self):
        """KC-01b: Client authenticates using JSON-RPC protocol."""
        from kanboard_client.client import KanboardClient

        with patch('httpx.Client.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "id": 1,
                "result": True
            }
            mock_post.return_value = mock_response

            client = KanboardClient(
                url="http://kanboard.local/jsonrpc.php",
                username="admin",
                api_token="test-token-123"
            )

            result = client.authenticate()

            assert result is True
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            # Verify JSON-RPC format
            assert call_args.kwargs.get('json', {}).get('jsonrpc') == '2.0'

    def test_client_fails_with_invalid_credentials(self):
        """KC-01c: Client raises AuthenticationError for invalid credentials."""
        from kanboard_client.client import KanboardClient
        from kanboard_client.exceptions import AuthenticationError

        with patch('httpx.Client.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "id": 1,
                "error": {"code": -32600, "message": "Access denied"}
            }
            mock_post.return_value = mock_response

            client = KanboardClient(
                url="http://kanboard.local/jsonrpc.php",
                username="admin",
                api_token="wrong-token"
            )

            with pytest.raises(AuthenticationError) as exc_info:
                client.authenticate()

            assert "Access denied" in str(exc_info.value)

    def test_client_uses_basic_auth_header(self):
        """KC-01d: Client sends Basic Auth header with username:token."""
        from kanboard_client.client import KanboardClient
        import base64

        with patch('httpx.Client.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "id": 1,
                "result": True
            }
            mock_post.return_value = mock_response

            client = KanboardClient(
                url="http://kanboard.local/jsonrpc.php",
                username="admin",
                api_token="test-token-123"
            )

            client.authenticate()

            call_args = mock_post.call_args
            headers = call_args.kwargs.get('headers', {})
            auth_header = headers.get('Authorization', '')

            # Verify Basic Auth format
            assert auth_header.startswith('Basic ')
            encoded = auth_header.replace('Basic ', '')
            decoded = base64.b64decode(encoded).decode('utf-8')
            assert decoded == "admin:test-token-123"

    def test_client_from_env_vars(self):
        """KC-01e: Client can be configured from environment variables."""
        from kanboard_client.client import KanboardClient
        import os

        with patch.dict(os.environ, {
            'KANBOARD_URL': 'http://env-kanboard.local/jsonrpc.php',
            'KANBOARD_USERNAME': 'env-user',
            'KANBOARD_API_TOKEN': 'env-token-456'
        }):
            client = KanboardClient.from_env()

            assert client.url == 'http://env-kanboard.local/jsonrpc.php'
            assert client.username == 'env-user'
            assert client.api_token == 'env-token-456'
