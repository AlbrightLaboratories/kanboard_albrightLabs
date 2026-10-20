"""
Test DG-07: affected_files() discovers files from story description.

TDD Phase: RED -> GREEN
"""
import pytest


class TestAffectedFiles:
    """Tests for discovering affected files from story description."""

    def test_discovers_python_files(self):
        """DG-07a: affected_files() finds Python files in description."""
        from dependency_graph.graph import DependencyGraph

        graph = DependencyGraph()

        description = """
        Update the authentication logic in src/auth/login.py
        and also modify src/utils/crypto.py for the hash function.
        """

        files = graph.affected_files(description=description)

        assert "src/auth/login.py" in files
        assert "src/utils/crypto.py" in files

    def test_discovers_typescript_files(self):
        """DG-07b: affected_files() finds TypeScript files."""
        from dependency_graph.graph import DependencyGraph

        graph = DependencyGraph()

        description = """
        Add new component in src/components/Board.tsx
        Update the hook in src/hooks/useKanboard.ts
        """

        files = graph.affected_files(description=description)

        assert "src/components/Board.tsx" in files
        assert "src/hooks/useKanboard.ts" in files

    def test_discovers_multiple_extensions(self):
        """DG-07c: affected_files() handles various file extensions."""
        from dependency_graph.graph import DependencyGraph

        graph = DependencyGraph()

        description = """
        Files to change:
        - backend/api/routes.py
        - frontend/app.tsx
        - k8s/deployment.yaml
        - Dockerfile
        """

        files = graph.affected_files(description=description)

        assert "backend/api/routes.py" in files
        assert "frontend/app.tsx" in files
        assert "k8s/deployment.yaml" in files

    def test_empty_description_returns_empty(self):
        """DG-07d: affected_files() returns empty for no file references."""
        from dependency_graph.graph import DependencyGraph

        graph = DependencyGraph()

        description = "This is a general task with no specific files."

        files = graph.affected_files(description=description)

        assert files == []
