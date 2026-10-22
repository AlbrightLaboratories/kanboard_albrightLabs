"""
Request Builder - Builds prompts for Hermes from Kanboard context.

Constructs system and user messages that provide Hermes with:
- Story context (title, description, acceptance criteria)
- Thread history (previous comments)
- The user's mention/question
"""
from __future__ import annotations

from typing import Optional
from dataclasses import dataclass


@dataclass
class StoryContext:
    """Story context for agent processing."""
    story_id: str
    title: str
    description: str
    column: str
    assignee: Optional[str] = None
    acceptance_criteria: Optional[list[str]] = None
    previous_comments: Optional[list[dict]] = None


HERMES_SYSTEM_PROMPT = """You are Hermes, an AI assistant integrated with Kanboard.

When users mention @hermes in comments, you help with:
- Answering questions about the story/task
- Providing code suggestions
- Explaining technical concepts
- Planning implementation approaches

Guidelines:
1. Be concise and helpful
2. Reference the story context when relevant
3. If asked to execute code, explain what you would do
4. Format responses in markdown for readability

You have access to tools for file operations and terminal commands on the Mac Mini."""


def build_simple_prompt(
    user_message: str,
) -> list[dict]:
    """
    Build a simple prompt without story context.

    Args:
        user_message: The user's message mentioning @hermes

    Returns:
        List of messages in OpenAI chat format
    """
    return [
        {"role": "system", "content": HERMES_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]


def build_comment_context_prompt(
    user_message: str,
    story: StoryContext,
    include_thread: bool = True,
) -> list[dict]:
    """
    Build a prompt with full story context.

    Args:
        user_message: The user's comment mentioning @hermes
        story: Story context from Kanboard
        include_thread: Whether to include previous comments

    Returns:
        List of messages in OpenAI chat format
    """
    # Build story context section
    story_section = f"""## Story Context

**Story ID:** {story.story_id}
**Title:** {story.title}
**Column:** {story.column}
**Assignee:** {story.assignee or 'Unassigned'}

### Description
{story.description or 'No description provided.'}
"""

    # Add acceptance criteria if present
    if story.acceptance_criteria:
        ac_list = "\n".join(f"- {ac}" for ac in story.acceptance_criteria)
        story_section += f"""
### Acceptance Criteria
{ac_list}
"""

    # Add thread history if requested and present
    thread_section = ""
    if include_thread and story.previous_comments:
        thread_items = []
        for comment in story.previous_comments[-5:]:  # Last 5 comments
            author = comment.get("author", "Unknown")
            content = comment.get("content", "")
            thread_items.append(f"**{author}:** {content}")
        thread_section = f"""
### Previous Comments
{chr(10).join(thread_items)}
"""

    # Combine system prompt with context
    system_with_context = f"""{HERMES_SYSTEM_PROMPT}

{story_section}
{thread_section}
"""

    return [
        {"role": "system", "content": system_with_context.strip()},
        {"role": "user", "content": user_message},
    ]


def format_agent_response(
    reply: str,
    agent_name: str = "Hermes",
) -> str:
    """
    Format agent reply with badge for posting as comment.

    Args:
        reply: Raw agent response
        agent_name: Name of the responding agent

    Returns:
        Formatted response with agent badge
    """
    return f"🤖 **{agent_name}** responding:\n\n{reply}"
