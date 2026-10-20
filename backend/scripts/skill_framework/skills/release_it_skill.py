"""
Release-It Skill

Creates release with full traceability to Master TOC.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from .base_skill import BaseSkill, SkillResult


class ReleaseItSkill(BaseSkill):
    """Creates release with traceability."""

    name = "release-it"

    def execute(
        self,
        story_id: int,
        story_data: Dict[str, Any],
        agent_id: Optional[str] = None,
        **kwargs: Any
    ) -> SkillResult:
        """
        Create release with full traceability.

        1. Link commits to story
        2. Create release notes
        3. Update Master TOC (issue #17)
        4. Tag release
        """
        try:
            title = story_data.get("title", "")
            commits = kwargs.get("commits", [])
            repo_url = story_data.get("repo_url", "")
            branch = story_data.get("branch", "main")

            # Generate release info
            release_info = self._generate_release_info(
                story_id, title, commits
            )

            # Create TOC entry
            toc_entry = self._create_toc_entry(story_id, title, commits)

            output = {
                "release_it": {
                    "release_tag": release_info["tag"],
                    "release_notes": release_info["notes"],
                    "commits_linked": len(commits),
                    "toc_entry": toc_entry,
                    "repo_url": repo_url,
                    "branch": branch,
                    "released_at": time.time()
                }
            }

            return self._create_result(
                story_id=story_id,
                status="passed",
                output=output,
                agent_id=agent_id
            )

        except Exception as e:
            return self._create_result(
                story_id=story_id,
                status="failed",
                failure_reason=str(e),
                agent_id=agent_id
            )

    def _generate_release_info(
        self,
        story_id: int,
        title: str,
        commits: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate release information."""
        # Generate semantic version tag
        tag = f"story-{story_id}-release"

        # Build release notes
        notes = f"## {title}\n\n"
        notes += "### Changes\n\n"

        for commit in commits:
            sha = commit.get("sha", "unknown")[:8]
            message = commit.get("message", "No message")
            notes += f"- [{sha}] {message}\n"

        if not commits:
            notes += "- Initial implementation\n"

        notes += f"\n### Story: #{story_id}\n"

        return {
            "tag": tag,
            "notes": notes
        }

    def _create_toc_entry(
        self,
        story_id: int,
        title: str,
        commits: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create entry for Master TOC."""
        commit_shas = [c.get("sha", "")[:8] for c in commits]

        return {
            "story_id": story_id,
            "title": title,
            "commit_links": commit_shas,
            "format": f"feat(US-{story_id}): {title}",
            "toc_issue": 17  # Master TOC issue number
        }
