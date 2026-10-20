"""
Test DG-06: find_repo() returns repo URL, branch, file paths from story.

TDD Phase: RED -> GREEN
"""
import pytest


class TestFindRepo:
    """Tests for finding repo information from stories."""

    def test_find_repo_returns_repo_info(self):
        """DG-06a: find_repo() returns repo URL, branch, and files."""
        from dependency_graph.graph import DependencyGraph

        graph = DependencyGraph()

        # Register story with repo info
        graph.register_story(
            story_id=1,
            repo_url="https://github.com/org/repo",
            branch="feature/story-1",
            file_paths=["src/main.py", "src/utils.py"]
        )

        repo_info = graph.find_repo(story_id=1)

        assert repo_info["repo_url"] == "https://github.com/org/repo"
        assert repo_info["branch"] == "feature/story-1"
        assert "src/main.py" in repo_info["file_paths"]

    def test_find_repo_returns_none_for_unknown(self):
        """DG-06b: find_repo() returns None for unknown story."""
        from dependency_graph.graph import DependencyGraph

        graph = DependencyGraph()

        repo_info = graph.find_repo(story_id=999)

        assert repo_info is None

    def test_find_repo_supports_partial_info(self):
        """DG-06c: find_repo() works with partial repo info."""
        from dependency_graph.graph import DependencyGraph

        graph = DependencyGraph()

        # Register with only repo URL
        graph.register_story(
            story_id=1,
            repo_url="https://github.com/org/repo"
        )

        repo_info = graph.find_repo(story_id=1)

        assert repo_info["repo_url"] == "https://github.com/org/repo"
        assert repo_info["branch"] is None
        assert repo_info["file_paths"] == []
