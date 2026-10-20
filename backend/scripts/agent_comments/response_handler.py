"""
Response Handler - Posts agent responses back as comments

Implements AIC-03: Agent response is posted back as comment with agent badge
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import json


@dataclass
class AgentResponse:
    """Represents an agent's response to a comment."""
    agent_id: str
    agent_name: str
    content: str
    story_id: str
    in_reply_to: str
    has_execution_request: bool = False
    execution_details: Optional[Dict[str, Any]] = None
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


# Marker for execution requests
EXECUTION_MARKER = "[READY_TO_EXECUTE]"


def create_agent_response(
    agent_id: str,
    agent_name: str,
    content: str,
    story_id: str,
    in_reply_to: str,
) -> AgentResponse:
    """
    Create an agent response object.

    Args:
        agent_id: Unique agent identifier
        agent_name: Human-readable agent name
        content: Response content
        story_id: Story being responded to
        in_reply_to: Comment ID being replied to

    Returns:
        AgentResponse object
    """
    has_execution = EXECUTION_MARKER in content
    execution_details = None

    if has_execution:
        execution_details = parse_execution_details(content)

    return AgentResponse(
        agent_id=agent_id,
        agent_name=agent_name,
        content=content,
        story_id=story_id,
        in_reply_to=in_reply_to,
        has_execution_request=has_execution,
        execution_details=execution_details,
    )


def parse_execution_details(content: str) -> Optional[Dict[str, Any]]:
    """
    Parse execution details from agent response.

    Looks for JSON block after EXECUTION_MARKER.

    Args:
        content: Agent response content

    Returns:
        Parsed execution details or None
    """
    if EXECUTION_MARKER not in content:
        return None

    # Look for JSON block after marker
    marker_pos = content.find(EXECUTION_MARKER)
    after_marker = content[marker_pos + len(EXECUTION_MARKER):]

    # Try to find JSON block
    json_start = after_marker.find("{")
    if json_start == -1:
        return {"type": "simple", "command": after_marker.strip()}

    # Find matching closing brace
    brace_count = 0
    json_end = json_start

    for i, char in enumerate(after_marker[json_start:]):
        if char == "{":
            brace_count += 1
        elif char == "}":
            brace_count -= 1
            if brace_count == 0:
                json_end = json_start + i + 1
                break

    try:
        json_str = after_marker[json_start:json_end]
        return json.loads(json_str)
    except json.JSONDecodeError:
        return {"type": "simple", "command": after_marker.strip()}


def format_agent_comment(response: AgentResponse) -> Dict[str, Any]:
    """
    Format agent response as a comment payload.

    Args:
        response: The agent response

    Returns:
        Comment payload for API
    """
    return {
        "story_id": response.story_id,
        "content": response.content,
        "author": f"{response.agent_name} (Agent)",
        "is_agent_response": True,
        "agent_id": response.agent_id,
        "in_reply_to": response.in_reply_to,
        "created_at": response.created_at,
        "metadata": {
            "has_execution_request": response.has_execution_request,
            "execution_details": response.execution_details,
        },
    }


async def post_agent_response(
    response: AgentResponse,
    api_client: Any,
) -> Dict[str, Any]:
    """
    Post agent response as a comment via API.

    Args:
        response: The agent response to post
        api_client: Kanboard API client

    Returns:
        API response with comment ID
    """
    payload = format_agent_comment(response)

    # Post to Kanboard API
    result = await api_client.create_comment(
        story_id=response.story_id,
        content=payload["content"],
        author=payload["author"],
        metadata=payload["metadata"],
    )

    return {
        "success": True,
        "comment_id": result.get("id"),
        "has_execution_request": response.has_execution_request,
    }


def add_agent_badge(content: str, agent_name: str) -> str:
    """
    Add agent badge/prefix to response content.

    Args:
        content: Original response content
        agent_name: Name of the responding agent

    Returns:
        Content with agent badge prepended
    """
    badge = f"🤖 **{agent_name}** responding:\n\n"
    return badge + content
