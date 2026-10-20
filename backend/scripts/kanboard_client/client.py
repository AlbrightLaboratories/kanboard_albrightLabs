"""
Kanboard JSON-RPC Client

Provides authenticated access to Kanboard API via JSON-RPC protocol.
"""
from __future__ import annotations

import base64
import os
from typing import Any

import httpx

from .exceptions import AuthenticationError, KanboardError


class KanboardClient:
    """JSON-RPC client for Kanboard API."""

    def __init__(
        self,
        url: str,
        username: str,
        api_token: str,
        timeout: float = 30.0
    ):
        """
        Initialize Kanboard client.

        Args:
            url: Kanboard JSON-RPC endpoint (e.g., http://kanboard/jsonrpc.php)
            username: API username
            api_token: API token for authentication
            timeout: Request timeout in seconds
        """
        self.url = url
        self.username = username
        self.api_token = api_token
        self.timeout = timeout
        self._request_id = 0
        self._http_client: httpx.Client | None = None

    @classmethod
    def from_env(cls) -> KanboardClient:
        """
        Create client from environment variables.

        Environment variables:
            KANBOARD_URL: JSON-RPC endpoint URL
            KANBOARD_USERNAME: API username
            KANBOARD_API_TOKEN: API token

        Returns:
            Configured KanboardClient instance
        """
        url = os.environ.get('KANBOARD_URL', '')
        username = os.environ.get('KANBOARD_USERNAME', '')
        api_token = os.environ.get('KANBOARD_API_TOKEN', '')

        return cls(url=url, username=username, api_token=api_token)

    @property
    def is_configured(self) -> bool:
        """Check if client has all required configuration."""
        return bool(self.url and self.username and self.api_token)

    @property
    def _auth_header(self) -> str:
        """Generate Basic Auth header value."""
        credentials = f"{self.username}:{self.api_token}"
        encoded = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        return f"Basic {encoded}"

    def _get_client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.Client(timeout=self.timeout)
        return self._http_client

    def _next_request_id(self) -> int:
        """Generate next JSON-RPC request ID."""
        self._request_id += 1
        return self._request_id

    def _call(self, method: str, **params: Any) -> Any:
        """
        Make JSON-RPC call to Kanboard API.

        Args:
            method: JSON-RPC method name
            **params: Method parameters

        Returns:
            Result from JSON-RPC response

        Raises:
            AuthenticationError: If authentication fails
            KanboardError: For other API errors
        """
        payload = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": method,
            "params": params
        }

        headers = {
            "Authorization": self._auth_header,
            "Content-Type": "application/json"
        }

        client = self._get_client()
        response = client.post(self.url, json=payload, headers=headers)

        if response.status_code == 401:
            data = response.json()
            error_msg = data.get('error', {}).get('message', 'Access denied')
            raise AuthenticationError(error_msg)

        data = response.json()

        if 'error' in data:
            error = data['error']
            raise KanboardError(
                message=error.get('message', 'Unknown error'),
                code=error.get('code')
            )

        return data.get('result')

    def authenticate(self) -> bool:
        """
        Verify authentication with Kanboard API.

        Returns:
            True if authentication succeeds

        Raises:
            AuthenticationError: If authentication fails
        """
        result = self._call("getMe")
        return result is not None

    def close(self) -> None:
        """Close HTTP client connection."""
        if self._http_client:
            self._http_client.close()
            self._http_client = None

    def __enter__(self) -> KanboardClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
