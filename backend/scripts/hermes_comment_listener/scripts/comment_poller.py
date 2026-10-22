"""
Comment Poller - Polls Kanboard for new comments with @hermes mentions.

Implements the main polling loop that:
1. Fetches recent comments from Kanboard
2. Detects @hermes mentions
3. Calls Hermes for responses
4. Posts responses back as comments
"""
from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

import httpx

from .comment_tracker import CommentTracker

logger = logging.getLogger(__name__)

# Configuration
KANBOARD_URL = os.getenv("KANBOARD_URL", "http://kanboard.hr-project-tracking.svc.cluster.local/jsonrpc.php")
KANBOARD_USERNAME = os.getenv("KANBOARD_USERNAME", "admin")
KANBOARD_API_TOKEN = os.getenv("KANBOARD_API_TOKEN", "")
POLL_INTERVAL_SECONDS = float(os.getenv("POLL_INTERVAL_SECONDS", "5"))


@dataclass
class Comment:
    """Represents a Kanboard comment."""
    id: str
    task_id: str
    user_id: str
    username: str
    content: str
    date_creation: str
    project_id: Optional[str] = None


class KanboardClient:
    """Simple Kanboard JSON-RPC client for comment operations."""

    def __init__(
        self,
        url: str = KANBOARD_URL,
        username: str = KANBOARD_USERNAME,
        api_token: str = KANBOARD_API_TOKEN,
    ):
        self._url = url
        self._username = username
        self._api_token = api_token
        self._request_id = 0

    def _get_auth(self) -> tuple[str, str]:
        """Get HTTP Basic auth credentials."""
        return (self._username, self._api_token)

    async def _call(self, method: str, **params) -> Any:
        """Make a JSON-RPC call to Kanboard."""
        self._request_id += 1
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "id": self._request_id,
            "params": params,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self._url,
                json=payload,
                auth=self._get_auth(),
            )
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                raise Exception(f"Kanboard error: {data['error']}")

            return data.get("result")

    async def get_all_comments(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all comments for a task."""
        result = await self._call("getAllComments", task_id=task_id)
        return result if result else []

    async def create_comment(
        self,
        task_id: int,
        content: str,
        user_id: int = 1,
    ) -> Optional[int]:
        """Create a comment on a task."""
        result = await self._call(
            "createComment",
            task_id=task_id,
            content=content,
            user_id=user_id,
        )
        return result

    async def get_all_tasks(self, project_id: int) -> List[Dict[str, Any]]:
        """Get all tasks for a project."""
        result = await self._call("getAllTasks", project_id=project_id, status_id=1)
        return result if result else []

    async def get_all_projects(self) -> List[Dict[str, Any]]:
        """Get all projects."""
        result = await self._call("getAllProjects")
        return result if result else []

    async def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Get a single task by ID."""
        return await self._call("getTask", task_id=task_id)


class CommentPoller:
    """
    Polls Kanboard for comments and processes @hermes mentions.
    """

    def __init__(
        self,
        kanboard_client: Optional[KanboardClient] = None,
        tracker: Optional[CommentTracker] = None,
        poll_interval: float = POLL_INTERVAL_SECONDS,
    ):
        """
        Initialize the poller.

        Args:
            kanboard_client: Kanboard API client
            tracker: Comment tracker for deduplication
            poll_interval: Seconds between polls
        """
        self._client = kanboard_client or KanboardClient()
        self._tracker = tracker or CommentTracker()
        self._poll_interval = poll_interval
        self._running = False
        self._last_poll_time = datetime.now(timezone.utc)

    async def poll_once(self) -> List[Comment]:
        """
        Poll for new comments with @hermes mentions.

        Returns:
            List of new comments with @hermes mentions
        """
        from scripts.agent_comments.mention_parser import is_agent_mentioned

        new_mentions = []

        try:
            # Get all projects
            projects = await self._client.get_all_projects()
            logger.debug(f"Found {len(projects)} projects")

            for project in projects:
                project_id = project.get("id")
                if not project_id:
                    continue

                # Get all tasks in project
                tasks = await self._client.get_all_tasks(int(project_id))

                for task in tasks:
                    task_id = task.get("id")
                    if not task_id:
                        continue

                    # Get comments for task
                    comments = await self._client.get_all_comments(int(task_id))

                    for comment_data in comments:
                        comment_id = str(comment_data.get("id", ""))
                        content = comment_data.get("comment", "")

                        # Skip if already processed
                        if self._tracker.is_processed(comment_id):
                            continue

                        # Check for @hermes mention
                        if is_agent_mentioned(content, "hermes"):
                            comment = Comment(
                                id=comment_id,
                                task_id=str(task_id),
                                user_id=str(comment_data.get("user_id", "")),
                                username=comment_data.get("username", "unknown"),
                                content=content,
                                date_creation=comment_data.get("date_creation", ""),
                                project_id=str(project_id),
                            )
                            new_mentions.append(comment)
                            logger.info(f"Found @hermes mention in comment {comment_id}")

        except Exception as e:
            logger.error(f"Error polling comments: {e}")

        return new_mentions

    async def process_mention(self, comment: Comment) -> bool:
        """
        Process a single @hermes mention.

        Args:
            comment: The comment with the mention

        Returns:
            True if processed successfully
        """
        from scripts.hermes_adapter import complete, build_simple_prompt
        from scripts.hermes_adapter.scripts.request_builder import format_agent_response

        # Try to acquire processing lock
        if not self._tracker.mark_processing(comment.id):
            logger.debug(f"Comment {comment.id} already being processed")
            return False

        try:
            logger.info(f"Processing @hermes mention in comment {comment.id}")

            # Build prompt and call Hermes
            messages = build_simple_prompt(comment.content)
            result = await complete(messages)

            if result.failure_reason:
                logger.error(f"Hermes failed: {result.failure_reason}")
                # Still mark as processed to avoid retry loops
                self._tracker.mark_processed(comment.id)
                return False

            # Format and post response
            response_content = format_agent_response(result.reply, "Hermes")
            comment_id = await self._client.create_comment(
                task_id=int(comment.task_id),
                content=response_content,
            )

            if comment_id:
                logger.info(f"Posted Hermes response as comment {comment_id}")
                self._tracker.mark_processed(comment.id)
                return True
            else:
                logger.error("Failed to post Hermes response")
                return False

        except Exception as e:
            logger.error(f"Error processing mention: {e}")
            # Mark as processed to avoid infinite retry
            self._tracker.mark_processed(comment.id)
            return False

    async def run(self) -> None:
        """
        Run the polling loop.

        Polls for new comments every poll_interval seconds.
        """
        self._running = True
        logger.info(f"Starting comment poller (interval: {self._poll_interval}s)")

        while self._running:
            try:
                # Poll for new mentions
                mentions = await self.poll_once()

                # Process each mention
                for comment in mentions:
                    await self.process_mention(comment)

                self._last_poll_time = datetime.now(timezone.utc)

            except Exception as e:
                logger.error(f"Polling error: {e}")

            # Wait before next poll
            await asyncio.sleep(self._poll_interval)

    def stop(self) -> None:
        """Stop the polling loop."""
        self._running = False
        logger.info("Stopping comment poller")
