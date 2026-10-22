"""
Hermes Adapter Module

OpenAI-compatible client for Hermes agent (Mac Mini 172.100.10.21:8642).
Provides retry logic, timeout handling, and context building for Kanboard comments.
"""

from .scripts.hermes_client import (
    HermesResult,
    complete,
    hermes_enabled,
    health_check,
)
from .scripts.request_builder import (
    build_comment_context_prompt,
    build_simple_prompt,
)

__all__ = [
    "HermesResult",
    "complete",
    "hermes_enabled",
    "health_check",
    "build_comment_context_prompt",
    "build_simple_prompt",
]
