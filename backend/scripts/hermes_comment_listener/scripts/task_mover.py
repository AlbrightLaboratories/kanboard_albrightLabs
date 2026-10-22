"""
Task Mover - Move Kanboard tasks between columns.

Enables Hermes to control task workflow:
- Move to "In Progress" when starting work
- Move to "Review" when ready for validation
- Move to "Done" when completed
"""
from __future__ import annotations

import logging
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)


class TaskMover:
    """
    Move Kanboard tasks between columns.

    Integrates with KanboardClient to move tasks through the workflow:
    Backlog → In Progress → Review → Done
    """

    # Default column names (can be overridden per project)
    # Based on actual Kanboard columns: Backlog, Ready, Work in progress, Done, Accepted
    DEFAULT_COLUMNS = {
        "backlog": "Backlog",
        "ready": "Ready",
        "in_progress": "Work in progress",
        "review": "Ready",  # Use Ready for validation/review
        "done": "Done",
        "accepted": "Accepted",
    }

    def __init__(self, kanboard_client):
        """
        Initialize TaskMover.

        Args:
            kanboard_client: KanboardClient instance for API calls
        """
        self._client = kanboard_client
        self._column_cache: Dict[int, List[Dict[str, Any]]] = {}

    async def get_columns(self, project_id: int) -> List[Dict[str, Any]]:
        """
        Get columns for a project (cached).

        Args:
            project_id: Kanboard project ID

        Returns:
            List of column dicts with id, title, position
        """
        if project_id not in self._column_cache:
            columns = await self._client.get_columns(project_id)
            self._column_cache[project_id] = columns or []
        return self._column_cache[project_id]

    async def get_column_id_by_name(
        self,
        project_id: int,
        column_name: str
    ) -> Optional[int]:
        """
        Get column ID by name (case-insensitive).

        Args:
            project_id: Kanboard project ID
            column_name: Column name to find

        Returns:
            Column ID if found, None otherwise
        """
        columns = await self.get_columns(project_id)
        column_lower = column_name.lower()

        for col in columns:
            if col.get("title", "").lower() == column_lower:
                return int(col.get("id"))

        return None

    async def get_current_column(self, task_id: int) -> Optional[str]:
        """
        Get current column name for a task.

        Args:
            task_id: Kanboard task ID

        Returns:
            Column name or None if not found
        """
        try:
            task = await self._client.get_task(task_id)
            if not task:
                return None

            project_id = int(task.get("project_id", 0))
            column_id = int(task.get("column_id", 0))

            columns = await self.get_columns(project_id)
            for col in columns:
                if int(col.get("id", 0)) == column_id:
                    return col.get("title")

            return None
        except Exception as e:
            logger.error(f"Error getting current column for task {task_id}: {e}")
            return None

    async def move_task(
        self,
        task_id: int,
        column_name: str,
        position: int = 1
    ) -> bool:
        """
        Move a task to a column by name.

        Args:
            task_id: Kanboard task ID
            column_name: Target column name
            position: Position in column (1 = top)

        Returns:
            True if moved successfully
        """
        try:
            # Get task to find project_id
            task = await self._client.get_task(task_id)
            if not task:
                logger.error(f"Task {task_id} not found")
                return False

            project_id = int(task.get("project_id", 0))
            current_column = task.get("column_id")

            # Get target column ID
            target_column_id = await self.get_column_id_by_name(
                project_id, column_name
            )

            if not target_column_id:
                logger.error(f"Column '{column_name}' not found in project {project_id}")
                return False

            # Skip if already in target column
            if current_column == target_column_id:
                logger.info(f"Task {task_id} already in '{column_name}'")
                return True

            # Move the task
            result = await self._client.move_task_position(
                task_id=task_id,
                column_id=target_column_id,
                position=position,
                project_id=project_id,
                swimlane_id=0,
            )

            if result:
                logger.info(f"Moved task {task_id} to '{column_name}'")
            else:
                logger.error(f"Failed to move task {task_id} to '{column_name}'")

            return bool(result)

        except Exception as e:
            logger.error(f"Error moving task {task_id}: {e}")
            return False

    async def move_to_in_progress(self, task_id: int) -> bool:
        """Move task to In Progress column."""
        return await self.move_task(task_id, self.DEFAULT_COLUMNS["in_progress"])

    async def move_to_review(self, task_id: int) -> bool:
        """Move task to Review column."""
        return await self.move_task(task_id, self.DEFAULT_COLUMNS["review"])

    async def move_to_done(self, task_id: int) -> bool:
        """Move task to Done column."""
        return await self.move_task(task_id, self.DEFAULT_COLUMNS["done"])

    async def move_to_backlog(self, task_id: int) -> bool:
        """Move task back to Backlog column."""
        return await self.move_task(task_id, self.DEFAULT_COLUMNS["backlog"])

    def clear_cache(self) -> None:
        """Clear column cache (use if columns changed)."""
        self._column_cache.clear()
