"""
Kanboard Client Module

JSON-RPC client for interacting with Kanboard API.
"""
from .client import KanboardClient
from .exceptions import (
    KanboardError,
    AuthenticationError,
    NotFoundError,
    TimeoutError,
)

__all__ = [
    'KanboardClient',
    'KanboardError',
    'AuthenticationError',
    'NotFoundError',
    'TimeoutError',
]
