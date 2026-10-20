"""
Context Extractor - Extracts full context for agent processing

Implements AIC-02: Agent receives comment context with story details
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class StoryContext:
    """Full context about a story for agent processing."""
    story_id: str
    title: str
    description: str
    column: str
    assignee: Optional[str]
    labels: List[str]
    priority: Optional[str]
    linked_repo: Optional[str]
    linked_branch: Optional[str]
    acceptance_criteria: List[str]
    subtasks: List[Dict[str, Any]]
    dependencies: List[str]
    skill_progress: Dict[str, str]


@dataclass
class CommentContext:
    """Full context about a comment and its story."""
    comment_id: str
    comment_text: str
    author: str
    created_at: str
    story: StoryContext
    previous_comments: List[Dict[str, str]]
    mentioned_agent: str
    thread_history: List[str] = field(default_factory=list)


def extract_comment_context(
    comment_id: str,
    comment_text: str,
    author: str,
    story_data: Dict[str, Any],
    previous_comments: List[Dict[str, Any]],
    mentioned_agent: str,
) -> CommentContext:
    """
    Extract full context for agent processing.

    Args:
        comment_id: The ID of the triggering comment
        comment_text: The text of the comment
        author: Who wrote the comment
        story_data: Full story data from API
        previous_comments: Previous comments in thread
        mentioned_agent: Which agent was mentioned

    Returns:
        CommentContext with all relevant information
    """
    # Extract acceptance criteria from description
    acceptance_criteria = extract_acceptance_criteria(
        story_data.get("description", "")
    )

    # Build story context
    story = StoryContext(
        story_id=str(story_data.get("id", "")),
        title=story_data.get("title", ""),
        description=story_data.get("description", ""),
        column=story_data.get("column", ""),
        assignee=story_data.get("assignee"),
        labels=story_data.get("labels", []),
        priority=story_data.get("priority"),
        linked_repo=story_data.get("linked_repo"),
        linked_branch=story_data.get("linked_branch"),
        acceptance_criteria=acceptance_criteria,
        subtasks=story_data.get("subtasks", []),
        dependencies=story_data.get("dependencies", []),
        skill_progress=story_data.get("skill_progress", {}),
    )

    # Format previous comments for thread history
    thread_history = [
        f"{c.get('author', 'Unknown')}: {c.get('content', '')}"
        for c in previous_comments[-10:]  # Last 10 comments
    ]

    # Build simplified previous comments
    simple_comments = [
        {
            "id": c.get("id", ""),
            "author": c.get("author", ""),
            "content": c.get("content", "")[:500],  # Truncate long comments
            "is_agent": c.get("is_agent_response", False),
        }
        for c in previous_comments
    ]

    return CommentContext(
        comment_id=comment_id,
        comment_text=comment_text,
        author=author,
        created_at=datetime.utcnow().isoformat(),
        story=story,
        previous_comments=simple_comments,
        mentioned_agent=mentioned_agent,
        thread_history=thread_history,
    )


def extract_acceptance_criteria(description: str) -> List[str]:
    """
    Extract acceptance criteria from story description.

    Looks for:
    - Lines starting with "- [ ]" or "- [x]"
    - Lines under "## Acceptance Criteria" header
    - Lines starting with "AC-" prefix

    Args:
        description: Story description text

    Returns:
        List of acceptance criteria strings
    """
    criteria = []
    lines = description.split("\n")
    in_ac_section = False

    for line in lines:
        line = line.strip()

        # Check for AC section header
        if "acceptance criteria" in line.lower():
            in_ac_section = True
            continue

        # Check for end of AC section
        if in_ac_section and line.startswith("##"):
            in_ac_section = False
            continue

        # Extract checkbox items
        if line.startswith("- [ ]") or line.startswith("- [x]"):
            criteria.append(line[5:].strip())
            continue

        # Extract AC-prefixed items
        if line.upper().startswith("AC-"):
            criteria.append(line)
            continue

        # Extract items in AC section
        if in_ac_section and line.startswith("-"):
            criteria.append(line[1:].strip())

    return criteria


def format_context_for_agent(context: CommentContext) -> str:
    """
    Format context into a prompt for the agent.

    Args:
        context: The extracted comment context

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        f"## Story: {context.story.title}",
        f"**ID**: {context.story.story_id}",
        f"**Column**: {context.story.column}",
        f"**Priority**: {context.story.priority or 'Not set'}",
        "",
        "### Description",
        context.story.description[:2000],  # Truncate long descriptions
        "",
    ]

    if context.story.acceptance_criteria:
        prompt_parts.append("### Acceptance Criteria")
        for ac in context.story.acceptance_criteria:
            prompt_parts.append(f"- {ac}")
        prompt_parts.append("")

    if context.story.linked_repo:
        prompt_parts.append(f"### Repository")
        prompt_parts.append(f"- Repo: {context.story.linked_repo}")
        if context.story.linked_branch:
            prompt_parts.append(f"- Branch: {context.story.linked_branch}")
        prompt_parts.append("")

    if context.thread_history:
        prompt_parts.append("### Recent Comments")
        for comment in context.thread_history[-5:]:
            prompt_parts.append(f"> {comment}")
        prompt_parts.append("")

    prompt_parts.append("### User Request")
    prompt_parts.append(f"**{context.author}**: {context.comment_text}")

    return "\n".join(prompt_parts)
