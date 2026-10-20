"""
Test SF-09: /release-it skill creates release with traceability to issue #17
"""
import pytest
from ..skills.release_it_skill import ReleaseItSkill


class TestReleaseItSkill:
    """Test /release-it skill implementation."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.skill = ReleaseItSkill()
        self.story_id = 505
        self.story_data = {
            "title": "Add Dashboard Feature",
            "description": "Implement analytics dashboard",
            "repo_url": "https://github.com/test/repo",
            "branch": "feature/dashboard"
        }
        self.commits = [
            {"sha": "abc123def456", "message": "Add dashboard component"},
            {"sha": "789xyz000111", "message": "Add dashboard tests"}
        ]

    def test_skill_name(self) -> None:
        """Verify skill name is 'release-it'."""
        assert self.skill.name == "release-it"

    def test_execute_returns_passed_status(self) -> None:
        """Verify successful execution returns passed status."""
        result = self.skill.execute(
            self.story_id,
            self.story_data,
            commits=self.commits
        )

        assert result.status == "passed"
        assert result.failure_reason is None

    def test_generates_release_tag(self) -> None:
        """Verify execution generates release tag."""
        result = self.skill.execute(
            self.story_id,
            self.story_data,
            commits=self.commits
        )

        assert "release_it" in result.output
        assert "release_tag" in result.output["release_it"]
        assert str(self.story_id) in result.output["release_it"]["release_tag"]

    def test_generates_release_notes(self) -> None:
        """Verify execution generates release notes."""
        result = self.skill.execute(
            self.story_id,
            self.story_data,
            commits=self.commits
        )

        notes = result.output["release_it"]["release_notes"]
        assert self.story_data["title"] in notes
        assert "Changes" in notes

    def test_includes_commits_in_notes(self) -> None:
        """Verify release notes include commit information."""
        result = self.skill.execute(
            self.story_id,
            self.story_data,
            commits=self.commits
        )

        notes = result.output["release_it"]["release_notes"]
        # Should contain abbreviated SHAs
        assert "abc123de" in notes
        assert "789xyz00" in notes
        # Should contain commit messages
        assert "Add dashboard component" in notes
        assert "Add dashboard tests" in notes

    def test_counts_linked_commits(self) -> None:
        """Verify output counts linked commits."""
        result = self.skill.execute(
            self.story_id,
            self.story_data,
            commits=self.commits
        )

        assert result.output["release_it"]["commits_linked"] == 2

    def test_creates_toc_entry(self) -> None:
        """Verify creates TOC entry for issue #17."""
        result = self.skill.execute(
            self.story_id,
            self.story_data,
            commits=self.commits
        )

        toc = result.output["release_it"]["toc_entry"]
        assert toc["story_id"] == self.story_id
        assert toc["title"] == self.story_data["title"]
        assert toc["toc_issue"] == 17

    def test_toc_entry_includes_commit_links(self) -> None:
        """Verify TOC entry includes commit links."""
        result = self.skill.execute(
            self.story_id,
            self.story_data,
            commits=self.commits
        )

        toc = result.output["release_it"]["toc_entry"]
        assert "commit_links" in toc
        assert len(toc["commit_links"]) == 2
        assert "abc123de" in toc["commit_links"]

    def test_toc_entry_has_standard_format(self) -> None:
        """Verify TOC entry uses standard commit format."""
        result = self.skill.execute(
            self.story_id,
            self.story_data,
            commits=self.commits
        )

        toc = result.output["release_it"]["toc_entry"]
        # Format: feat(US-XXX): title
        assert "format" in toc
        assert f"US-{self.story_id}" in toc["format"]
        assert self.story_data["title"] in toc["format"]

    def test_includes_repo_info(self) -> None:
        """Verify output includes repo information."""
        result = self.skill.execute(
            self.story_id,
            self.story_data,
            commits=self.commits
        )

        output = result.output["release_it"]
        assert output["repo_url"] == self.story_data["repo_url"]
        assert output["branch"] == self.story_data["branch"]

    def test_includes_release_timestamp(self) -> None:
        """Verify output includes release timestamp."""
        result = self.skill.execute(
            self.story_id,
            self.story_data,
            commits=self.commits
        )

        assert "released_at" in result.output["release_it"]
        assert result.output["release_it"]["released_at"] > 0

    def test_handles_no_commits(self) -> None:
        """Verify handles case with no commits."""
        result = self.skill.execute(
            self.story_id,
            self.story_data,
            commits=[]
        )

        assert result.status == "passed"
        assert result.output["release_it"]["commits_linked"] == 0
        assert "Initial implementation" in result.output["release_it"]["release_notes"]

    def test_notes_include_story_reference(self) -> None:
        """Verify release notes include story reference."""
        result = self.skill.execute(
            self.story_id,
            self.story_data,
            commits=self.commits
        )

        notes = result.output["release_it"]["release_notes"]
        assert f"#{self.story_id}" in notes

    def test_truncates_long_sha(self) -> None:
        """Verify long SHAs are truncated to 8 chars."""
        long_sha_commits = [
            {"sha": "abcdefghijklmnop1234567890", "message": "Test"}
        ]

        result = self.skill.execute(
            self.story_id,
            self.story_data,
            commits=long_sha_commits
        )

        notes = result.output["release_it"]["release_notes"]
        # Should be truncated to first 8 chars
        assert "abcdefgh" in notes
        assert "abcdefghijklmnop" not in notes

    def test_handles_commit_without_sha(self) -> None:
        """Verify handles commits with missing SHA gracefully."""
        bad_commits = [
            {"message": "No SHA commit"}  # Missing 'sha' key
        ]

        result = self.skill.execute(
            self.story_id,
            self.story_data,
            commits=bad_commits
        )

        assert result.status == "passed"
        notes = result.output["release_it"]["release_notes"]
        assert "unknown" in notes

    def test_includes_agent_id_in_result(self) -> None:
        """Verify result includes agent ID when provided."""
        agent_id = "claude-007"
        result = self.skill.execute(
            self.story_id,
            self.story_data,
            agent_id=agent_id,
            commits=self.commits
        )

        assert result.agent_id == agent_id

    def test_includes_story_id_in_result(self) -> None:
        """Verify result includes story ID."""
        result = self.skill.execute(
            self.story_id,
            self.story_data,
            commits=self.commits
        )

        assert result.story_id == self.story_id
