"""
Test MA-05: GET /stories/{id}/prompt returns structured prompt with AC, repo, deps.
"""
import pytest
from fastapi.testclient import TestClient


class TestStoryPrompt:
    """Tests for story prompt endpoint."""

    def test_returns_structured_prompt(self):
        """MA-05a: Returns prompt with title, description, ACs."""
        from maestro_api.server import app, get_maestro

        client = TestClient(app)
        maestro = get_maestro()

        maestro.add_story(20, {
            "title": "Implement auth",
            "description": "Add OAuth2 login flow",
            "acceptance_criteria": ["AC1: Login works", "AC2: Logout works"],
            "blocked": False,
            "claimed": False
        })

        response = client.get("/stories/20/prompt")
        assert response.status_code == 200

        prompt = response.json()
        assert prompt["title"] == "Implement auth"
        assert prompt["description"] == "Add OAuth2 login flow"
        assert len(prompt["acceptance_criteria"]) == 2

    def test_includes_repo_info(self):
        """MA-05b: Prompt includes linked repo, branch, files."""
        from maestro_api.server import app, get_maestro

        client = TestClient(app)
        maestro = get_maestro()

        maestro.add_story(21, {
            "title": "Fix bug",
            "repo_url": "https://github.com/org/repo",
            "branch": "fix/bug-123",
            "file_paths": ["src/auth.py"],
            "blocked": False,
            "claimed": False
        })

        response = client.get("/stories/21/prompt")
        prompt = response.json()

        assert prompt["repo_url"] == "https://github.com/org/repo"
        assert prompt["branch"] == "fix/bug-123"
        assert "src/auth.py" in prompt["file_paths"]

    def test_includes_dependencies(self):
        """MA-05c: Prompt includes dependency information."""
        from maestro_api.server import app, get_maestro

        client = TestClient(app)
        maestro = get_maestro()

        maestro.add_story(22, {
            "title": "Feature B",
            "depends_on": [21],
            "blocked": False,
            "claimed": False
        })

        response = client.get("/stories/22/prompt")
        prompt = response.json()

        assert "depends_on" in prompt
        assert 21 in prompt["depends_on"]

    def test_unknown_story_404(self):
        """MA-05d: Unknown story returns 404."""
        from maestro_api.server import app

        client = TestClient(app)

        response = client.get("/stories/99999/prompt")
        assert response.status_code == 404
