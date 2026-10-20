"""
Test AIC-02: Agent receives comment context with story details
"""

import pytest
from ..context_extractor import (
    extract_comment_context,
    extract_acceptance_criteria,
    format_context_for_agent,
    StoryContext,
    CommentContext,
)


@pytest.fixture
def sample_story_data():
    """Sample story data for tests."""
    return {
        "id": "123",
        "title": "Implement login feature",
        "description": """
## Description
Add login functionality to the app.

## Acceptance Criteria
- [ ] User can enter email and password
- [ ] Invalid credentials show error
- [x] Successful login redirects to dashboard
        """,
        "column": "in_progress",
        "assignee": "developer",
        "labels": ["feature", "auth"],
        "priority": "high",
        "linked_repo": "AlbrightLaboratories/app",
        "linked_branch": "feature/login",
        "subtasks": [
            {"id": "1", "title": "Create form", "completed": True},
            {"id": "2", "title": "Add validation", "completed": False},
        ],
        "dependencies": ["story-100"],
        "skill_progress": {
            "plan": "passed",
            "tdd": "in_progress",
        },
    }


@pytest.fixture
def sample_comments():
    """Sample previous comments."""
    return [
        {"id": "c1", "author": "user1", "content": "Started working on this"},
        {"id": "c2", "author": "user2", "content": "Need help with validation"},
    ]


class TestExtractCommentContext:
    """Tests for extract_comment_context function."""

    def test_extracts_basic_info(self, sample_story_data, sample_comments):
        """Basic comment info is extracted."""
        context = extract_comment_context(
            comment_id="c3",
            comment_text="@claude help with tests",
            author="developer",
            story_data=sample_story_data,
            previous_comments=sample_comments,
            mentioned_agent="claude",
        )

        assert context.comment_id == "c3"
        assert context.comment_text == "@claude help with tests"
        assert context.author == "developer"
        assert context.mentioned_agent == "claude"

    def test_extracts_story_context(self, sample_story_data, sample_comments):
        """Story context is fully extracted."""
        context = extract_comment_context(
            comment_id="c3",
            comment_text="@claude help",
            author="dev",
            story_data=sample_story_data,
            previous_comments=sample_comments,
            mentioned_agent="claude",
        )

        story = context.story
        assert story.story_id == "123"
        assert story.title == "Implement login feature"
        assert story.column == "in_progress"
        assert story.assignee == "developer"
        assert story.labels == ["feature", "auth"]
        assert story.priority == "high"
        assert story.linked_repo == "AlbrightLaboratories/app"
        assert story.linked_branch == "feature/login"

    def test_extracts_acceptance_criteria(self, sample_story_data, sample_comments):
        """Acceptance criteria extracted from description."""
        context = extract_comment_context(
            comment_id="c3",
            comment_text="@claude help",
            author="dev",
            story_data=sample_story_data,
            previous_comments=sample_comments,
            mentioned_agent="claude",
        )

        ac = context.story.acceptance_criteria
        assert len(ac) == 3
        assert "User can enter email and password" in ac
        assert "Invalid credentials show error" in ac

    def test_includes_thread_history(self, sample_story_data, sample_comments):
        """Previous comments included in thread history."""
        context = extract_comment_context(
            comment_id="c3",
            comment_text="@claude help",
            author="dev",
            story_data=sample_story_data,
            previous_comments=sample_comments,
            mentioned_agent="claude",
        )

        assert len(context.thread_history) == 2
        assert "user1: Started working on this" in context.thread_history


class TestExtractAcceptanceCriteria:
    """Tests for extract_acceptance_criteria function."""

    def test_checkbox_items(self):
        """Checkbox items are extracted."""
        description = """
- [ ] First AC
- [x] Second AC completed
- [ ] Third AC
        """
        ac = extract_acceptance_criteria(description)

        assert len(ac) == 3
        assert "First AC" in ac
        assert "Second AC completed" in ac

    def test_ac_prefix_items(self):
        """AC-prefixed items are extracted."""
        description = """
AC-01: User can login
AC-02: User can logout
        """
        ac = extract_acceptance_criteria(description)

        assert len(ac) == 2
        assert any("AC-01" in a for a in ac)

    def test_section_header_items(self):
        """Items under AC section header extracted."""
        description = """
## Acceptance Criteria
- Item one
- Item two

## Notes
- Not an AC
        """
        ac = extract_acceptance_criteria(description)

        assert len(ac) == 2
        assert "Item one" in ac
        assert "Not an AC" not in ac


class TestFormatContextForAgent:
    """Tests for format_context_for_agent function."""

    def test_includes_story_title(self, sample_story_data, sample_comments):
        """Formatted context includes story title."""
        context = extract_comment_context(
            comment_id="c3",
            comment_text="@claude help",
            author="dev",
            story_data=sample_story_data,
            previous_comments=sample_comments,
            mentioned_agent="claude",
        )

        formatted = format_context_for_agent(context)

        assert "Implement login feature" in formatted

    def test_includes_user_request(self, sample_story_data, sample_comments):
        """Formatted context includes user request."""
        context = extract_comment_context(
            comment_id="c3",
            comment_text="@claude help with tests",
            author="developer",
            story_data=sample_story_data,
            previous_comments=sample_comments,
            mentioned_agent="claude",
        )

        formatted = format_context_for_agent(context)

        assert "developer" in formatted
        assert "@claude help with tests" in formatted

    def test_includes_repo_info(self, sample_story_data, sample_comments):
        """Formatted context includes repo information."""
        context = extract_comment_context(
            comment_id="c3",
            comment_text="@claude help",
            author="dev",
            story_data=sample_story_data,
            previous_comments=sample_comments,
            mentioned_agent="claude",
        )

        formatted = format_context_for_agent(context)

        assert "AlbrightLaboratories/app" in formatted
        assert "feature/login" in formatted
