"""
Test TI-03: Commit subjects follow TOC format: feat(US-XXX): description
"""
import pytest
from ..commit_linker import CommitLinker, CommitInfo
from ..comment_poster import TOCCommentPoster


class TestCommitFormat:
    """Test commit message format validation."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.linker = CommitLinker()
        self.poster = TOCCommentPoster()

    # Valid format tests
    def test_valid_feat_format(self) -> None:
        """Verify feat(US-XXX): description is valid."""
        message = "feat(US-123): Add new login feature"
        is_valid, error = self.linker.validate_format(message)
        assert is_valid is True
        assert error is None

    def test_valid_fix_format(self) -> None:
        """Verify fix(US-XXX): description is valid."""
        message = "fix(US-456): Fix memory leak in auth module"
        is_valid, error = self.linker.validate_format(message)
        assert is_valid is True
        assert error is None

    def test_valid_chore_format(self) -> None:
        """Verify chore(US-XXX): description is valid."""
        message = "chore(US-789): Update dependencies"
        is_valid, error = self.linker.validate_format(message)
        assert is_valid is True
        assert error is None

    def test_valid_docs_format(self) -> None:
        """Verify docs(US-XXX): description is valid."""
        message = "docs(US-101): Add API documentation"
        is_valid, error = self.linker.validate_format(message)
        assert is_valid is True
        assert error is None

    def test_valid_refactor_format(self) -> None:
        """Verify refactor(US-XXX): description is valid."""
        message = "refactor(US-202): Clean up auth code"
        is_valid, error = self.linker.validate_format(message)
        assert is_valid is True
        assert error is None

    def test_valid_test_format(self) -> None:
        """Verify test(US-XXX): description is valid."""
        message = "test(US-303): Add unit tests for login"
        is_valid, error = self.linker.validate_format(message)
        assert is_valid is True
        assert error is None

    def test_valid_style_format(self) -> None:
        """Verify style(US-XXX): description is valid."""
        message = "style(US-404): Format code with black"
        is_valid, error = self.linker.validate_format(message)
        assert is_valid is True
        assert error is None

    def test_valid_ci_format(self) -> None:
        """Verify ci(US-XXX): description is valid."""
        message = "ci(US-505): Add GitHub Actions workflow"
        is_valid, error = self.linker.validate_format(message)
        assert is_valid is True
        assert error is None

    def test_valid_build_format(self) -> None:
        """Verify build(US-XXX): description is valid."""
        message = "build(US-606): Update Dockerfile"
        is_valid, error = self.linker.validate_format(message)
        assert is_valid is True
        assert error is None

    def test_valid_perf_format(self) -> None:
        """Verify perf(US-XXX): description is valid."""
        message = "perf(US-707): Optimize database queries"
        is_valid, error = self.linker.validate_format(message)
        assert is_valid is True
        assert error is None

    # Invalid format tests
    def test_invalid_no_type(self) -> None:
        """Verify message without type is invalid."""
        message = "Add new feature"
        is_valid, error = self.linker.validate_format(message)
        assert is_valid is False
        assert error is not None

    def test_invalid_no_scope(self) -> None:
        """Verify message without scope is invalid."""
        message = "feat: Add new feature"
        is_valid, error = self.linker.validate_format(message)
        assert is_valid is False
        assert error is not None

    def test_invalid_no_colon(self) -> None:
        """Verify message without colon is invalid."""
        message = "feat(US-123) Add new feature"
        is_valid, error = self.linker.validate_format(message)
        assert is_valid is False
        assert error is not None

    def test_invalid_unknown_type(self) -> None:
        """Verify message with unknown type is invalid."""
        message = "unknown(US-123): Add new feature"
        is_valid, error = self.linker.validate_format(message)
        assert is_valid is False
        assert "Invalid type" in error

    def test_invalid_empty_message(self) -> None:
        """Verify empty message is invalid."""
        message = ""
        is_valid, error = self.linker.validate_format(message)
        assert is_valid is False
        assert error is not None

    def test_invalid_short_description(self) -> None:
        """Verify message with too short description is invalid."""
        message = "feat(US-123): A"  # Only 1 char description
        is_valid, error = self.linker.validate_format(message)
        assert is_valid is False
        assert "Description too short" in error

    # Story ID extraction tests
    def test_extract_story_id_from_scope(self) -> None:
        """Verify story ID is extracted from US-XXX scope."""
        info = self.linker.parse_commit("abc123", "feat(US-123): Add feature")
        assert info.story_id == 123

    def test_extract_story_id_numeric_only(self) -> None:
        """Verify story ID extracted from numeric scope."""
        info = self.linker.parse_commit("abc123", "feat(123): Add feature")
        assert info.story_id == 123

    def test_no_story_id_from_non_numeric_scope(self) -> None:
        """Verify no story ID when scope is not story-like."""
        info = self.linker.parse_commit("abc123", "feat(auth): Add feature")
        assert info.story_id is None

    # TOC entry formatting tests
    def test_format_toc_entry(self) -> None:
        """Verify TOC entry format for story."""
        entry = self.poster.format_toc_entry(123, "Add user authentication")
        assert entry == "feat(US-123): Add user authentication"

    def test_validate_commit_format_via_poster(self) -> None:
        """Verify poster can validate commit format."""
        valid_msg = "feat(US-123): Add new feature"
        invalid_msg = "random commit message"

        assert self.poster.validate_commit_format(valid_msg) is True
        assert self.poster.validate_commit_format(invalid_msg) is False

    # Case insensitivity tests
    def test_type_case_insensitive(self) -> None:
        """Verify type matching is case-insensitive."""
        messages = [
            "FEAT(US-123): Add feature",
            "Feat(US-123): Add feature",
            "feat(US-123): Add feature",
        ]
        for msg in messages:
            is_valid, _ = self.linker.validate_format(msg)
            assert is_valid is True, f"Failed for: {msg}"

    # Multi-line commit message tests
    def test_validates_first_line_only(self) -> None:
        """Verify validation uses only first line."""
        message = """feat(US-123): Add new feature

        This is the body of the commit.
        It has multiple lines.
        """
        is_valid, error = self.linker.validate_format(message)
        assert is_valid is True
        assert error is None

    # CommitInfo linking tests
    def test_link_commit_to_story(self) -> None:
        """Verify commit can be linked to story."""
        info = CommitInfo(
            sha="abc123def456",
            message="feat(US-123): Add feature",
            valid_format=True
        )
        self.linker.link_commit(123, info)

        commits = self.linker.get_commits_for_story(123)
        assert len(commits) == 1
        assert commits[0].sha == "abc123def456"

    def test_format_toc_entry_for_commit(self) -> None:
        """Verify commit formats as TOC entry."""
        info = CommitInfo(
            sha="abc123def456",
            message="feat(US-123): Add feature",
            valid_format=True
        )
        entry = self.linker.format_toc_entry(info)
        assert "[abc123de]" in entry
        assert "feat(US-123): Add feature" in entry

