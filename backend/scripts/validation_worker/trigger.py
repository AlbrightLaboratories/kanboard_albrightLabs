"""
Validation Trigger

Triggers GitHub validation workflows when stories enter Validation column.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class WorkflowTriggerResult:
    """Result of triggering a validation workflow."""

    story_id: int
    workflow_id: Optional[str] = None
    status: str = "pending"  # pending, triggered, failed
    repo: Optional[str] = None
    branch: Optional[str] = None
    error: Optional[str] = None
    run_url: Optional[str] = None


class ValidationTrigger:
    """Triggers GitHub Actions validation workflows."""

    def __init__(
        self,
        workflow_file: str = "kanboard-validation.yml",
        default_repo: str = "AlbrightLaboratories/kanboard_albrightLabs"
    ) -> None:
        """
        Initialize validation trigger.

        Args:
            workflow_file: Name of the workflow file to trigger
            default_repo: Default repository if not specified in story
        """
        self.workflow_file = workflow_file
        self.default_repo = default_repo
        self._gh_authenticated: Optional[bool] = None

    def check_gh_auth(self) -> bool:
        """Check if gh CLI is authenticated."""
        if self._gh_authenticated is not None:
            return self._gh_authenticated

        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True,
                timeout=10
            )
            self._gh_authenticated = result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self._gh_authenticated = False

        return self._gh_authenticated

    def trigger_validation(
        self,
        story_id: int,
        story_data: Dict[str, Any]
    ) -> WorkflowTriggerResult:
        """
        Trigger GitHub validation workflow for a story.

        Args:
            story_id: Story ID
            story_data: Story data containing repo, branch info

        Returns:
            WorkflowTriggerResult with trigger status
        """
        # Extract repo and branch from story
        repo = story_data.get("linked_repo") or story_data.get("repo_url")
        branch = story_data.get("linked_branch") or story_data.get("branch", "main")

        # Clean repo URL to get owner/repo format
        if repo:
            repo = self._normalize_repo(repo)
        else:
            repo = self.default_repo

        # Check gh authentication
        if not self.check_gh_auth():
            return WorkflowTriggerResult(
                story_id=story_id,
                status="failed",
                error="GitHub CLI not authenticated",
                repo=repo,
                branch=branch
            )

        # Build workflow dispatch command
        try:
            result = self._dispatch_workflow(story_id, repo, branch)
            return result
        except Exception as e:
            return WorkflowTriggerResult(
                story_id=story_id,
                status="failed",
                error=str(e),
                repo=repo,
                branch=branch
            )

    def _normalize_repo(self, repo: str) -> str:
        """Normalize repo URL to owner/repo format."""
        # Handle full URLs
        if "github.com" in repo:
            # Extract owner/repo from URL
            parts = repo.rstrip("/").split("/")
            if len(parts) >= 2:
                return f"{parts[-2]}/{parts[-1].replace('.git', '')}"

        return repo

    def _dispatch_workflow(
        self,
        story_id: int,
        repo: str,
        branch: str
    ) -> WorkflowTriggerResult:
        """Dispatch the validation workflow."""
        cmd = [
            "gh", "workflow", "run",
            self.workflow_file,
            "--repo", repo,
            "-f", f"story_id={story_id}",
            "-f", f"repo={repo}",
            "-f", f"branch={branch}"
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                # Try to get the workflow run URL
                run_url = self._get_latest_run_url(repo)
                return WorkflowTriggerResult(
                    story_id=story_id,
                    status="triggered",
                    repo=repo,
                    branch=branch,
                    run_url=run_url
                )
            else:
                return WorkflowTriggerResult(
                    story_id=story_id,
                    status="failed",
                    error=result.stderr or "Workflow dispatch failed",
                    repo=repo,
                    branch=branch
                )
        except subprocess.TimeoutExpired:
            return WorkflowTriggerResult(
                story_id=story_id,
                status="failed",
                error="Workflow dispatch timed out",
                repo=repo,
                branch=branch
            )

    def _get_latest_run_url(self, repo: str) -> Optional[str]:
        """Get URL of the latest workflow run."""
        try:
            result = subprocess.run(
                [
                    "gh", "run", "list",
                    "--repo", repo,
                    "--workflow", self.workflow_file,
                    "--limit", "1",
                    "--json", "url"
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0 and result.stdout:
                import json
                runs = json.loads(result.stdout)
                if runs:
                    return runs[0].get("url")
        except Exception:
            pass

        return None

    def can_validate(self, story_data: Dict[str, Any]) -> tuple:
        """
        Check if a story can be validated.

        Args:
            story_data: Story data

        Returns:
            Tuple of (can_validate, missing_fields)
        """
        missing = []

        # Check for linked repo
        if not story_data.get("linked_repo") and not story_data.get("repo_url"):
            missing.append("linked_repo")

        # Check for linked branch
        if not story_data.get("linked_branch") and not story_data.get("branch"):
            missing.append("linked_branch")

        return len(missing) == 0, missing

    def extract_checkout_info(
        self,
        story_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Extract checkout info for the workflow.

        Args:
            story_data: Story data

        Returns:
            Dict with repo, branch, and ref info
        """
        repo = story_data.get("linked_repo") or story_data.get("repo_url", "")
        branch = story_data.get("linked_branch") or story_data.get("branch", "main")
        pr_url = story_data.get("linked_pr", "")

        # Extract PR number if present
        pr_number = None
        if pr_url and "/pull/" in pr_url:
            try:
                pr_number = pr_url.split("/pull/")[-1].split("/")[0]
            except (IndexError, AttributeError):
                pass

        return {
            "repo": self._normalize_repo(repo) if repo else "",
            "branch": branch,
            "pr_number": pr_number or "",
            "ref": f"refs/heads/{branch}" if not pr_number else f"refs/pull/{pr_number}/merge"
        }
