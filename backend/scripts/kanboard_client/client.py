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

    def get_columns(self, project_id: int) -> list:
        """
        Get columns for a project.

        Args:
            project_id: Project ID

        Returns:
            List of column dictionaries with id, title, position
        """
        return self._call("getColumns", project_id=project_id)

    def create_story(
        self,
        project_id: int,
        title: str,
        description: str = "",
        column_id: int = None,
        owner_id: int = None,
        priority: int = None,
        tags: list = None,
        **kwargs: Any
    ) -> int:
        """
        Create a new story (task) in Kanboard.

        Args:
            project_id: Project ID to create story in
            title: Story title
            description: Story description (optional)
            column_id: Column ID (defaults to first column/Backlog)
            owner_id: Assignee user ID (optional)
            priority: Priority level (optional)
            tags: List of tag strings (optional)
            **kwargs: Additional task fields

        Returns:
            New story ID

        Raises:
            KanboardError: If story creation fails
        """
        # Build params
        params = {
            "project_id": project_id,
            "title": title,
        }

        if description:
            params["description"] = description

        if column_id is not None:
            params["column_id"] = column_id
        else:
            # Default to first column (Backlog)
            columns = self.get_columns(project_id)
            if columns:
                # Sort by position, take first
                backlog = min(columns, key=lambda c: c.get("position", 0))
                params["column_id"] = backlog["id"]

        if owner_id is not None:
            params["owner_id"] = owner_id

        if priority is not None:
            params["priority"] = priority

        if tags is not None:
            params["tags"] = tags

        # Add any extra kwargs
        params.update(kwargs)

        return self._call("createTask", **params)

    def close(self) -> None:
        """Close HTTP client connection."""
        if self._http_client:
            self._http_client.close()
            self._http_client = None

    def __enter__(self) -> KanboardClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
