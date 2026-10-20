"""
Kanboard Client Exceptions

Custom exceptions for Kanboard API interactions.
"""
from __future__ import annotations

from typing import Optional


class KanboardError(Exception):
    """Base exception for all Kanboard client errors."""

    def __init__(self, message: str, code: Optional[int] = None):
        self.message = message
        self.code = code
        super().__init__(self.message)


class AuthenticationError(KanboardError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, code=401)


class NotFoundError(KanboardError):
    """Raised when a resource is not found (404-equivalent)."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, code=404)


class TimeoutError(KanboardError):
    """Raised when API request times out (retry-able)."""

    def __init__(self, message: str = "Request timed out"):
        super().__init__(message, code=408)
        self.retryable = True
