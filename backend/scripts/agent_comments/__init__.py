"""
Agent Comments Module

Enables AI agents to respond to @mentions in story comments.
When users mention @claude, @gemini, or other agents, this module:
1. Detects the mention and extracts context
2. Routes to the appropriate agent
3. Posts agent responses back as comments
4. Handles sandbox execution requests
5. Broadcasts updates via WebSocket
"""

from .mention_parser import parse_mentions, extract_agent_name
from .context_extractor import extract_comment_context
from .response_handler import post_agent_response
from .execution_handler import (
    parse_execution_request,
    trigger_sandbox_execution,
    handle_execution_result,
)
from .websocket_broadcaster import broadcast_agent_response

__all__ = [
    "parse_mentions",
    "extract_agent_name",
    "extract_comment_context",
    "post_agent_response",
    "parse_execution_request",
    "trigger_sandbox_execution",
    "handle_execution_result",
    "broadcast_agent_response",
]
