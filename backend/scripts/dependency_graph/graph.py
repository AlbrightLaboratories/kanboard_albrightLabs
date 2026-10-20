"""
Dependency Graph

Manages story dependencies, blocking relationships, and repo awareness.
"""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set

from .exceptions import CircularDependencyError


class DependencyGraph:
    """
    Manages story dependencies and repo awareness.

    Tracks which stories block others, detects circular dependencies,
    and provides repo/file discovery for agent scheduling.
    """

    def __init__(self):
        """Initialize empty dependency graph."""
        # story_id -> set of story_ids it blocks
        self._blocks: Dict[int, Set[int]] = defaultdict(set)
        # story_id -> set of story_ids that block it
        self._blocked_by: Dict[int, Set[int]] = defaultdict(set)
        # story_id -> status (in_progress, done, etc.)
        self._status: Dict[int, str] = {}
        # story_id -> repo info
        self._repo_info: Dict[int, Dict[str, Any]] = {}
        # story_id -> list of repos (for cross-repo stories)
        self._multi_repo: Dict[int, List[Dict[str, Any]]] = {}

    def add_dependency(
        self,
        from_story_id: int,
        to_story_id: int,
        dependency_type: str = "blocks"
    ) -> bool:
        """
        Add a dependency between stories.

        Args:
            from_story_id: Source story ID
            to_story_id: Target story ID
            dependency_type: "blocks" or "blocked_by"

        Returns:
            True if dependency added successfully

        Raises:
            CircularDependencyError: If this would create a cycle
        """
        # Check for self-reference
        if from_story_id == to_story_id:
            raise CircularDependencyError(
                f"Story {from_story_id} cannot depend on itself"
            )

        # Determine the actual blocker and blocked
        if dependency_type == "blocks":
            blocker = from_story_id
            blocked = to_story_id
        else:  # blocked_by
            blocker = to_story_id
            blocked = from_story_id

        # Check for circular dependency
        if self._would_create_cycle(blocker, blocked):
            raise CircularDependencyError(
                f"Adding {blocker} -> {blocked} would create circular dependency"
            )

        # Add the dependency
        self._blocks[blocker].add(blocked)
        self._blocked_by[blocked].add(blocker)

        return True

    def _would_create_cycle(self, blocker: int, blocked: int) -> bool:
        """Check if adding blocker->blocked would create a cycle."""
        # If blocked already (directly or indirectly) blocks blocker, we'd have a cycle
        visited: Set[int] = set()
        stack = [blocked]

        while stack:
            current = stack.pop()
            if current == blocker:
                return True
            if current in visited:
                continue
            visited.add(current)
            stack.extend(self._blocks[current])

        return False

    def get_dependencies(self, story_id: int) -> Dict[str, List[int]]:
        """
        Get dependencies for a story.

        Returns:
            Dict with 'blocks' and 'blocked_by' lists
        """
        return {
            "blocks": list(self._blocks.get(story_id, set())),
            "blocked_by": list(self._blocked_by.get(story_id, set()))
        }

    def get_graph(self, story_id: int) -> Dict[str, Any]:
        """
        Get full dependency tree starting from story.

        Returns:
            Tree structure with story_id and children
        """
        visited: Set[int] = set()

        def build_tree(sid: int) -> Dict[str, Any]:
            if sid in visited:
                return {"story_id": sid, "children": []}
            visited.add(sid)

            children = []
            for child_id in self._blocks.get(sid, set()):
                children.append(build_tree(child_id))

            return {
                "story_id": sid,
                "children": children
            }

        return build_tree(story_id)

    def set_story_status(self, story_id: int, status: str) -> None:
        """Set status for a story."""
        self._status[story_id] = status

    def get_story_status(self, story_id: int) -> Optional[str]:
        """Get status for a story."""
        return self._status.get(story_id)

    def is_claimable(self, story_id: int) -> bool:
        """
        Check if story can be claimed (no incomplete blockers).

        Returns:
            True if all blockers are done or no blockers exist
        """
        blockers = self._blocked_by.get(story_id, set())
        if not blockers:
            return True

        for blocker_id in blockers:
            status = self._status.get(blocker_id)
            if status != "done":
                return False

        return True

    def get_blockers(self, story_id: int) -> List[int]:
        """
        Get list of incomplete blockers for a story.

        Returns:
            List of story IDs that are blocking and not done
        """
        blockers = []
        for blocker_id in self._blocked_by.get(story_id, set()):
            status = self._status.get(blocker_id)
            if status != "done":
                blockers.append(blocker_id)
        return blockers

    def complete_and_get_unblocked(self, story_id: int) -> List[int]:
        """
        Mark story as done and return newly unblocked stories.

        Returns:
            List of story IDs that became claimable
        """
        self._status[story_id] = "done"

        unblocked = []
        for blocked_id in self._blocks.get(story_id, set()):
            if self.is_claimable(blocked_id):
                unblocked.append(blocked_id)

        return unblocked

    def register_story(
        self,
        story_id: int,
        repo_url: str = None,
        branch: str = None,
        file_paths: List[str] = None,
        repos: List[Dict[str, Any]] = None
    ) -> None:
        """
        Register story with repo information.

        For single repo:
            register_story(1, repo_url="...", branch="...", file_paths=[...])

        For multi-repo:
            register_story(1, repos=[{repo_url, branch, file_paths, primary}, ...])
        """
        if repos:
            # Multi-repo story
            self._multi_repo[story_id] = repos
            # Set primary repo info
            for repo in repos:
                if repo.get("primary", False):
                    self._repo_info[story_id] = {
                        "repo_url": repo.get("repo_url"),
                        "branch": repo.get("branch"),
                        "file_paths": repo.get("file_paths", [])
                    }
                    break
            # If no primary, use first
            if story_id not in self._repo_info:
                first = repos[0]
                self._repo_info[story_id] = {
                    "repo_url": first.get("repo_url"),
                    "branch": first.get("branch"),
                    "file_paths": first.get("file_paths", [])
                }
        else:
            # Single repo story
            self._repo_info[story_id] = {
                "repo_url": repo_url,
                "branch": branch,
                "file_paths": file_paths or []
            }

    def find_repo(self, story_id: int) -> Optional[Dict[str, Any]]:
        """
        Get repo information for a story.

        Returns:
            Dict with repo_url, branch, file_paths or None
        """
        return self._repo_info.get(story_id)

    def get_all_repos(self, story_id: int) -> List[Dict[str, Any]]:
        """
        Get all repos for a cross-repo story.

        Returns:
            List of repo info dicts
        """
        if story_id in self._multi_repo:
            return self._multi_repo[story_id]
        elif story_id in self._repo_info:
            return [self._repo_info[story_id]]
        return []

    def get_all_files(self, story_id: int) -> List[str]:
        """
        Get all files across all repos for a story.

        Returns:
            Combined list of file paths
        """
        all_files = []
        repos = self.get_all_repos(story_id)
        for repo in repos:
            files = repo.get("file_paths", [])
            all_files.extend(files)
        return all_files

    def affected_files(self, description: str) -> List[str]:
        """
        Discover file paths mentioned in description.

        Uses regex to find common file patterns.

        Returns:
            List of discovered file paths
        """
        if not description:
            return []

        # Pattern to match file paths
        # Matches paths like: src/foo/bar.py, ./components/App.tsx, k8s/deploy.yaml
        pattern = r'(?:^|[\s\-\*])([a-zA-Z0-9_./]+(?:\.[a-zA-Z0-9]+))'

        matches = re.findall(pattern, description)

        # Filter to likely file paths (must have extension)
        files = []
        extensions = {
            '.py', '.ts', '.tsx', '.js', '.jsx', '.yaml', '.yml',
            '.json', '.md', '.go', '.rs', '.java', '.cpp', '.c', '.h'
        }

        for match in matches:
            # Must contain a path separator or start with reasonable prefix
            if '/' in match or '.' in match:
                for ext in extensions:
                    if match.endswith(ext):
                        files.append(match)
                        break

        return list(set(files))  # Remove duplicates
