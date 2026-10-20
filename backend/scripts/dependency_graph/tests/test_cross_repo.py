"""
Test DG-08: Cross-repo story correctly links multiple repositories.

TDD Phase: RED -> GREEN
"""
import pytest


class TestCrossRepo:
    """Tests for cross-repository story support."""

    def test_register_multiple_repos(self):
        """DG-08a: Story can link to multiple repositories."""
        from dependency_graph.graph import DependencyGraph

        graph = DependencyGraph()

        # Register story with multiple repos
        graph.register_story(
            story_id=1,
            repos=[
                {
                    "repo_url": "https://github.com/org/frontend",
                    "branch": "feature/ui",
                    "file_paths": ["src/App.tsx"]
                },
                {
                    "repo_url": "https://github.com/org/backend",
                    "branch": "feature/api",
                    "file_paths": ["src/routes.py"]
                }
            ]
        )

        repos = graph.get_all_repos(story_id=1)

        assert len(repos) == 2
        repo_urls = [r["repo_url"] for r in repos]
        assert "https://github.com/org/frontend" in repo_urls
        assert "https://github.com/org/backend" in repo_urls

    def test_find_repo_returns_primary(self):
        """DG-08b: find_repo() returns primary repo for cross-repo story."""
        from dependency_graph.graph import DependencyGraph

        graph = DependencyGraph()

        graph.register_story(
            story_id=1,
            repos=[
                {
                    "repo_url": "https://github.com/org/primary",
                    "branch": "main",
                    "primary": True
                },
                {
                    "repo_url": "https://github.com/org/secondary",
                    "branch": "feature"
                }
            ]
        )

        repo_info = graph.find_repo(story_id=1)

        assert repo_info["repo_url"] == "https://github.com/org/primary"

    def test_get_all_files_across_repos(self):
        """DG-08c: Can get all files across all repos for a story."""
        from dependency_graph.graph import DependencyGraph

        graph = DependencyGraph()

        graph.register_story(
            story_id=1,
            repos=[
                {
                    "repo_url": "https://github.com/org/frontend",
                    "file_paths": ["src/App.tsx", "src/index.tsx"]
                },
                {
                    "repo_url": "https://github.com/org/backend",
                    "file_paths": ["src/main.py"]
                }
            ]
        )

        all_files = graph.get_all_files(story_id=1)

        assert len(all_files) == 3
        assert "src/App.tsx" in all_files
        assert "src/main.py" in all_files
